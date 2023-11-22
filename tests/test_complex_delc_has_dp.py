# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter import tests
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code


@pytest.fixture
def test_list():
    return {"variable_declaration": [tests.test_real_dp_declaration]}


@pytest.fixture
def parser():
    return get_fortran_parser()


def test_complex_dp_correct(parser, test_list):
    code = b"complex(kind=dp) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


@pytest.mark.skip(reason="Not current implemented")
def test_complex_dp_correctb(parser, test_list):
    code = b"complex, kind(dp) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_no_kind(parser, test_list):
    code = b"complex, intent(in) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_integer_kind_with_keyword(parser, test_list):
    code = b"complex(kind=8) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_integer_kind_without_keyword(parser, test_list):
    code = b"complex(8) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_bad_var_kind_without_keyword(parser, test_list):
    code = b"complex(x) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_bad_var_kind_with_keyword(parser, test_list):
    code = b"complex(kind=x) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1
