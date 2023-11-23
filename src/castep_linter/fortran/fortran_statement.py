""""Module with base class for Fortran code parser classes"""
from typing import ClassVar, List

from castep_linter.fortran.fortran_node import Fortran, FortranNode
from castep_linter.fortran.node_type_err import WrongNodeError


class FortranStatementParser:
    """Base class for fortran statement parsers"""

    ALLOWED_NODES: ClassVar[List[Fortran]] = []

    def __init__(self, node: FortranNode):
        if not any(node.is_type(ftype) for ftype in self.ALLOWED_NODES):
            err = f"{node.type} not in {self.ALLOWED_NODES}"
            raise WrongNodeError(err)

        self.node = node
