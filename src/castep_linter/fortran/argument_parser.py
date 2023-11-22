"""Module containing an argument list parser"""
from enum import Enum, auto
from typing import ClassVar, List, Optional

from tree_sitter import Node

from castep_linter.fortran.parser import parse_arg_list


class ArgType(Enum):
    """Types of arguments for fortran functions/subroutines"""

    KEYWORD = auto()
    POSITION = auto()
    # NONE = auto()


class ArgParser:
    """Parser for fortran argument lists"""

    ALLOWED_NODES: ClassVar[List[str]] = ["argument_list"]
    ArgType = ArgType

    def __init__(self, arg_list: Optional[Node] = None):
        if arg_list:
            self.args, self.kwargs = parse_arg_list(arg_list)
        else:
            self.args, self.kwargs = [], {}

    def get(self, keyword: str, position: Optional[int] = None):
        """Return a value from a fortran argument list by keyword and optionally position"""
        if position and len(self.args) >= position:
            return ArgType.POSITION, self.args[position - 1]
        if keyword.lower() in self.kwargs:
            return ArgType.KEYWORD, self.kwargs[keyword]

        err = f"Argument {keyword} not found in argument list"
        raise KeyError(err)
