from typing import Optional

from tree_sitter import Node

from castep_linter.fortran import node_factory
from castep_linter.fortran.fortran_nodes.argument_types import (
    ArgumentItem,
    KeywordArgument,
    PositionalArgument,
)
from castep_linter.fortran.fortran_nodes.fortran_node import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier

SKIP_ARGS_LIST = {"&", ",", ""}


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

        # Arguments sit between the opening "(" and the final ")". The "(" is not always the
        # first child (eg "allocate(...)")
        children = self.children
        open_bracket = next((i for i, c in enumerate(children) if c.raw == "("), None)
        if open_bracket is None:
            # Kinds may be given without brackets, eg the 8 in "real*8"
            args = [c for c in children if c.node.is_named and not c.is_type(Fortran.COMMENT)]
            return args, kwargs

        for child in children[open_bracket + 1 : -1]:
            if child.is_type(Fortran.COMMENT) or (
                child.is_type(Fortran.UNKNOWN) and child.raw in SKIP_ARGS_LIST
            ):
                continue

            if child.is_type(Fortran.KEYWORD_ARGUMENT):
                parsing_arg_list = False

            if parsing_arg_list:
                args.append(child)
            elif child.is_type(Fortran.KEYWORD_ARGUMENT):
                # Look up by field as line continuations can add extra children, eg "kind=&"
                key = child.node.child_by_field_name("name")
                value = child.node.child_by_field_name("value")
                if key is None or value is None:
                    err = f"Unable to parse keyword argument: {child.raw}"
                    raise ValueError(err)
                keyword = Identifier.from_node(node_factory.wrap_node(key))
                kwargs[keyword] = node_factory.wrap_node(value)
            else:
                err = f"Unknown argument list item in keyword arguments: {child.type}: \n{child.raw}\nin\n{self.raw}"
                raise ValueError(err)

        return args, kwargs
