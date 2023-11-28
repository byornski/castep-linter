# pylint: disable=W0621,C0116,C0114
from unittest import mock

import pytest

from castep_linter import tests
from castep_linter.fortran.fortran_node import WrongNodeError
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests.real_declaration_has_dp import check_real_dp_declaration


@pytest.fixture
def test_list():
    return {"variable_declaration": [tests.check_real_dp_declaration]}


@pytest.fixture
def parser():
    return get_fortran_parser()


def test_wrong_node():
    mock_node = mock.Mock(**{"is_type.return_value": False})
    err_log = mock.MagicMock()
    with pytest.raises(WrongNodeError):
        check_real_dp_declaration(mock_node, err_log)


def test_real_dp_correct(parser, test_list):
    code = b"real(kind=dp) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_version_kind_correct(parser, test_list):
    code = b"real(kind=version_kind) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


@pytest.mark.skip(reason="Not current implemented")
def test_real_dp_correctb(parser, test_list):
    code = b"real, kind(dp) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_dp_by_position(parser, test_list):
    code = b"real(dp) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_dp_by_d0(parser, test_list):
    code = b"DOUBLE PRECISION :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_real_dp_no_kind(parser, test_list):
    code = b"real, intent(in) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_integer_kind_with_keyword(parser, test_list):
    code = b"real(kind=8) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_integer_kind_without_keyword(parser, test_list):
    code = b"real(8) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_bad_var_kind_without_keyword(parser, test_list):
    code = b"real(x) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_bad_var_kind_with_keyword(parser, test_list):
    code = b"real(kind=x) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_real_with_other_keyword(parser, test_list):
    code = b"real(lemon=x) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_integer_declaration(parser, test_list):
    code = b"integer :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_derived_type_declaration(parser, test_list):
    code = b"type(z) :: y"
    error_log = run_tests_on_code(parser, code, test_list, "filename")
    assert len(error_log.errors) == 0
