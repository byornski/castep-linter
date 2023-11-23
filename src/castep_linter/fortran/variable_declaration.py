"""Module holding the VariableDeclaration type"""
from enum import Enum, auto
from typing import ClassVar, Dict, List, Optional, Set, Tuple

from castep_linter.fortran.argument_parser import ArgParser, ArgType
from castep_linter.fortran.fortran_node import Fortran, FortranNode
from castep_linter.fortran.fortran_statement import FortranStatementParser
from castep_linter.fortran.identifier import Identifier


class FType(Enum):
    """Intrinsic variable types in fortran"""

    REAL = auto()
    DOUBLE = auto()
    COMPLEX = auto()
    INTEGER = auto()
    LOGICAL = auto()
    CHARACTER = auto()
    OTHER = auto()


def parse_fort_type(var_decl_node: FortranNode) -> FType:
    """Parse a variable declaration for type"""
    try:
        fortran_type = var_decl_node.get(Fortran.INTRINSIC_TYPE).raw.upper()
        if fortran_type == "DOUBLE PRECISION":
            return FType.DOUBLE
        else:
            return FType[fortran_type]
    except KeyError:
        return FType.OTHER


def parse_fort_type_qualifiers(var_decl_node: FortranNode) -> Set[str]:
    """Parse a variable declaration for qualifiers, eg parameter"""
    qualifiers = set()
    for type_qualifier in var_decl_node.get_children_by_name(Fortran.TYPE_QUALIFIER):
        qualifier = type_qualifier.raw.lower()
        qualifiers.add(qualifier)
    return qualifiers


def parse_fort_var_size(var_decl_node: FortranNode) -> ArgParser:
    """Parse a variable declaration for a size, eg kind=8"""
    try:
        fortran_size = var_decl_node.get(Fortran.SIZE)
    except KeyError:
        return ArgParser()

    return ArgParser(fortran_size.get(Fortran.ARGUMENT_LIST))


def parse_fort_var_names(var_decl_node: FortranNode) -> Dict[Identifier, Optional[str]]:
    """Parse variable declaration statement for variables and optionally assignments"""
    myvars: Dict[Identifier, Optional[str]] = {}
    for assignment in var_decl_node.get_children_by_name(Fortran.ASSIGNMENT_STMT):
        lhs, rhs = assignment.split()
        #   lhs, rhs = split_relational_node(assignment)
        varname = Identifier.from_node(lhs)
        if rhs.is_type(Fortran.STRING_LITERAL):
            myvars[varname] = rhs.parse_string_literal()
        else:
            myvars[varname] = None
    return myvars


class VariableDeclaration(FortranStatementParser):
    """Class representing a variable declaration"""

    ALLOWED_NODES: ClassVar[List[Fortran]] = [Fortran.VARIABLE_DECLARATION]

    def __init__(self, var_decl_node: FortranNode) -> None:
        super().__init__(var_decl_node)

        self.type = parse_fort_type(var_decl_node)
        self.qualifiers = parse_fort_type_qualifiers(var_decl_node)
        self.vars = parse_fort_var_names(var_decl_node)
        self.args = parse_fort_var_size(var_decl_node)

    def get_arg(
        self, keyword: Identifier, position: Optional[int] = None
    ) -> Tuple[ArgType, FortranNode]:
        """Get an argument from the call expression"""
        return self.args.get(keyword, position)
