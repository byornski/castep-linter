"""Module containing an argument list parser"""
from enum import Enum, auto
from typing import ClassVar, Dict, List, Optional, Tuple

from castep_linter.fortran.fortran_node import Fortran, FortranNode, WrongNodeError
from castep_linter.fortran.identifier import Identifier


class ArgType(Enum):
    """Types of arguments for fortran functions/subroutines"""

    KEYWORD = auto()
    POSITION = auto()
    # NONE = auto()


class ArgParser:
    """Parser for fortran argument lists"""

    ALLOWED_NODES: ClassVar[List[Fortran]] = [Fortran.ARGUMENT_LIST]
    ArgType = ArgType

    def __init__(self, arg_list: Optional[FortranNode] = None):
        if arg_list:
            self.args, self.kwargs = parse_arg_list(arg_list)
        else:
            self.args, self.kwargs = [], {}

    def get(self, keyword: Identifier, position: Optional[int] = None):
        """Return a value from a fortran argument list by keyword and optionally position"""
        if position and len(self.args) >= position:
            return ArgType.POSITION, self.args[position - 1]
        if keyword in self.kwargs:
            return ArgType.KEYWORD, self.kwargs[keyword]

        err = f"Argument {keyword} not found in argument list"
        raise KeyError(err)


def parse_arg_list(node: FortranNode) -> Tuple[List[FortranNode], Dict[Identifier, FortranNode]]:
    """
    Convert a fortran argument list into a args, kwargs pair.
    The keyword arguments will be converted into identifiers.
    """
    if not node.is_type(Fortran.ARGUMENT_LIST):
        err = "Expected argument list"
        raise WrongNodeError(err)

    args = []
    kwargs = {}

    parsing_arg_list = True

    for child in node.children[1:-1:2]:
        if child.is_type(Fortran.KEYWORD_ARGUMENT):
            parsing_arg_list = False

        if parsing_arg_list:
            args.append(child)
        elif child.is_type(Fortran.KEYWORD_ARGUMENT):
            key, _, value = child.children
            kwargs[Identifier.from_node(key)] = value
        else:
            err = f"Unknown argument list item in keyword arguments: {child.type}"
            raise ValueError(err)

    return args, kwargs
