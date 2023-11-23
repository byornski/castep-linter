"""Module holding the CallExpression type"""
from typing import ClassVar, List, Optional, Tuple

from castep_linter.fortran.argument_parser import ArgParser, ArgType
from castep_linter.fortran.fortran_node import Fortran, FortranNode
from castep_linter.fortran.fortran_statement import FortranStatementParser
from castep_linter.fortran.identifier import Identifier


class CallExpression(FortranStatementParser):
    """Class representing a fortran call expression"""

    ALLOWED_NODES: ClassVar[List[Fortran]] = [Fortran.CALL_EXPRESSION, Fortran.SUBROUTINE_CALL]

    def __init__(self, call_expression_node: FortranNode) -> None:
        super().__init__(call_expression_node)

        self.name = _get_name(call_expression_node)

        try:
            arg_list = call_expression_node.get(Fortran.ARGUMENT_LIST)
        except KeyError:
            arg_list = None

        self.args = ArgParser(arg_list)

    def get_arg(
        self, keyword: Identifier, position: Optional[int] = None
    ) -> Tuple[ArgType, FortranNode]:
        """Get an argument from the call expression"""
        return self.args.get(keyword, position)

    def __str__(self):
        return f"{self.name=} {self.args=}"


def _get_name(node: FortranNode) -> Identifier:
    try:
        return Identifier.from_node(node.get(Fortran.IDENTIFIER))
    except KeyError:
        return Identifier("")
