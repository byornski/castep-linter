""""Module with base class for Fortran code parser classes"""
from typing import ClassVar, List

from castep_linter.fortran.fortran_node import FortranNode
from castep_linter.fortran.type_checking import WrongNodeError, node_of_type


class FortranStatementParser:
    """Base class for fortran statement parsers"""

    ALLOWED_NODES: ClassVar[List[str]] = []

    def __init__(self, node: FortranNode):
        if not node_of_type(node, self.ALLOWED_NODES):
            err = f"{node.type} not in {self.ALLOWED_NODES}"
            raise WrongNodeError(err)

        self.node = node
