# pylint: disable=W0621,C0116,C0114
import pytest

from castep_linter.error_logging.error_types import FortranError
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import CheckFunctionDict, check_trace_entry_exit
from tests.conftest import CodeWrapper, Parser


@pytest.fixture
def test_list() -> CheckFunctionDict:
    return {"subroutine": [check_trace_entry_exit], "function": [check_trace_entry_exit]}


def test_trace_entry_exit_correct(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("x", stat)
    call trace_exit("x", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors


def test_trace_entry_exit_correct_extra(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("x", stat)
    call bleh()
    call trace_exit("x", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_keyword(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry(string="x", status=stat)
    call trace_exit(string="x", status=stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    character(len=100), parameter :: sub_name = "x"
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param_extra(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    character(len=100), parameter :: sub_name = "x"
    character(len=100), parameter :: bleh = othervar
    integer :: p
    type(myvar) :: z
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_missing(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""call trace_exit("x", stat)""")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_trace_exit_missing(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""call trace_entry("x", stat)""")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 1


def test_trace_entry_exit_missing(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("y", stat)
    call trace_exit("y", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name_keyword(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry(string="y", status=stat)
    call trace_exit(string="y", status=stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name_by_param(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    character(len=100), parameter :: sub_name = "y"
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_wrong_name_exception(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("castep", stat)
    call trace_exit("castep", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_wrong_name_by_param_exception(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    character(len=100), parameter :: sub_name = "castep"
    call trace_entry(sub_name, stat)
    call trace_exit(sub_name, stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_no_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry()
    call trace_exit()
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [e.message for e in error_log.errors] == ["No name passed to trace in x"] * 2


@pytest.mark.parametrize(
    "calls",
    [
        b"call trace_entry\ncall trace_exit\n",
        b"call trace_entry(status=stat)\ncall trace_exit(status=stat)\n",
    ],
)
def test_trace_entry_exit_no_name_other_forms(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict, calls
):
    error_log = run_tests_on_code(parse(subroutine_wrapper(calls)), test_list, "filename")
    assert [e.message for e in error_log.errors] == ["No name passed to trace in x"] * 2


def test_trace_entry_exit_call_without_brackets(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("x", stat)
    call flush
    call trace_exit("x", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_unknown_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry(other_var)
    call trace_exit(other_var)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


@pytest.mark.parametrize("name", [b"names(1)", b'"x"//"y"', b"obj%name", b"trim(sub)", b'("x")'])
def test_trace_entry_exit_unrecognised_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict, name
):
    code = subroutine_wrapper(
        b"call trace_entry(" + name + b", stat)\ncall trace_exit(" + name + b", stat)\n"
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [(type(e), e.message) for e in error_log.errors] == [
        (FortranError, "Unrecognised name passed to trace in x"),
        (FortranError, "Unrecognised name passed to trace in x"),
    ]


def test_trace_entry_exit_correct_caps(parse: Parser, test_list: CheckFunctionDict):
    code = b"""
    module foo
    SUBROUTINE X(Y)
    CALL TRACE_ENTRY("X", STAT)
    CALL TRACE_EXIT("X", STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0, error_log.errors[0].message


def test_trace_entry_exit_correct_by_param_mixed_caps(parse: Parser, test_list: CheckFunctionDict):
    code = b"""
    module foo
    SUBROUTINE X(Y)
    CHARACTER(len=100), PARAMETER :: sub_name = "X"
    CALL TRACE_ENTRY(SUB_NAME, STAT)
    CALL TRACE_EXIT(SUB_NAME, STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_by_param_all_caps(parse: Parser, test_list: CheckFunctionDict):
    code = b"""
    module foo
    SUBROUTINE X(Y)
    CHARACTER(len=100), PARAMETER :: SUB_NAME = "X"
    CALL TRACE_ENTRY(SUB_NAME, STAT)
    CALL TRACE_EXIT(SUB_NAME, STAT)
    END SUBROUTINE X
    end module foo
    """
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_correct_function(
    parse: Parser, function_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = function_wrapper(b"""
        CALL TRACE_ENTRY("x", STAT)
        CALL TRACE_EXIT("x", STAT)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_missing_function(
    parse: Parser, function_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = function_wrapper(b"")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 2


def test_trace_entry_exit_non_utf8_parameter(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    # Some source files contain Latin-1 text, which must not stop the trace names being checked
    code = subroutine_wrapper(b"""
    character(len=*), parameter :: author = "M\xf6ller"
    call trace_entry("x", stat)
    call trace_exit("x", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


def test_trace_entry_exit_non_utf8_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    code = subroutine_wrapper(b"""
    call trace_entry("x\xf6", stat)
    call trace_exit("x", stat)
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [e.message for e in error_log.errors] == ["Incorrect name passed to trace in x"]


@pytest.mark.parametrize("interface", [b"interface", b"abstract interface"])
def test_trace_not_required_in_interface(parse: Parser, test_list: CheckFunctionDict, interface):
    # Routines declared in an interface block have no body to call trace from
    code = (
        b"""module foo
    """
        + interface
        + b"""
      subroutine declared(a)
        integer :: a
      end subroutine declared
      function declared_fn(a)
        integer :: a, declared_fn
      end function declared_fn
    end interface
    end module foo"""
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) == 0


@pytest.mark.parametrize(
    "exit_call",
    [
        b'if (y) then\ncall trace_exit("x", stat)\nreturn\nend if\n',
        b'if (full_trace) call trace_exit("x", stat)\n',
        b'do i = 1, 2\ncall trace_exit("x", stat)\nend do\n',
        b'select case (y)\ncase (1)\ncall trace_exit("x", stat)\nend select\n',
        b'#ifdef MPI\ncall trace_exit("x", stat)\n#endif\n',
        b"if (y) then\ncall trace_exit(sub_name, stat)\nend if\n",
    ],
    ids=["block if", "one-line if", "do", "select case", "ifdef", "parameter"],
)
def test_trace_exit_inside_block(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict, exit_call
):
    code = subroutine_wrapper(
        b'character(len=*), parameter :: sub_name = "x"\ncall trace_entry("x", stat)\n' + exit_call
    )
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [e.message for e in error_log.errors] == []


def test_trace_section_timer_inside_block(
    parse: Parser, subroutine_wrapper: CodeWrapper, test_list: CheckFunctionDict
):
    # Trace calls with another name inside a block time a section, so are neither
    # checked nor counted as the routine's own
    code = subroutine_wrapper(b"""
    call trace_entry("x", stat)
    if (y) then
      call trace_entry("section", stat)
      call trace_exit("section", stat)
    end if
    """)
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert [e.message for e in error_log.errors] == ["Missing trace_exit in x"]


def test_trace_in_contained_routine_not_counted(parse: Parser, test_list: CheckFunctionDict):
    code = b"""module foo
    contains
    subroutine x()
    contains
      subroutine inner()
        call trace_entry("x", stat)
        call trace_exit("x", stat)
      end subroutine inner
    end subroutine x
    end module foo"""
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    messages = [e.message for e in error_log.errors]
    assert "Missing trace_entry in x" in messages
    assert "Missing trace_exit in x" in messages
