"""Tests for Fortran code in CASTEP"""
from collections import namedtuple
from enum import Enum, auto
from importlib import resources as impresources
from typing import Dict, List, Optional, Set, Tuple, Union

from tree_sitter import Language, Node, Parser


def get_fortran_parser():
    """Get a tree-sitter-fortran parser from src"""

    tree_sitter_src_ref = impresources.files("castep_linter") / "tree_sitter_fortran"
    with impresources.as_file(tree_sitter_src_ref) as tree_sitter_src:
        fortran_language = Language(tree_sitter_src / "fortran.so", "fortran")
        
    parser = Parser()
    parser.set_language(fortran_language)
    return parser


ContextData = namedtuple("ContextData", ["type", "get_name"])


FORTRAN_CONTEXTS = {
    "subroutine": ContextData("subroutine", "subroutine_statement.name"),
    "function": ContextData("function", "function_statement.name"),
    "module": ContextData("module", "module_statement.name"),
    "submodule": ContextData("submodule", "submodule_statement.name"),
    "program": ContextData("program", "program_statement.name"),
}


def is_fortran_subprogram(node) -> bool:
    """Check if a node contains a fortran context (subprogram, subroutine, etc)"""
    if not node.is_named:
        return False
    return node.type in FORTRAN_CONTEXTS


def get_child_by_name(node, typename: str) -> Node:
    """Return the first child node with the requested type"""
    for c in node.named_children:
        if c.type == typename:
            return c
    raise KeyError(f'"{typename}" not found in children of node {node}')


def get_children_by_name(node, typename: str) -> List[Node]:
    """Return all the children with the requested type"""
    return [c for c in node.named_children if c.type == typename]


def get_child_property(node, prop: str) -> Node:
    """Finds a nested property of the form node.subroutine_statment.name"""
    properties = prop.split(".")
    cursor = node
    for p in properties:
        cursor = get_child_by_name(cursor, p)
    return cursor


def get_child_property_str(node, prop: str) -> str:
    """
    Finds a nested property of the form node.subroutine_statment.name and
    returns the contained code as unicode
    """
    return get_child_property(node, prop).text.decode()


def node_of_type(node, typename: Union[str, List[str]]) -> bool:
    """Check if a node is of this type"""
    if isinstance(typename, str):
        return node.is_named and node.type == typename

    return node.is_named and any(node.type == t for t in typename)


def get_fortran_subprogram_name(node: Node) -> str:
    """Gets the name of a fortran context"""
    assert is_fortran_subprogram(node)
    return get_child_property(node, FORTRAN_CONTEXTS[node.type].get_name).text.decode()


def parse_arg_list(node: Node, lower: bool = False) -> Tuple[List[Node], Dict[str, Node]]:
    """
    Convert a fortran argument list into a args, kwargs pair.
    If lower_kwargs is true, the keyword arguments will be lowercased.
    """
    assert node.type == "argument_list"

    args = []
    kwargs = {}

    parsing_arg_list = True

    for child in node.children[1:-1:2]:
        if child.type == "keyword_argument":
            parsing_arg_list = False

        if parsing_arg_list:
            args.append(child)
        elif child.type == "keyword_argument":
            key, _, value = child.children
            kwargs[get_code(key, lower=lower)] = value

        else:
            raise ValueError(f"Unknown argument list item in keyword arguments: {child.type}")

    return args, kwargs


def get_code(node: Node, lower=False) -> str:
    """Return a string of all the text in a node as unicode"""
    if lower:
        return node.text.decode().lower()
    else:
        return node.text.decode()


class ArgType(Enum):
    """Types of arguments for fortran functions/subroutines"""

    KEYWORD = auto()
    POSITION = auto()
    # NONE = auto()


class FType(Enum):
    """Intrinsic variable types in fortran"""

    REAL = auto()
    DOUBLE = auto()
    COMPLEX = auto()
    INTEGER = auto()
    LOGICAL = auto()
    CHARACTER = auto()
    OTHER = auto()


def split_relational_node(node: Node) -> Tuple[Node, Node]:
    """Split a relational node with a left and right part into the two child nodes"""
    left = node.child_by_field_name("left")
    assert left is not None, f"LHS of expression is none: {get_code(node)}"
    right = node.child_by_field_name("right")
    assert right is not None, f"RHS of expression is none: {get_code(node)}"
    return left, right


def get_call_expression_name(node: Node) -> Optional[str]:
    """Get the name of a function or subroutine in a call expression"""
    assert node_of_type(node, ["call_expression", "subroutine_call"])

    try:
        return get_child_property_str(node, "identifier").lower()
    except LookupError:
        return None


class FortranStatementParser:
    """Base class for fortran statement parsers"""

    ALLOWED_NODES: List[str] = []

    def __init__(self, node: Node):
        assert node_of_type(node, self.ALLOWED_NODES), f"{node.type} not in {self.ALLOWED_NODES}"
        self.node = node


def get_arg(args, kwargs, keyword: str, position: Optional[int] = None) -> Tuple[ArgType, Node]:
    """Get an argument from the call expression"""
    if position and len(args) >= position:
        return ArgType.POSITION, args[position - 1]
    if keyword.lower() in kwargs:
        return ArgType.KEYWORD, kwargs[keyword]

    raise KeyError(f"Argument {keyword} not found in argument list")


class CallExpression(FortranStatementParser):
    """Class representing a fortran call expression"""

    ALLOWED_NODES = ["call_expression", "subroutine_call"]

    def __init__(self, call_expression_node: Node) -> None:
        super().__init__(call_expression_node)

        self.name = get_call_expression_name(call_expression_node)
        try:
            arg_list = get_child_property(call_expression_node, "argument_list")
            self.args, self.kwargs = parse_arg_list(arg_list, lower=True)
        except KeyError:
            self.args = []
            self.kwargs = {}


    def get_arg(self, keyword: str, position: Optional[int] = None) -> Tuple[ArgType, Node]:
        """Get an argument from the call expression"""
        return get_arg(self.args, self.kwargs, keyword, position)

    def __str__(self):
        return f"{self.name=} {self.args=} {self.kwargs=}"


def parse_fort_type(var_decl_node: Node) -> FType:
    """Parse a variable declaration for type"""
    try:
        fortran_type = get_code(get_child_property(var_decl_node, "intrinsic_type")).upper()
        if fortran_type == "DOUBLE PRECISION":
            return FType.DOUBLE
        else:
            return FType[fortran_type]
    except KeyError:
        return FType.OTHER


def parse_fort_type_qualifiers(var_decl_node: Node) -> Set[str]:
    """Parse a variable declaration for qualifiers, eg parameter"""
    qualifiers = set()
    for type_qualifier in get_children_by_name(var_decl_node, "type_qualifier"):
        qualifier = get_code(type_qualifier, lower=True)
        qualifiers.add(qualifier)
    return qualifiers


def parse_fort_var_size(var_decl_node: Node) -> Tuple[List[Node], Dict[str, Node]]:
    """Parse a variable declaration for a size, eg kind=8"""
    try:
        fortran_size = get_child_property(var_decl_node, "size")
    except KeyError:
        return [], {}

    arg_list = get_child_property(fortran_size, "argument_list")
    return parse_arg_list(arg_list, lower=True)


def parse_fort_var_names(var_decl_node: Node) -> Dict[str, Optional[str]]:
    """Parse variable declaration statement for variables and optionally assignments"""
    myvars: Dict[str, Optional[str]] = {}
    for assignment in get_children_by_name(var_decl_node, "assignment_statement"):
        lhs, rhs = split_relational_node(assignment)
        varname = get_code(lhs, lower=True)
        if rhs.type == "string_literal":
            myvars[varname]= parse_string_literal(rhs)
        else:
            myvars[varname] = None
    return myvars


def parse_string_literal(node: Node) -> str:
    "Parse a string literal object to get the string"
    return get_code(node).strip("\"'")


class VariableDeclaration(FortranStatementParser):
    """Class representing a variable declaration"""

    ALLOWED_NODES = ['variable_declaration']

    def __init__(self, var_decl_node: Node) -> None:
        super().__init__(var_decl_node)

        self.type = parse_fort_type(var_decl_node)
        self.qualifiers = parse_fort_type_qualifiers(var_decl_node)
        self.vars = parse_fort_var_names(var_decl_node)
        self.args, self.kwargs = parse_fort_var_size(var_decl_node)

    def get_arg(self, keyword: str, position: Optional[int] = None) -> Tuple[ArgType, Node]:
        """Get an argument from the call expression"""
        return get_arg(self.args, self.kwargs, keyword, position)
