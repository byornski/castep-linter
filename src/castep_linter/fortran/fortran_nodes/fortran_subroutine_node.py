from castep_linter.fortran.fortran_nodes import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier


class FortranSubroutineNode(FortranNode):
    """Node representing a subroutine"""

    def get_context_identifier(self) -> Identifier:
        """Get the name of the subroutine"""
        return Identifier.from_node(self.get(Fortran.SUBROUTINE_STMT).get(Fortran.NAME))
