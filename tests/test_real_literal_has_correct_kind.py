# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_number_literal
from tests.conftest import Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"number_literal": [check_number_literal]}


def test_real_literal_with_dp(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0_dp"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_literal_with_version_kind(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0_version_kind"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_literal_with_other_kind(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0_sp"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_literal_missing_dp(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_literal_missing_dp_scientific(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0e5"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_literal_d0(parse: Parser, test_list: CheckFunctionDict):
    code = b"z = 1.0d5"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0
