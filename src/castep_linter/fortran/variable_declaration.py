"""Module holding the VariableDeclaration type"""
from enum import Enum, auto
from typing import ClassVar, Dict, List, Optional, Set, Tuple

from tree_sitter import Node

from castep_linter.fortran.argument_parser import ArgParser
from castep_linter.fortran.fortran_statement import FortranStatementParser


class FType(Enum):
    """Intrinsic variable types in fortran"""

    REAL = auto()
    DOUBLE = auto()
    COMPLEX = auto()
    INTEGER = auto()
    LOGICAL = auto()
    CHARACTER = auto()
    OTHER = auto()


def parse_fort_type(var_decl_node: Node) -> FType:
    """Parse a variable declaration for type"""
    try:
        fortran_type = var_decl_node.get_child_property("intrinsic_type").raw().upper()
        if fortran_type == "DOUBLE PRECISION":
            return FType.DOUBLE
        else:
            return FType[fortran_type]
    except KeyError:
        return FType.OTHER


def parse_fort_type_qualifiers(var_decl_node: Node) -> Set[str]:
    """Parse a variable declaration for qualifiers, eg parameter"""
    qualifiers = set()
    for type_qualifier in var_decl_node.get_children_by_name("type_qualifier"):
        qualifier = type_qualifier.raw(lower=True)
        qualifiers.add(qualifier)
    return qualifiers


def parse_fort_var_size(var_decl_node: Node) -> ArgParser:
    """Parse a variable declaration for a size, eg kind=8"""
    try:
        fortran_size = var_decl_node.get_child_property("size")
    except KeyError:
        return ArgParser()

    return ArgParser(fortran_size.get_child_property("argument_list"))


def parse_fort_var_names(var_decl_node: Node) -> Dict[str, Optional[str]]:
    """Parse variable declaration statement for variables and optionally assignments"""
    myvars: Dict[str, Optional[str]] = {}
    for assignment in var_decl_node.get_children_by_name("assignment_statement"):
        lhs, rhs = assignment.split()
        #   lhs, rhs = split_relational_node(assignment)
        varname = lhs.raw(lower=True)
        if rhs.type == "string_literal":
            myvars[varname] = rhs.parse_string_literal()
        else:
            myvars[varname] = None
    return myvars


class VariableDeclaration(FortranStatementParser):
    """Class representing a variable declaration"""

    ALLOWED_NODES: ClassVar[List[str]] = ["variable_declaration"]

    def __init__(self, var_decl_node: Node) -> None:
        super().__init__(var_decl_node)

        self.type = parse_fort_type(var_decl_node)
        self.qualifiers = parse_fort_type_qualifiers(var_decl_node)
        self.vars = parse_fort_var_names(var_decl_node)
        self.args = parse_fort_var_size(var_decl_node)

    def get_arg(self, keyword: str, position: Optional[int] = None) -> Tuple[ArgParser.ArgType, Node]:
        """Get an argument from the call expression"""
        return self.args.get(keyword, position)
