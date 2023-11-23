"""Fortran identifier Class Module"""
from castep_linter.fortran.fortran_node import FortranNode


class Identifier:
    """Represents a type insensitive identifier in Fortran"""

    def __init__(self, name: str):
        self.lower_name = name.lower()

    @classmethod
    def from_node(cls, node: FortranNode) -> "Identifier":
        """Create an identifier directly from a node"""
        return Identifier(node.raw)

    def __repr__(self):
        return self.lower_name

    def __hash__(self):
        return hash(self.lower_name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.lower_name == other.lower()
        if isinstance(other, Identifier):
            return self.lower_name == other.lower_name.lower()
        err = "Can only compare identifiers with other identifiers"
        raise TypeError(err)
