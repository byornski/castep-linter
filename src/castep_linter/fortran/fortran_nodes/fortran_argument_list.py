from typing import Optional

from tree_sitter import Node

from castep_linter.fortran.fortran_nodes.argument_types import (
    ArgumentItem,
    KeywordArgument,
    PositionalArgument,
)
from castep_linter.fortran.fortran_nodes.fortran_node import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier


class FortranArgumentList(FortranNode):
    """Parser for fortran argument lists"""

    def __init__(self, arg_list: Optional[Node]):
        if arg_list:
            super().__init__(arg_list)

        if arg_list:
            self.args, self.kwargs = self._parse_arg_list()
        else:
            self.args, self.kwargs = [], {}

    def get_arg(self, keyword: Identifier, position: Optional[int] = None) -> ArgumentItem:
        """Return a value from a fortran argument list by keyword and optionally position"""
        if position and len(self.args) >= position:
            return PositionalArgument(self.args[position - 1])
        if keyword in self.kwargs:
            return KeywordArgument(self.kwargs[keyword])

        err = f"Argument {keyword} not found in argument list"
        raise KeyError(err)

    def _parse_arg_list(self):
        """
        Convert a fortran argument list into a args, kwargs pair.
        The keyword arguments will be converted into identifiers.
        """

        args = []
        kwargs = {}

        parsing_arg_list = True

        for child in self.children[1:-1]:
            if child.raw == ",":
                continue

            if child.is_type(Fortran.KEYWORD_ARGUMENT):
                parsing_arg_list = False

            if parsing_arg_list:
                args.append(child)
            elif child.is_type(Fortran.KEYWORD_ARGUMENT):
                key, _, value = child.children
                kwargs[Identifier.from_node(key)] = value
            elif child.is_type(Fortran.COMMENT):
                continue
            else:
                err = f"Unknown argument list item in keyword arguments: {child.type}: \n{child.raw}\nin\n{self.raw}"
                raise ValueError(err)

        return args, kwargs
