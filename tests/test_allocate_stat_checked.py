# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter import tests
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code


@pytest.fixture
def test_list():
    return {"call_expression": [tests.test_allocate_has_stat]}


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


def test_allocate_stat_correct(parser, test_list):
    code = b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) STOP 'err'
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


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
