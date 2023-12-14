from tree_sitter import Node

from castep_linter.fortran import fortran_nodes
from castep_linter.fortran.fortran_raw_types import Fortran, FortranLookup


def wrap_node(node: Node) -> "fortran_nodes.FortranNode":
    """Turn a tree-sitter node into a FortranNode of the correct type"""

    factory_dict = {
        Fortran.SUBROUTINE: fortran_nodes.FortranSubroutineNode,
        Fortran.FUNCTION: fortran_nodes.FortranFunctionNode,
        Fortran.SUBROUTINE_CALL: fortran_nodes.FortranCallExpression,
        Fortran.CALL_EXPRESSION: fortran_nodes.FortranCallExpression,
        Fortran.ARGUMENT_LIST: fortran_nodes.FortranArgumentList,
        Fortran.VARIABLE_DECLARATION: fortran_nodes.FortranVariableDeclaration,
    }

    if node.is_named:
        node_type_raw = node.type
        node_type = FortranLookup.get(node_type_raw, Fortran.UNKNOWN)
    else:
        node_type = Fortran.UNKNOWN

    factory_method = factory_dict.get(node_type, fortran_nodes.FortranNode)
    return factory_method(node)
