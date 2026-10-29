# pylint: disable=W0621,C0116,C0114
import io
import pickle

from rich.console import Console

from castep_linter.error_logging.error_types import PrintStyle
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import test_list
from tests.conftest import CodeWrapper, Parser


def test_error_log_survives_pickling(parse: Parser, subroutine_wrapper: CodeWrapper):
    # Error logs are passed back from multiprocessing workers, so must round trip through pickle
    code = subroutine_wrapper(b"real :: x")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) > 0

    restored = pickle.loads(pickle.dumps(error_log))  # noqa: S301

    assert [(e.message, e.start_point, e.end_point) for e in restored.errors] == [
        (e.message, e.start_point, e.end_point) for e in error_log.errors
    ]


def test_gcc_format_is_one_indexed(parse: Parser):
    # GCC style diagnostics number both lines and columns from 1
    code = b"module foo\ncontains\nsubroutine x(y)\n  real :: z\nend subroutine x\nend module foo\n"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    (error,) = [e for e in error_log.errors if e.message == "No kind specifier"]

    output = io.StringIO()
    error.print_err("file.f90", Console(file=output, width=200), print_style=PrintStyle.GCC)

    assert output.getvalue().strip() == "file.f90:4:3: Error: No kind specifier"
