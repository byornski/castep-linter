from typing import Dict, Optional, Set

from tree_sitter import Node

from castep_linter.fortran.fortran_nodes.argument_types import ArgumentItem
from castep_linter.fortran.fortran_nodes.fortran_argument_list import FortranArgumentList
from castep_linter.fortran.fortran_nodes.fortran_node import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran, FType
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError


class FortranVariableDeclaration(FortranNode):
    """Class representing a variable declaration"""

    def __init__(self, var_decl_node: Node) -> None:
        super().__init__(var_decl_node)

        self.var_type = self.parse_fort_type()
        self.qualifiers = self.parse_fort_type_qualifiers()
        self.vars = self.parse_fort_var_names()
        self.args = self.parse_fort_var_size()

    def get_arg(self, keyword: Identifier, position: Optional[int] = None) -> ArgumentItem:
        """Get an argument from the call expression"""
        return self.args.get_arg(keyword, position)

    def get_initialized_vars(self) -> dict[Identifier, str]:
        """Get variables that have an initial value"""
        return {k: v for k, v in self.vars.items() if v}

    def parse_fort_type(self) -> FType:
        """Parse a variable declaration for type"""
        try:
            fortran_type = self.get(Fortran.INTRINSIC_TYPE).raw.upper()
            if fortran_type == "DOUBLE PRECISION":
                return FType.DOUBLE
            else:
                return FType[fortran_type]
        except KeyError:
            return FType.OTHER

    def parse_fort_type_qualifiers(self) -> Set[str]:
        """Parse a variable declaration for qualifiers, eg parameter"""
        qualifiers = set()
        for type_qualifier in self.get_children_by_name(Fortran.TYPE_QUALIFIER):
            qualifier = type_qualifier.raw.lower()
            qualifiers.add(qualifier)
        return qualifiers

    def parse_fort_var_size(self) -> FortranArgumentList:
        """Parse a variable declaration for a size, eg kind=8"""
        try:
            fortran_size = self.get(Fortran.SIZE).get(Fortran.ARGUMENT_LIST)
        except KeyError:
            return FortranArgumentList(None)

        if not isinstance(fortran_size, FortranArgumentList):
            err = f"Expected an argument list but got {fortran_size}"
            raise WrongNodeError(err)

        return fortran_size

    def parse_fort_var_names(self) -> Dict[Identifier, Optional[str]]:
        """Parse variable declaration statement for variables and optionally assignments"""
        myvars: Dict[Identifier, Optional[str]] = {}
        for assignment in self.get_children_by_name(Fortran.ASSIGNMENT_STMT):
            lhs, rhs = assignment.split()
            #   lhs, rhs = split_relational_node(assignment)
            varname = Identifier.from_node(lhs)
            if rhs.is_type(Fortran.STRING_LITERAL):
                myvars[varname] = rhs.parse_string_literal()
            else:
                myvars[varname] = None
        return myvars
