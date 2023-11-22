"""Tests for Fortran code in CASTEP"""
import functools
from importlib import resources as impresources
from typing import Dict, List, Tuple, Union

from tree_sitter import Language, Node, Parser

import castep_linter.fortran.monekey_patching
from castep_linter.fortran.type_checking import node_type_check


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





@node_type_check(*FORTRAN_CONTEXTS.keys())
def get_fortran_subprogram_name(node: Node) -> str:
    """Gets the name of a fortran context"""
    return 


@node_type_check("argument_list")
def parse_arg_list(node: Node) -> Tuple[List[Node], Dict[str, Node]]:
    """
    Convert a fortran argument list into a args, kwargs pair.
    If lower_kwargs is true, the keyword arguments will be lowercased.
    """

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
            kwargs[key.raw(lower=True)] = value

        else:
            err = f"Unknown argument list item in keyword arguments: {child.type}"
            raise ValueError(err)

    return args, kwargs




