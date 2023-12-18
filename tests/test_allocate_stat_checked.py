# pylint: disable=W0621,C0116,C0114
from unittest import mock

import pytest

from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_allocate_has_stat
from tests.conftest import CodeWrapper, Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"call_expression": [check_allocate_has_stat]}


def test_wrong_node():
    mock_node = mock.Mock(**{"is_type.return_value": False})
    err_log = mock.MagicMock()
    with pytest.raises(WrongNodeError):
        check_allocate_has_stat(mock_node, err_log)


def test_allocate_stat_correct(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_wrong_way(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=u) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_if_but_not_checked(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=z) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_correct_mixed_caps(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (U/=0) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_mixed_caps2(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=U)
    if (u/=0) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_comment(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    ! comment
    if (u/=0) call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_no_stat(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z))
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked_with_line_after(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    x = 5
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


@pytest.mark.skip()
def test_allocate_stat_wrong_function_called(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call trace_exit()
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_abort_correct(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("stat_checked_var", "x")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


@pytest.mark.skip()
def test_allocate_abort_wrong_var_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("wrong_var", "x")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


@pytest.mark.skip()
def test_allocate_abort_wrong_sub_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("stat_checked_var", "wrong_sub_name")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


@pytest.mark.skip()
def test_allocate_abort_wrong_var_and_sub(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("wrong", "wrong_sub_name")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2
