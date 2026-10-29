# pylint: disable=W0621,C0116,C0114
import io
import json
import pathlib
import pickle

from rich.console import Console

from castep_linter.error_logging.error_types import PrintStyle
from castep_linter.error_logging.json_writer import write_codeclimate, write_jenkins
from castep_linter.scan_files import run_tests_on_code
from castep_linter.tests import test_list
from tests.conftest import CodeWrapper, Parser


def test_error_log_survives_pickling(parse: Parser, subroutine_wrapper: CodeWrapper):
    # Error logs are passed back from multiprocessing workers, so must round trip through pickle
    code = subroutine_wrapper(b"real :: x")
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    assert len(error_log.errors) > 0

    restored = pickle.loads(pickle.dumps(error_log))  # noqa: S301

    assert [(e.message, e.start_point, e.end_point) for e in restored.errors] == [
        (e.message, e.start_point, e.end_point) for e in error_log.errors
    ]


def test_gcc_format_is_one_indexed(parse: Parser):
    # GCC style diagnostics number both lines and columns from 1
    code = b"module foo\ncontains\nsubroutine x(y)\n  real :: z\nend subroutine x\nend module foo\n"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    (error,) = [e for e in error_log.errors if e.message == "No kind specifier"]

    output = io.StringIO()
    error.print_err("file.f90", Console(file=output, width=200), print_style=PrintStyle.GCC)

    assert output.getvalue().strip() == "file.f90:4:3: Error: No kind specifier"


def test_report_line_numbers_are_one_indexed(parse: Parser, tmp_path: pathlib.Path):
    # The declaration is on line 4 of the file
    code = b"module foo\ncontains\nsubroutine x(y)\n  real :: z\nend subroutine x\nend module foo\n"
    error_log = run_tests_on_code(parse(code), test_list, "filename")
    error_log.errors = [e for e in error_log.errors if e.message == "No kind specifier"]

    codeclimate_file = tmp_path / "codeclimate.json"
    write_codeclimate(codeclimate_file, {"file.f90": error_log}, 0)
    jenkins_file = tmp_path / "jenkins.json"
    write_jenkins(jenkins_file, {"file.f90": error_log}, 0)

    (codeclimate,) = json.loads(codeclimate_file.read_text())
    (jenkins,) = json.loads(jenkins_file.read_text())["issues"]
    assert codeclimate["location"]["lines"]["begin"] == 4
    assert jenkins["lineStart"] == 4


def codeclimate_fingerprints(parse: Parser, tmp_path: pathlib.Path, code: bytes) -> list:
    source = tmp_path / "file.f90"
    source.write_bytes(code)
    error_log = run_tests_on_code(parse(code), test_list, str(source))

    report = tmp_path / "codeclimate.json"
    write_codeclimate(report, {str(source): error_log}, 0)
    return [(i["description"], i["fingerprint"]) for i in json.loads(report.read_text())]


ROUTINE = b"""module foo
contains
subroutine x()
%s
  real :: a
  real :: a
  real :: b
end subroutine x
end module foo
"""


def test_fingerprints_unique(parse: Parser, tmp_path: pathlib.Path):
    issues = codeclimate_fingerprints(parse, tmp_path, ROUTINE % b"")
    assert len(issues) == 5
    assert len({fingerprint for _, fingerprint in issues}) == 5


def test_fingerprints_unchanged_by_moving_lines(parse: Parser, tmp_path: pathlib.Path):
    before = codeclimate_fingerprints(parse, tmp_path, ROUTINE % b"")
    after = codeclimate_fingerprints(parse, tmp_path, ROUTINE % b"  ! A new comment\n\n")
    assert before == after


def test_fingerprints_change_with_flagged_line(parse: Parser, tmp_path: pathlib.Path):
    before = codeclimate_fingerprints(parse, tmp_path, ROUTINE % b"")
    after = codeclimate_fingerprints(parse, tmp_path, (ROUTINE % b"").replace(b"b\n", b"c\n"))
    changed = [desc for (desc, old), (_, new) in zip(before, after, strict=True) if old != new]
    assert changed == ["No kind specifier"]
