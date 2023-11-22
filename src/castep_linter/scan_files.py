"""Static code analysis tool for castep"""
import argparse
import pathlib
from typing import Generator

from rich.console import Console
from tree_sitter import Node, Parser, Tree

from castep_linter import error_logging
from castep_linter.fortran import parser
from castep_linter.tests import test_list


def traverse_tree(tree: Tree) -> Generator[Node, None, None]:
    """Traverse a tree-sitter tree in a depth first search"""
    cursor = tree.walk()

    reached_root = False
    while not reached_root:
        yield cursor.node

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


# done - complex(var) vs complex(var,dp) or complex(var, kind=dp)
# done - allocate without stat and stat not checked. deallocate?
# done - integer_dp etc
# real with trailing . not .0 or .0_dp?
# io_allocate_abort with wrong subname
# tabs & DOS line endings, whitespace, comments?


def run_tests_on_code(
    fort_parser: Parser, code: bytes, test_dict: dict, filename: str
) -> error_logging.ErrorLogger:
    """Run all available tests on the supplied source code"""
    tree = fort_parser.parse(code)
    error_log = error_logging.ErrorLogger(filename)

    for node in traverse_tree(tree):
        # Have to check for is_named here as we want the statements,
        # not literal words like subroutine
        if node.is_named and node.type in test_dict:
            for test in test_dict[node.type]:
                test(node, error_log)

    return error_log


def path(arg: str) -> pathlib.Path:
    """Check a file exists and if so, return a path object"""
    my_file = pathlib.Path(arg)
    if not my_file.is_file():
        err = f"The file {arg} does not exist!"
        raise argparse.ArgumentTypeError(err)
    return my_file


def parse_args():
    """Parse the command line args for a message print level and a list of filenames"""
    arg_parser = argparse.ArgumentParser(prog="castep-linter", description="Code linter for CASTEP")
    arg_parser.add_argument(
        "-l",
        "--level",
        help="Error message level",
        default="Info",
        choices=error_logging.FORTRAN_ERRORS.keys(),
    )
    arg_parser.add_argument("file", nargs="+", type=path)
    return arg_parser.parse_args()


def main() -> None:
    """Main entry point for the CASTEP linter"""
    args = parse_args()

    fortran_parser = parser.get_fortran_parser()
    console = Console()

    for file in args.file:
        with file.open("rb") as fd:
            raw_text = fd.read()

        error_log = run_tests_on_code(fortran_parser, raw_text, test_list, str(file))
        error_log.printc(console, level=args.level)

        err_count = error_log.count_errors()

        print(
            f"{len(error_log.errors)} issues in {file} ({err_count['Error']} errors,"
            f" {err_count['Warning']} warnings, {err_count['Info']} info)"
        )
