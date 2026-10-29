# pylint: disable=W0621,C0116,C0114
import pickle

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
