# pylint: disable=W0621,C0116,C0114
from unittest import mock

import pytest

from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_real_dp_declaration
from tests.conftest import Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"variable_declaration": [check_real_dp_declaration]}


def test_wrong_node():
    mock_node = mock.Mock(**{"is_type.return_value": False})
    err_log = mock.MagicMock()
    with pytest.raises(WrongNodeError):
        check_real_dp_declaration(mock_node, err_log)


def test_real_dp_correct(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(kind=dp) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_version_kind_correct(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(kind=version_kind) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_dp_by_position(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(dp) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_dp_by_d0(parse: Parser, test_list: CheckFunctionDict):
    code = b"DOUBLE PRECISION :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_dp_no_kind(parse: Parser, test_list: CheckFunctionDict):
    code = b"real, intent(in) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_integer_kind_with_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(kind=8) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_integer_kind_without_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(8) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_bad_var_kind_without_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(x) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_bad_var_kind_with_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(kind=x) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_with_other_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"real(lemon=x) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_integer_declaration(parse: Parser, test_list: CheckFunctionDict):
    code = b"integer :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_derived_type_declaration(parse: Parser, test_list: CheckFunctionDict):
    code = b"type(z) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0
