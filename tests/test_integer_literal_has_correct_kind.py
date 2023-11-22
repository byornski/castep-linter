# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter import tests
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code


@pytest.fixture
def test_list():
    return {"number_literal": [tests.test_number_literal]}


@pytest.fixture
def parser():
    return get_fortran_parser()


def test_integer_literal_no_dp(parser, test_list):
    code = b"z = 1"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_integer_literal_has_dp(parser, test_list):
    code = b"z = 1_dp"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1
