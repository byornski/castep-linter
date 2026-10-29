# pylint: disable=W0621,C0116,C0114
import json
import pathlib
from typing import List

from castep_linter.error_logging.json_writer import write_codeclimate
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import test_list
from tests.conftest import CodeWrapper, Parser

TRACE = b"""
    call trace_entry("x", stat)
    call trace_exit("x", stat)
"""


def messages(parse: Parser, code: bytes) -> List[str]:
    return [e.message for e in run_tests_on_code(parse(code), test_list, "filename").errors]


def test_no_directive_reports(parse: Parser, subroutine_wrapper: CodeWrapper):
    assert messages(parse, subroutine_wrapper(b"")) == [
        "Missing trace_entry in x",
        "Missing trace_exit in x",
    ]


def test_disable_trace_in_subroutine(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=trace\n")
    assert messages(parse, code) == []


def test_disable_trace_in_function(parse: Parser, function_wrapper: CodeWrapper):
    code = function_wrapper(b"! castep-lint: disable=trace\n")
    assert messages(parse, code) == []


def test_disable_trace_on_subroutine_line(parse: Parser):
    code = b"""module foo
    contains
    subroutine x(y)  ! castep-lint: disable=trace
    end subroutine x
    end module foo"""
    assert messages(parse, code) == []


def test_disable_only_named_check(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=trace\nreal :: z\n")
    assert messages(parse, code) == ["No kind specifier"]


def test_disable_multiple_case_insensitive(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=TRACE, kind\nreal :: z\n")
    assert messages(parse, code) == []


def test_disable_does_not_affect_other_routines(parse: Parser):
    code = b"""module foo
    contains
    subroutine x()
      ! castep-lint: disable=trace
    contains
      subroutine inner()
      end subroutine inner
    end subroutine x
    subroutine sibling()
    end subroutine sibling
    end module foo"""
    assert messages(parse, code) == [
        "Missing trace_entry in inner",
        "Missing trace_exit in inner",
        "Missing trace_entry in sibling",
        "Missing trace_exit in sibling",
    ]


def test_disable_statement(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(TRACE + b"""
    z = 1.0  ! castep-lint: disable=literal_kind
    z = 1.0
    """)
    assert messages(parse, code) == ["Float literal without kind"]


def test_disable_continued_statement_from_last_line(parse: Parser, subroutine_wrapper: CodeWrapper):
    # "No stat on allocate statement" is reported on the first line of the statement
    code = subroutine_wrapper(TRACE + b"""
    allocate(p(n), &
       q(n))  ! castep-lint: disable=alloc
    allocate(r(n))
    """)
    assert messages(parse, code) == ["No stat on allocate statement"]


def test_disable_continued_statement_from_first_line(
    parse: Parser, subroutine_wrapper: CodeWrapper
):
    code = subroutine_wrapper(TRACE + b"""
    call g(a, &  ! castep-lint: disable=literal_kind
           1.0, &
! comment between continued lines
         & 2.0)
    z = 3.0
    """)
    assert messages(parse, code) == ["Float literal without kind"]


def test_disable_statement_in_if_block(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(TRACE + b"""
    if (y) then
      z = 1.0  ! castep-lint: disable=literal_kind
      z = 2.0
    end if
    """)
    assert messages(parse, code) == ["Float literal without kind"]


def test_ampersand_in_string_does_not_continue(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(TRACE + b"""
    call g("a&")  ! castep-lint: disable=literal_kind
    z = 1.0
    """)
    assert messages(parse, code) == ["Float literal without kind"]


def test_unknown_check_name(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=trace, bogus\n")
    assert messages(parse, code) == [
        (
            "Unknown check 'bogus' in castep-lint comment, "
            "expected one of ALLOC, CMPLX_KIND, KIND, LITERAL_KIND, TRACE"
        )
    ]


def test_directive_with_no_effect(parse: Parser):
    code = b"""module foo
    ! castep-lint: disable=trace
    contains
    subroutine x()
    end subroutine x
    end module foo"""
    assert messages(parse, code) == [
        "castep-lint comment has no effect here",
        "Missing trace_entry in x",
        "Missing trace_exit in x",
    ]


def test_malformed_directive(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint disable=trace\n")
    assert messages(parse, code) == [
        "Missing trace_entry in x",
        "Missing trace_exit in x",
        "Malformed castep-lint comment",
    ]


def test_trailing_comma_ignored(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=trace,\n")
    assert messages(parse, code) == []


def test_directive_naming_no_checks(parse: Parser, subroutine_wrapper: CodeWrapper):
    code = subroutine_wrapper(b"! castep-lint: disable=,\n")
    assert messages(parse, code) == [
        "Missing trace_entry in x",
        "Missing trace_exit in x",
        "castep-lint comment names no checks",
    ]


def test_continued_statement_at_end_of_file(parse: Parser):
    code = b"program p\nx = 1.0 + &\n    2.0  ! castep-lint: disable=literal_kind"
    assert messages(parse, code) == []


def test_continued_statement_at_start_of_file(parse: Parser):
    code = b"x = 1.0 + &  ! castep-lint: disable=literal_kind\n    2.0\nend"
    assert messages(parse, code) == []


def test_continuation_on_last_line_of_file(parse: Parser):
    # Not valid Fortran, but must not crash looking for the next line
    code = b"program p\nx = 1.0 + &  ! castep-lint: disable=literal_kind"
    assert messages(parse, code) == []


def test_routine_directive_does_not_affect_module(parse: Parser):
    code = b"""module foo
    real :: m = 1.0
    contains
    subroutine x()
    ! castep-lint: disable=literal_kind, trace
    y = 2.0
    end subroutine x
    end module foo"""
    assert messages(parse, code) == ["No kind specifier", "Float literal without kind"]


def test_codeclimate_uses_check_name(
    parse: Parser, subroutine_wrapper: CodeWrapper, tmp_path: pathlib.Path
):
    # determine_type alone cannot classify this message from its text
    code = subroutine_wrapper(b'call trace_entry(unknown_var, stat)\ncall trace_exit("x", stat)\n')
    error_log = run_tests_on_code(parse(code), test_list, "filename")

    out_file = tmp_path / "codeclimate.json"
    write_codeclimate(out_file, {"filename": error_log}, 0)

    issues = json.loads(out_file.read_text())
    assert [issue["check_name"] for issue in issues] == ["TRACE"]


def test_comment_not_utf8(parse: Parser, subroutine_wrapper: CodeWrapper):
    # Comments in some CASTEP files contain Latin-1 text, eg author names
    code = subroutine_wrapper(b"! Written by M\xf6ller\n! castep-lint: disable=trace\n")
    assert messages(parse, code) == []
