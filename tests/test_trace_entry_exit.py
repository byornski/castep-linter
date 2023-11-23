# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter import tests
from castep_linter.fortran.parser import get_fortran_parser
from castep_linter.scan_files import run_tests_on_code


@pytest.fixture
def test_list():
    return {"subroutine": [tests.test_trace_entry_exit], "function": [tests.test_trace_entry_exit]}


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


def test_trace_entry_exit_correct(parser, test_list):
    code = b"""
    call trace_entry("x", stat)
    call trace_exit("x", stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors


def test_trace_entry_exit_correct_extra(parser, test_list):
    code = b"""
    call trace_entry("x", stat)
    call bleh()
    call trace_exit("x", stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_keyword(parser, test_list):
    code = b"""
    call trace_entry(string="x", status=stat)
    call trace_exit(string="x", status=stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param(parser, test_list):
    code = b"""
    character(len=100), parameter :: sub_name = "x"
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param_extra(parser, test_list):
    code = b"""
    character(len=100), parameter :: sub_name = "x"
    character(len=100), parameter :: bleh = othervar
    integer :: p
    type(myvar) :: z
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_missing(parser, test_list):
    code = b"""
    call trace_exit("x", stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_trace_exit_missing(parser, test_list):
    code = b"""
    call trace_entry("x", stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 1


def test_trace_entry_exit_missing(parser, test_list):
    code = b""
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name(parser, test_list):
    code = b"""
    call trace_entry("y", stat)
    call trace_exit("y", stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name_keyword(parser, test_list):
    code = b"""
    call trace_entry(string="y", status=stat)
    call trace_exit(string="y", status=stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name_by_param(parser, test_list):
    code = b"""
    character(len=100), parameter :: sub_name = "y"
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_no_name(parser, test_list):
    code = b"""
    call trace_entry()
    call trace_exit()
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_unknown_name(parser, test_list):
    code = b"""
    call trace_entry(other_var)
    call trace_exit(other_var)
    """
    wrapped_code = subroutine_wrapper(code)
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_correct_caps(parser, test_list):
    wrapped_code = b"""
    module foo
    SUBROUTINE X(Y)
    CALL TRACE_ENTRY("X", STAT)
    CALL TRACE_EXIT("X", STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_trace_entry_exit_correct_by_param_mixed_caps(parser, test_list):
    wrapped_code = b"""
    module foo
    SUBROUTINE X(Y)
    CHARACTER(len=100), PARAMETER :: sub_name = "X"
    CALL TRACE_ENTRY(SUB_NAME, STAT)
    CALL TRACE_EXIT(SUB_NAME, STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param_all_caps(parser, test_list):
    wrapped_code = b"""
    module foo
    SUBROUTINE X(Y)
    CHARACTER(len=100), PARAMETER :: SUB_NAME = "X"
    CALL TRACE_ENTRY(SUB_NAME, STAT)
    CALL TRACE_EXIT(SUB_NAME, STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_function(parser, test_list):
    wrapped_code = b"""
    module foo
    function X(Y)
    CALL TRACE_ENTRY("x", STAT)
    CALL TRACE_EXIT("x", STAT)
    end function X
    end module foo
    """
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_missing_function(parser, test_list):
    wrapped_code = b"""
    module foo
    function X(Y)
    end function X
    end module foo
    """
    error_log = run_tests_on_code(parser, wrapped_code, test_list, "filename")
    assert len(error_log.errors) == 2
