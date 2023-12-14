from typing import Optional

from tree_sitter import Node

from castep_linter.fortran.fortran_nodes.argument_types import ArgumentItem
from castep_linter.fortran.fortran_nodes.fortran_argument_list import FortranArgumentList
from castep_linter.fortran.fortran_nodes.fortran_node import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError


class FortranCallExpression(FortranNode):
    """Class representing a Fortran call expression"""

    def __init__(self, call_expression_node: Node) -> None:
        super().__init__(call_expression_node)

        self.name = self._get_name()

        try:
            args = self.get(Fortran.ARGUMENT_LIST)
        except KeyError:
            args = FortranArgumentList(None)

        if not isinstance(args, FortranArgumentList):
            err = f"Expected argument list but got {args}"
            raise WrongNodeError(err)

        self.args = args

    def _get_name(self) -> Identifier:
        try:
            return Identifier.from_node(self.get(Fortran.IDENTIFIER))
        except KeyError:
            return Identifier("")

    def get_arg(self, keyword: Identifier, position: Optional[int] = None) -> ArgumentItem:
        """Get an argument from the call expression"""
        return self.args.get_arg(keyword, position)

    def __str__(self):
        return f"{self.name=} {self.args=}"
