# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter import tests
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code


@pytest.fixture
def test_list():
    return {"call_expression": [tests.check_complex_has_dp]}


@pytest.fixture
def parser():
    return get_fortran_parser()


def test_other_function(parser, test_list):
    code = b"y = myownfunction(a, b, dp)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_correct(parser, test_list):
    code = b"y = CMPLX(a, b, dp)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_correct_keyword(parser, test_list):
    code = b"y = CMPLX(z, kind=dp)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_wrong_place(parser, test_list):
    code = b"y = CMPLX(z, dp)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_dp_missing(parser, test_list):
    code = b"y = CMPLX(a, b)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_wrong_kind(parser, test_list):
    code = b"y = CMPLX(a, b, x)"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1
