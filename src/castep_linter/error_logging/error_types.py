"""Module to handle errors, warnings and info messages"""
from typing import ClassVar, Dict

from castep_linter.fortran.fortran_nodes import FortranNode


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

    def print_err(self, filename: str, console) -> None:
        """Print the error to the supplied console"""
        console.print(self, style=self.ERROR_STYLE)
        context = self.context(filename, underline=True)
        if context:
            console.print(context)

    def context(self, filename, *, underline=False):
        """Print a line of context for the current error"""
        context = ""

        with open(filename, "rb") as fd:
            start_line, start_char = self.start_point
            end_line, end_char = self.end_point
            num_lines = end_line - start_line + 1
            num_chars = end_char - start_char

            file_str = str(filename)

            if num_lines == 1:
                line = fd.read().splitlines()[start_line].decode(errors="replace")
                context = f"{file_str}:{start_line+1:{self.LINE_NUMBER_OFFSET}}>{line}"
                if underline:
                    context += (
                        "\n"
                        + " " * (len(file_str) + 1)
                        + " " * (self.LINE_NUMBER_OFFSET + 1)
                        + " " * start_char
                        + "^" * num_chars
                    )
        return context

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


FORTRAN_ERRORS: Dict[str, type[FortranMsgBase]] = {
    "Error": FortranError,
    "Warn": FortranWarning,
    "Info": FortranInfo,
}

ERROR_SEVERITY: Dict[str, int] = {k: v.ERROR_SEVERITY for k, v in FORTRAN_ERRORS.items()}
