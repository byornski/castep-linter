"""Module to handle errors, warnings and info messages"""
from typing import ClassVar
from tree_sitter import Node


class FortranMsgBase:
    """Base class for other static analysis problems to inherit from"""

    ERROR_TYPE: ClassVar[str] = "NONE"
    ERROR_STYLE: ClassVar[str] = "grey"
    LINE_NUMBER_OFFSET = 8
    ERROR_SEVERITY: ClassVar[int] = 100

    def __init__(self, node: Node, message: str) -> None:
        self.message = message
        self.start_point = node.start_point
        self.end_point = node.end_point

    def print_err(self, filename: str, console) -> None:
        """Print the error to the supplied console"""
        console.print(f"{self.ERROR_TYPE}: {self.message}", style=self.ERROR_STYLE)

        with open(filename, "rb") as fd:
            start_line, start_char = self.start_point
            end_line, end_char = self.end_point
            num_lines = end_line - start_line + 1
            num_chars = end_char - start_char

            file_str = str(filename)

            if num_lines == 1:
                line = fd.read().splitlines()[start_line].decode(errors="replace")
                console.print(f"{file_str}:{start_line+1:{self.LINE_NUMBER_OFFSET}}>{line}")
                console.print(
                    " " * (len(file_str) + 1)
                    + " " * (self.LINE_NUMBER_OFFSET + 1)
                    + " " * start_char
                    + "^" * num_chars
                )


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


def new_fortran_error(level: str, node: Node, message: str) -> FortranMsgBase:
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

FORTRAN_ERRORS = {
    "Error": FortranError,
    "Warning": FortranWarning,
    "Info": FortranInfo,
}
