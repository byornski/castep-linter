# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_number_literal
from tests.conftest import Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"number_literal": [check_number_literal]}


def test_integer_literal_no_dp(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_integer_literal_has_dp(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1_dp"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_integer_int64(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1_int64"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_integer_int32(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1_int32"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0
