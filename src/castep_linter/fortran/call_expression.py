"""Module holding the CallExpression type"""
from typing import ClassVar, List, Optional, Tuple

from tree_sitter import Node

from castep_linter.fortran.argument_parser import ArgParser
from castep_linter.fortran.fortran_statement import FortranStatementParser


class CallExpression(FortranStatementParser):
    """Class representing a fortran call expression"""

    ALLOWED_NODES: ClassVar[List[str]] = ["call_expression", "subroutine_call"]

    def __init__(self, call_expression_node: Node) -> None:
        super().__init__(call_expression_node)

        self.name = self._get_name(call_expression_node)
        try:
            arg_list = call_expression_node.get_child_property("argument_list")
        except KeyError:
            self.args = []
        else:
            self.args = ArgParser(arg_list)

    def get_arg(self, keyword: str, position: Optional[int] = None) -> Tuple[ArgParser.ArgType, Node]:
        """Get an argument from the call expression"""
        return self.args.get(keyword, position)

    def _get_name(self, node):
        try:
            return node.get_child_property("identifier").raw(lower=True)
        except LookupError:
            return None

    def __str__(self):
        return f"{self.name=} {self.args=}"
