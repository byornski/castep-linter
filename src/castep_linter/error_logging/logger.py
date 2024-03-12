"""Module containing code for the high level error logger"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterator, List

from rich.console import Console

from castep_linter.error_logging import error_types
from castep_linter.fortran.fortran_nodes import FortranNode


@dataclass
class ErrorLogger:
    """Container for all errors and messages generated while analysing
    a Fortran file"""

    filename: str
    errors: List[error_types.FortranMsgBase] = field(default_factory=list)

    def __iter__(self) -> Iterator[error_types.FortranMsgBase]:
        return iter(self.errors)

    def add_msg(self, level: str, node: FortranNode, message: str):
        """Add an error to the error list"""
        err = error_types.new_fortran_error(level, node, message)
        self.errors.append(err)

    def print_errors(
        self,
        console: Console,
        level: str = "Warning",
        *,
        print_style: error_types.PrintStyle = error_types.PrintStyle.ANNOTATED,
    ) -> None:
        """Print all the contained errors above the level"""
        severity = error_types.ERROR_SEVERITY[level]

        for err in self.errors:
            if err.ERROR_SEVERITY >= severity:
                err.print_err(self.filename, console, print_style=print_style)

    def count_errors(self):
        """Count the number of errors in each category"""
        c = Counter(e.ERROR_SEVERITY for e in self.errors)
        return {
            err_str: c[err_severity] for err_str, err_severity in error_types.ERROR_SEVERITY.items()
        }

    def __len__(self):
        return len(self.errors)

    @property
    def has_errors(self):
        """Does the logger contain any errors"""
        return len(self) > 0

    def has_errors_above(self, level: str):
        """Does the logger contain any errors above the requested level"""
        error_severity = error_types.ERROR_SEVERITY[level]
        errors = (1 for e in self.errors if e.ERROR_SEVERITY >= error_severity)
        return sum(errors) > 0  # type: ignore
