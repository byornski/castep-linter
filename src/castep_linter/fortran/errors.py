"""Module to handle errors, warnings and info messages"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterator, List, ClassVar, Union

from rich.console import Console
from tree_sitter import Node


class FortranMsgBase:
    """Base class for other static analysis problems to inherit from"""

    ERROR_TYPE: ClassVar[str] = "NONE"
    ERROR_STYLE: ClassVar[str]  = "grey"
    LINE_NUMBER_OFFSET = 8
    ERROR_SEVERITY: ClassVar[int] = 100

    def __init__(self, node: Node, message: str) -> None:
        self.message = message
        self.start_point = node.start_point
        self.end_point = node.end_point

    def print(self, filename: str, console) -> None:
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

    ERROR_TYPE: ClassVar[str] = "ERROR"
    ERROR_STYLE: ClassVar[str]  = "red"
    ERROR_SEVERITY: ClassVar[int] = 2


class FortranWarning(FortranMsgBase):
    """Warning message from static analysis"""

    ERROR_TYPE: ClassVar[str]  = "Warning"
    ERROR_STYLE: ClassVar[str]  = "yellow"
    ERROR_SEVERITY: ClassVar[int] = 1


class FortranInfo(FortranMsgBase):
    """Warning message from static analysis"""

    ERROR_TYPE: ClassVar[str]  = "Info"
    ERROR_STYLE: ClassVar[str]  = "Blue"
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
        raise ValueError(f"Unknown fortran diagnostic message type: {level}")
    return cls(node, message)


FORTRAN_ERRORS = {"Error": FortranError, "Warning": FortranWarning, "Info": FortranInfo}


@dataclass
class ErrorLogger:
    """Container for all errors and messages generated while analysing
    a Fortran file"""

    filename: str
    errors: List[FortranMsgBase] = field(default_factory=list)

    def __iter__(self) -> Iterator[FortranMsgBase]:
        return iter(self.errors)

    def add_msg(self, level: str, node: Node, message: str):
        """Add an error to the error list"""
        err = new_fortran_error(level, node, message)
        self.errors.append(err)

    def print(self, console: Console, level: str = "Warning") -> None:
        """Print all the contained errors above the level"""
        severity = FORTRAN_ERRORS[level].ERROR_SEVERITY

        for err in self.errors:
            if err.ERROR_SEVERITY >= severity:
                err.print(self.filename, console)

    def count_errors(self):
        """Count the number of errors in each category"""
        c = Counter(e.ERROR_SEVERITY for e in self.errors)
        return {err_str: c[err_type.ERROR_SEVERITY] for err_str, err_type in FORTRAN_ERRORS.items()}
