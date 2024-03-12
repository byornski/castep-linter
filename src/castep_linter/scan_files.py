"""Static code analysis tool for castep"""

import argparse
import logging
import pathlib
import sys

from rich.console import Console

from castep_linter import error_logging
from castep_linter.error_logging.error_types import PrintStyle
from castep_linter.error_logging.json_writer import write_json
from castep_linter.error_logging.xml_writer import write_xml
from castep_linter.fortran import parser
from castep_linter.tests import CheckFunction, test_list

# done - complex(var) vs complex(var,dp) or complex(var, kind=dp)
# done - allocate without stat and stat not checked. deallocate?
# done - integer_dp etc
# real with trailing . not .0 or .0_dp?
# io_allocate_abort with wrong subname
# tabs & DOS line endings, whitespace, comments?


def run_tests_on_code(
    fort_tree: parser.FortranTree, test_dict: dict[str, list[CheckFunction]], filename: str
) -> error_logging.ErrorLogger:
    """Run all available tests on the supplied source code"""
    error_log = error_logging.ErrorLogger(filename)

    for node in fort_tree.walk():
        # Have to check for is_named here as we want the statements,
        # not literal words like subroutine
        if node.type in test_dict:
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
        choices=error_logging.ERROR_SEVERITY.keys(),
    )
    arg_parser.add_argument(
        "-f",
        "--format",
        type=lambda x: str(x).upper(),
        choices=[x.name for x in PrintStyle],
        help="Format screen printing",
        default="ANNOTATED",
    )
    arg_parser.add_argument(
        "-x", "--xml", type=pathlib.Path, help="File for JUnit xml output if required"
    )
    arg_parser.add_argument(
        "-j", "--json", type=pathlib.Path, help="File for Jenkins json output if required"
    )
    arg_parser.add_argument("-q", "--quiet", action="store_true", help="Do not write to console")
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Turn on debug output")
    arg_parser.add_argument(
        "-p", "--print-tree", action="store_true", help="Print the parsed source tree"
    )
    arg_parser.add_argument("file", nargs="+", type=path, help="Files to scan")
    return arg_parser.parse_args()


def main() -> None:
    """Main entry point for the CASTEP linter"""
    args = parse_args()

    console = Console(soft_wrap=True)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    error_logs = {}

    for file in args.file:
        # Parse the source file
        fortan_tree = parser.FortranTree.from_file(file)

        # Print for development
        if args.print_tree:
            fortan_tree.display(console.print)

        # Actually run the tests
        try:
            error_log = run_tests_on_code(fortan_tree, test_list, str(file))
        except UnicodeDecodeError:
            logging.error("Failed to properly decode %s", file)
            raise
        except Exception:
            logging.error("Failed to properly parse %s", file)
            raise

        # Report any errors
        if not args.quiet:
            error_log.print_errors(console, level=args.level, print_style=PrintStyle[args.format])

            err_count = error_log.count_errors()

            console.print(
                f"{len(error_log.errors)} issues in {file} ({err_count['Error']} errors,"
                f" {err_count['Warn']} warnings, {err_count['Info']} info)"
            )

        error_logs[str(file)] = error_log

    # Write junit xml file
    if args.xml:
        write_xml(args.xml, error_logs, error_logging.ERROR_SEVERITY[args.level])
    if args.json:
        write_json(args.json, error_logs, error_logging.ERROR_SEVERITY[args.level])

    # Exit with an error code if there were any errors
    if any(e.has_errors_above(args.level) for e in error_logs.values()):
        sys.exit(1)
    else:
        sys.exit(0)
