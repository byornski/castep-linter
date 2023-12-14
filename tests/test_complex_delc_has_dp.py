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


def test_complex_dp_correct(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex(kind=dp) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_complex_dp_no_kind(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex, intent(in) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_integer_kind_with_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex(kind=8) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_integer_kind_without_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex(8) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_bad_var_kind_without_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex(x) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_complex_bad_var_kind_with_keyword(parse: Parser, test_list: CheckFunctionDict):
    code = b"complex(kind=x) :: y"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1
