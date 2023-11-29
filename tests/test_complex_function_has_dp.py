# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_complex_has_dp
from tests.conftest import Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"call_expression": [check_complex_has_dp]}


def test_other_function(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = myownfunction(a, b, dp)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_correct(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = CMPLX(a, b, dp)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_correct_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = CMPLX(z, kind=dp)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_wrong_place(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = CMPLX(z, dp)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_dp_missing(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = CMPLX(a, b)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_wrong_kind(parse: Parser, test_list: CheckFunctionDict):
    code = b"y = CMPLX(a, b, x)"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1
