"""Disabling checks with "! castep-lint: disable=..." comments

A comment on its own line directly in the body of a subroutine or function disables the named
checks for that routine (but not for routines contained within it). A comment following code
disables them for every line of that statement, including any lines joined by "&".
"""

import re

from castep_linter.error_logging.error_types import FortranMsgBase
from castep_linter.error_logging.logger import ErrorLogger
from castep_linter.fortran.fortran_nodes import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran, FortranContexts

DIRECTIVE = re.compile(r"!\s*castep-lint\s*:\s*disable\s*=\s*(.+)", re.IGNORECASE)
MARKER = re.compile(r"castep-lint", re.IGNORECASE)

# Name for problems with the comments themselves, which cannot be disabled
DIRECTIVE_CHECK = "DIRECTIVE"

Point = tuple[int, ...]


class Suppressions:
    """Checks disabled by comments in a single source file"""

    def __init__(self, raw_text: bytes, valid_checks: set[str]):
        self.lines = raw_text.split(b"\n")
        self.valid_checks = valid_checks

        # (start, end) of every routine, with the checks disabled in it
        self.routines: dict[tuple[Point, Point], set[str]] = {}
        # Checks disabled by trailing comments, by row
        self.line_disables: dict[int, set[str]] = {}
        # Rows which end with a continuation "&"
        self.continued_rows: set[int] = set()

    def add_node(self, node: FortranNode, error_log: ErrorLogger) -> None:
        """Record anything relevant to disabling checks from a node of the source tree"""
        if node.ftype in FortranContexts:
            self.routines[_extent(node)] = set()
        elif node.is_type(Fortran.COMMENT):
            self._add_comment(node, error_log)
        elif node.node.type == "&" and node.node.text:
            self._add_continuation(node)

    def _add_comment(self, node: FortranNode, error_log: ErrorLogger) -> None:
        match = DIRECTIVE.fullmatch(node.raw.strip())
        if not match:
            if MARKER.search(node.raw):
                _warn(error_log, node, "Malformed castep-lint comment")
            return

        names = [name.strip() for name in match.group(1).split(",") if name.strip()]
        if not names:
            _warn(error_log, node, "castep-lint comment names no checks")
            return

        checks = set()
        for name in names:
            check = name.upper()
            if check in self.valid_checks:
                checks.add(check)
            else:
                expected = ", ".join(sorted(self.valid_checks))
                err = f"Unknown check '{name}' in castep-lint comment, expected one of {expected}"
                _warn(error_log, node, err)

        row, column = node.node.start_point
        parent = node.node.parent

        if not self._is_first_on_line(row, column):
            self.line_disables.setdefault(row, set()).update(checks)
        elif parent is not None and FortranNode(parent).ftype in FortranContexts:
            self.routines[_extent(FortranNode(parent))].update(checks)
        else:
            _warn(error_log, node, "castep-lint comment has no effect here")

    def _add_continuation(self, node: FortranNode) -> None:
        row, column = node.node.start_point
        # A leading "&" on a continued line does not continue it onto the next
        if not self._is_first_on_line(row, column):
            self.continued_rows.add(row)

    def _is_first_on_line(self, row: int, column: int) -> bool:
        return not self.lines[row][:column].strip()

    def _has_code(self, row: int) -> bool:
        line = self.lines[row].strip()
        return bool(line) and not line.startswith((b"!", b"#"))

    def _code_row(self, row: int, step: int) -> int | None:
        """Find the next row with code on it in the given direction, skipping comments"""
        row += step
        while 0 <= row < len(self.lines):
            if self._has_code(row):
                return row
            row += step
        return None

    def _statement_rows(self, row: int) -> range:
        """All rows of the statement on this row, following continuations"""
        start = row
        prev_row = self._code_row(start, -1)
        while prev_row is not None and prev_row in self.continued_rows:
            start = prev_row
            prev_row = self._code_row(start, -1)

        end = row
        next_row = self._code_row(end, 1)
        while end in self.continued_rows and next_row is not None:
            end = next_row
            next_row = self._code_row(end, 1)

        return range(start, end + 1)

    def finalise(self) -> None:
        """Extend checks disabled by trailing comments to all rows of their statements"""
        line_disables: dict[int, set[str]] = {}
        for row, checks in self.line_disables.items():
            for statement_row in self._statement_rows(row):
                line_disables.setdefault(statement_row, set()).update(checks)
        self.line_disables = line_disables

    def is_suppressed(self, error: FortranMsgBase) -> bool:
        """Has the check which found this error been disabled where it was found"""
        if error.check is None:
            return False

        if error.check in self.line_disables.get(error.start_point[0], set()):
            return True

        if not any(self.routines.values()):
            return False

        # Only the innermost routine applies, so contained routines do not inherit from their parent
        containing: list[tuple[Point, set[str]]] = [
            (start, checks)
            for (start, end), checks in self.routines.items()
            if start <= error.start_point < end
        ]
        if not containing:
            return False

        _, checks = max(containing, key=lambda routine: routine[0])
        return error.check in checks


def _extent(node: FortranNode) -> tuple[Point, Point]:
    return tuple(node.node.start_point), tuple(node.node.end_point)


def _warn(error_log: ErrorLogger, node: FortranNode, message: str) -> None:
    error_log.add_msg("Warning", node, message)
    error_log.errors[-1].check = DIRECTIVE_CHECK
