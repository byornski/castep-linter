from castep_linter.fortran.fortran_nodes.fortran_node import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier


class FortranFunctionNode(FortranNode):
    """Node representing a function"""

    def get_context_identifier(self) -> Identifier:
        """Get the name of the function"""
        return Identifier.from_node(self.get(Fortran.FUNCTION_STMT).get(Fortran.NAME))
