# pylint: disable=W0621,C0116,C0114
from unittest import mock

import pytest

from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import (
    CheckFunction,
    CheckFunctionDict,
    check_allocate_abort,
    check_allocate_has_stat,
)
from tests.conftest import CodeWrapper, Parser

ALLOCATE_CHECKS: list[CheckFunction] = [check_allocate_has_stat, check_allocate_abort]


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"allocate_statement": ALLOCATE_CHECKS}


def test_wrong_node():
    mock_node = mock.Mock(**{"is_type.return_value": False})
    err_log = mock.MagicMock()
    with pytest.raises(WrongNodeError):
        check_allocate_has_stat(mock_node, err_log)


def test_allocate_stat_correct(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_wrong_way(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=u) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_stat_correct_if_but_not_checked(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (0/=z) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


@pytest.mark.parametrize(
    "condition", [b"u /= 0 .and. on_root", b"on_root .and. u /= 0", b"(u /= 0) .or. failed"]
)
def test_allocate_stat_compound_condition_not_allowed(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict, condition
):
    # The stat must be checked on its own, not as part of a larger condition
    code = subroutine_wrapper(
        b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if ("""
        + condition
        + b""") call io_abort("bleh")
    """
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [e.message for e in error_log.errors] == ["Allocate status not checked"]


def test_allocate_stat_correct_mixed_caps(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (U/=0) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_mixed_caps2(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=U)
    if (u/=0) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_allocate_stat_correct_comment(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    ! comment
    if (u/=0) call io_abort("bleh")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_no_stat(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z))
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_not_checked_with_line_after(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    x = 5
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_stat_wrong_function_called(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call trace_exit()
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_abort_correct(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("stat_checked_var", "x")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_allocate_abort_wrong_var_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("wrong_var", "x")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_abort_wrong_sub_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("stat_checked_var", "wrong_sub_name")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_allocate_abort_wrong_var_and_sub(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    allocate(stat_checked_var(x,y,z), stat=u)
    if (u/=0) call io_allocate_abort("wrong", "wrong_sub_name")
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def abort_messages(parse: Parser, code: bytes) -> list[str]:
    error_log = run_tests_on_code(parse(code), {"allocate_statement": [check_allocate_abort]}, "f")
    return [e.message for e in error_log.errors]


@pytest.mark.parametrize(
    "handler",
    [
        b'if (u/=0) call io_abort("failed")',
        b'if (u/=0) call io_allocate_abort("arr", "x")',
        b'if (u/=0) call err_abort("failed")',
        b'if (u/=0) then\nwrite(*,*) "failed"\ncall err_abort("failed")\nend if',
        b'if (u/=0) call err_assert(.false., "failed")',
    ],
    ids=[
        "io_abort",
        "io_allocate_abort",
        "err_abort",
        "err_abort in block if",
        "err_assert",
    ],
)
def test_allocate_failure_stops_program(parse: Parser, subroutine_wrapper: CodeWrapper, handler):
    code = subroutine_wrapper(b"allocate(arr(n), stat=u)\n" + handler)
    assert abort_messages(parse, code) == []


@pytest.mark.parametrize(
    "handler",
    [
        b'if (u/=0) call trace_log_error("failed", u)',
        b'if (u/=0) call memory_allocate_abort("arr", 8, "failed")',
        b"if (u/=0) call comms_abort()",
        b"if (u/=0) then\nstatus = u\nreturn\nend if",
        b"if (u/=0) stop",
        b'if (u/=0) then\nwrite(*,*) "failed"\nerror stop 1\nend if',
    ],
    ids=[
        "other routine",
        "other abort routine",
        "comms_abort",
        "return status",
        "stop",
        "error stop",
    ],
)
def test_allocate_failure_not_reported(parse: Parser, subroutine_wrapper: CodeWrapper, handler):
    code = subroutine_wrapper(b"allocate(arr(n), stat=u)\n" + handler)
    assert abort_messages(parse, code) == ["Allocation failure does not raise an error"]


@pytest.mark.parametrize(
    ("allocate", "array", "errors"),
    [
        (b"allocate(a(n), b(n), stat=u)", b"b", []),
        (b"allocate(obj%arr(n), stat=u)", b"obj%arr", []),
        (b"allocate(obj%arr(n), stat=u)", b"OBJ % Arr", []),
        (
            b"allocate(obj%arr(n), stat=u)",
            b"arr",
            ["Wrong array name used in io_allocate_abort. Expected: obj%arr"],
        ),
        (
            b"allocate(a(n), b(n), stat=u)",
            b"c",
            ["Wrong array name used in io_allocate_abort. Expected: a or b"],
        ),
        (b"allocate(param_type :: obj%param, stat=u)", b"obj%param", []),
        (
            b"allocate(param_type :: obj%param, stat=u)",
            b"param_type",
            ["Wrong array name used in io_allocate_abort. Expected: obj%param"],
        ),
    ],
    ids=[
        "second of two",
        "component",
        "case and spaces",
        "component only",
        "neither of two",
        "typed",
        "type name",
    ],
)
def test_allocate_abort_array_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, allocate, array, errors
):
    code = subroutine_wrapper(
        allocate + b'\nif (u/=0) call io_allocate_abort("' + array + b'", "x")'
    )
    assert abort_messages(parse, code) == errors


def test_allocate_abort_names_in_variables_not_checked(
    parse: Parser, subroutine_wrapper: CodeWrapper
):
    code = subroutine_wrapper(b"""
    allocate(arr(n), stat=u)
    if (u/=0) call io_allocate_abort(array_name, routine_name)
    """)
    assert abort_messages(parse, code) == []


@pytest.mark.parametrize(
    ("routine", "errors"),
    [
        (b"tool", []),
        (b"x", ["Wrong subroutine name used in io_allocate_abort. Expected: tool"]),
    ],
)
def test_allocate_abort_in_program(parse: Parser, routine, errors):
    code = (
        b"""program tool
    allocate(arr(n), stat=u)
    if (u/=0) call io_allocate_abort("arr", \""""
        + routine
        + b"""\")
    end program tool"""
    )
    assert abort_messages(parse, code) == errors


@pytest.mark.parametrize(
    ("disabled", "remaining"),
    [
        ("alloc_abort", ["Allocate status not checked"]),
        ("alloc", ["Wrong subroutine name used in io_allocate_abort. Expected: x"]),
    ],
)
def test_allocate_checks_disabled_separately(
    parse: Parser, subroutine_wrapper: CodeWrapper, disabled, remaining
):
    code = subroutine_wrapper(f"""
    ! castep-lint: disable={disabled}
    allocate(a(n), stat=u)
    if (u/=0) call io_allocate_abort("a", "wrong")
    allocate(b(n), stat=v)
    """.encode())
    error_log = run_tests_on_code(parse(code), {"allocate_statement": ALLOCATE_CHECKS}, "f")
    assert [e.message for e in error_log.errors] == remaining


def by_variable(kind: str, variable: str, value: str, expected: str) -> str:
    return (
        f"Wrong {kind} name used in io_allocate_abort "
        f'by variable {variable}="{value}". Expected: {expected}'
    )


@pytest.mark.parametrize(
    ("declaration", "abort", "errors"),
    [
        (b"character(len=*), parameter :: subname = 'x'", b"'arr', subname", []),
        (
            b"character(len=*), parameter :: subname = 'wrong'",
            b"'arr', subname",
            [by_variable("subroutine", "subname", "wrong", "x")],
        ),
        (
            b"character(len=30) :: routinename = 'wrong'",
            b"'arr', routinename",
            [by_variable("subroutine", "routinename", "wrong", "x")],
        ),
        (b"character(len=*), parameter :: arr_name = 'arr'", b"arr_name, 'x'", []),
        (
            b"character(len=*), parameter :: arr_name = 'other'",
            b"arr_name, 'x'",
            [by_variable("array", "arr_name", "other", "arr")],
        ),
        (b"character(len=30) :: subname", b"'arr', subname", []),
    ],
    ids=[
        "parameter",
        "wrong parameter",
        "wrong initialised variable",
        "array parameter",
        "wrong array parameter",
        "variable without a value",
    ],
)
def test_allocate_abort_names_in_variables(
    parse: Parser, subroutine_wrapper: CodeWrapper, declaration, abort, errors
):
    code = subroutine_wrapper(
        declaration
        + b"\nallocate(arr(n), stat=u)\nif (u/=0) call io_allocate_abort("
        + abort
        + b")"
    )
    assert abort_messages(parse, code) == errors


def test_allocate_abort_name_in_dummy_argument_not_checked(parse: Parser):
    code = b"""module foo
    contains
    subroutine x(subname)
    character(len=*), intent(in) :: subname
    allocate(arr(n), stat=u)
    if (u/=0) call io_allocate_abort("arr", subname)
    end subroutine x
    end module foo"""
    assert abort_messages(parse, code) == []


@pytest.mark.parametrize(
    ("value", "errors"),
    [(b"tool", []), (b"x", [by_variable("subroutine", "progname", "x", "tool")])],
)
def test_allocate_abort_name_in_program_parameter(parse: Parser, value, errors):
    code = (
        b"""program tool
    character(len=*), parameter :: progname = '"""
        + value
        + b"""'
    allocate(arr(n), stat=u)
    if (u/=0) call io_allocate_abort("arr", progname)
    end program tool"""
    )
    assert abort_messages(parse, code) == errors


def test_allocate_err_assert_does_not_check_stat(parse: Parser, subroutine_wrapper: CodeWrapper):
    # err_assert only counts inside an if which checks the stat, like other error routines
    code = subroutine_wrapper(b'allocate(arr(n), stat=u)\ncall err_assert(u == 0, "failed")')
    error_log = run_tests_on_code(parse(code), {"allocate_statement": ALLOCATE_CHECKS}, "f")
    assert [e.message for e in error_log.errors] == ["Allocate status not checked"]
