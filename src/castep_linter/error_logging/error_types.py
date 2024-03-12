"""Module to handle errors, warnings and info messages"""

from enum import Enum, auto
from typing import ClassVar, Dict, Literal

from castep_linter.fortran.fortran_nodes import FortranNode


class PrintStyle(Enum):
    """Error print styles"""

    ANNOTATED = auto()
    GCC = auto()


class FortranMsgBase:
    """Base class for other static analysis problems to inherit from"""

    ERROR_TYPE: ClassVar[str] = "NONE"
    ERROR_STYLE: ClassVar[str] = "grey"
    LINE_NUMBER_OFFSET = 8
    ERROR_SEVERITY: ClassVar[int] = 100

    def __init__(self, node: FortranNode, message: str) -> None:
        self.message = message
        self.start_point = node.node.start_point  # TODO FIX
        self.end_point = node.node.end_point

    def print_err(
        self, filename: str, console, *, print_style: PrintStyle = PrintStyle.ANNOTATED
    ) -> None:
        """Print the error to the supplied console"""

        if print_style is PrintStyle.ANNOTATED:
            console.print(self, style=self.ERROR_STYLE)
            context = self.context(filename, underline=True)
        elif print_style is PrintStyle.GCC:
            context = self._gcc_format(filename)

        if context:
            console.print(context)

    def _gcc_format(self, filename):
        """Format errors like the GCC"""
        start_line, _ = self.line_ranges
        start_char, _ = self.char_ranges

        return f"{filename}:{start_line+1}:{start_char}: {self.ERROR_TYPE}: {self.message}"

    def context(self, filename, *, underline=False):
        """Print a line of context for the current error"""
        context = ""

        with open(filename, "rb") as fd:
            start_line, _ = self.line_ranges
            start_char, _ = self.char_ranges

            file_str = str(filename)

            if self.num_lines == 1:
                line = fd.read().splitlines()[start_line].decode(errors="replace")
                context = f"{file_str}:{start_line+1:{self.LINE_NUMBER_OFFSET}}>{line}"
                if underline:
                    context += (
                        "\n"
                        + " " * (len(file_str) + 1)
                        + " " * (self.LINE_NUMBER_OFFSET + 1)
                        + " " * start_char
                        + "^" * self.num_chars
                    )
        return context

    @property
    def line_ranges(self):
        """Start and end line as a tuple"""
        return self.start_point[0], self.end_point[0]

    @property
    def num_lines(self):
        """Number of lines covering issue"""
        return self.line_ranges[1] - self.line_ranges[0] + 1

    @property
    def char_ranges(self):
        """Start and end chars as a tuple"""
        return self.start_point[1], self.end_point[1]

    @property
    def num_chars(self):
        """Number of characters covering issue"""
        return self.char_ranges[1] - self.char_ranges[0]

    def __repr__(self):
        return f"{self.ERROR_TYPE}: {self.message}"


class FortranError(FortranMsgBase):
    """Fatal static analysis problem in code"""

    ERROR_TYPE: ClassVar[str] = "Error"
    ERROR_STYLE: ClassVar[str] = "red"
    ERROR_SEVERITY: ClassVar[int] = 2


class FortranWarning(FortranMsgBase):
    """Warning message from static analysis"""

    ERROR_TYPE: ClassVar[str] = "Warning"
    ERROR_STYLE: ClassVar[str] = "yellow"
    ERROR_SEVERITY: ClassVar[int] = 1


class FortranInfo(FortranMsgBase):
    """Warning message from static analysis"""

    ERROR_TYPE: ClassVar[str] = "Info"
    ERROR_STYLE: ClassVar[str] = "Blue"
    ERROR_SEVERITY: ClassVar[int] = 0


def new_fortran_error(level: str, node: FortranNode, message: str) -> FortranMsgBase:
    """Generate a new fortran diagnostic message"""
    cls = FortranMsgBase
    if level == "Error":
        cls = FortranError
    elif level == "Warning":
        cls = FortranWarning
    elif level == "Info":
        cls = FortranInfo
    else:
        raise ValueError("Unknown fortran diagnostic message type: " + level)
    return cls(node, message)


ErrorNames = Literal["Error", "Warn", "Info"]

FORTRAN_ERRORS: Dict[ErrorNames, type[FortranMsgBase]] = {
    "Error": FortranError,
    "Warn": FortranWarning,
    "Info": FortranInfo,
}

ERROR_SEVERITY: Dict[str, int] = {k: v.ERROR_SEVERITY for k, v in FORTRAN_ERRORS.items()}
