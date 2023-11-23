"""Tests for Fortran code in CASTEP"""
from importlib import resources as impresources
from typing import Generator

from tree_sitter import Language, Parser, Tree

from castep_linter.fortran.fortran_node import FortranNode


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
