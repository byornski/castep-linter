"""Tests for Fortran code in CASTEP"""
from importlib import resources as impresources
from typing import Dict, Generator, List, Tuple

from tree_sitter import Language, Parser, Tree

from castep_linter.fortran.fortran_node import FortranNode
from castep_linter.fortran.type_checking import node_type_check


def traverse_tree(tree: Tree) -> Generator[FortranNode, None, None]:
    """Traverse a tree-sitter tree in a depth first search"""
    cursor = tree.walk()

    reached_root = False
    while not reached_root:
        yield FortranNode(cursor.node)

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False


def get_fortran_parser():
    """Get a tree-sitter-fortran parser from src"""

    tree_sitter_src_ref = impresources.files("castep_linter") / "tree_sitter_fortran"
    with impresources.as_file(tree_sitter_src_ref) as tree_sitter_src:
        fortran_language = Language(tree_sitter_src / "fortran.so", "fortran")

    parser = Parser()
    parser.set_language(fortran_language)
    return parser


FORTRAN_CONTEXTS = {
    "subroutine": "subroutine_statement.name",
    "function": "function_statement.name",
    "module": "module_statement.name",
    "submodule": "submodule_statement.name",
    "program": "program_statement.name",
}


@node_type_check("argument_list")
def parse_arg_list(node: FortranNode) -> Tuple[List[FortranNode], Dict[str, FortranNode]]:
    """
    Convert a fortran argument list into a args, kwargs pair.
    If lower_kwargs is true, the keyword arguments will be lowercased.
    """

    args = []
    kwargs = {}

    parsing_arg_list = True

    for child in node.get_children()[1:-1:2]:  # TODO REPLACE NODE
        if child.type == "keyword_argument":
            parsing_arg_list = False

        if parsing_arg_list:
            args.append(child)
        elif child.type == "keyword_argument":
            key, _, value = child.get_children()
            kwargs[key.raw(lower=True)] = value

        else:
            err = f"Unknown argument list item in keyword arguments: {child.type}"
            raise ValueError(err)

    return args, kwargs
