"""Module containing code for the high level error logger"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterator, List

from rich.console import Console
from tree_sitter import Node

from castep_linter.error_logging import error_types


@dataclass
class ErrorLogger:
    """Container for all errors and messages generated while analysing
    a Fortran file"""

    filename: str
    errors: List[error_types.FortranMsgBase] = field(default_factory=list)

    def __iter__(self) -> Iterator[error_types.FortranMsgBase]:
        return iter(self.errors)

    def add_msg(self, level: str, node: Node, message: str):
        """Add an error to the error list"""
        err = error_types.new_fortran_error(level, node, message)
        self.errors.append(err)

    def printc(self, console: Console, level: str = "Warning") -> None:
        """Print all the contained errors above the level"""
        severity = error_types.FORTRAN_ERRORS[level].ERROR_SEVERITY

        for err in self.errors:
            if err.ERROR_SEVERITY >= severity:
                err.print_err(self.filename, console)

    def count_errors(self):
        """Count the number of errors in each category"""
        c = Counter(e.ERROR_SEVERITY for e in self.errors)
        return {
            err_str: c[err_type.ERROR_SEVERITY]
            for err_str, err_type in error_types.FORTRAN_ERRORS.items()
        }
