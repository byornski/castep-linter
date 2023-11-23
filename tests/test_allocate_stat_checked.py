# pylint: disable=W0621,C0116,C0114
from unittest import mock

import pytest

from castep_linter import tests
from castep_linter.fortran.fortran_node import WrongNodeError
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests.allocate_stat_checked import check_allocate_has_stat


@pytest.fixture
def test_list():
    return {"call_expression": [tests.check_allocate_has_stat]}


@pytest.fixture
def parser():
    return get_fortran_parser()


def subroutine_wrapper(code):
    return (
        b"""module foo
        subroutine x(y)
        """
        + code
        + b"""
        end subroutine x
        end module foo"""
    )


def test_wrong_node():
    mock_node = mock.Mock(**{"is_type.return_value": False})
    err_log = mock.MagicMock()
    with pytest.raises(WrongNodeError):
        check_allocate_has_stat(mock_node, err_log)


def test_allocate_stat_correct(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_wrong_way(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=u) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_if_but_not_checked(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=z) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_correct_mixed_caps(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (U/=0) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_mixed_caps2(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=U)
    if (u/=0) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_comment(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    ! comment
    if (u/=0) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_no_stat(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z))
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked_with_line_after(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    x = 5
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1
