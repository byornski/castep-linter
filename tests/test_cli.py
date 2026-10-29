# pylint: disable=W0621,C0116,C0114
"""
End to end tests of the castep-lint command line, which scans files using a multiprocessing pool.

These run the linter in a subprocess with a timeout, as a result that cannot be passed back from
a worker makes the pool hang rather than fail.
"""

import json
import os
import pathlib
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

TIMEOUT = 60

GOOD_CODE = b"""module foo
contains
  subroutine x()
    call trace_entry("x", stat)
    call trace_exit("x", stat)
  end subroutine x
end module foo
"""

BAD_CODE = b"""module foo
contains
  subroutine x()
    real :: y
    y = 1.0
  end subroutine x
end module foo
"""


def run_linter(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-c", "from castep_linter.scan_files import main; main()", *args]
    # Run in a new session so a hung linter can be killed along with its pool workers
    with subprocess.Popen(  # noqa: S603
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            pytest.fail(f"castep-lint did not finish within {TIMEOUT}s: {' '.join(args)}")
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


@pytest.fixture
def source_files(tmp_path: pathlib.Path) -> list[pathlib.Path]:
    """Several files with errors so that results come back from more than one worker"""
    files = []
    for i in range(4):
        file = tmp_path / f"bad_{i}.f90"
        file.write_bytes(BAD_CODE)
        files.append(file)
    return files


@pytest.mark.parametrize("parallel", [1, 4])
def test_cli_reports_errors(tmp_path: pathlib.Path, source_files: list[pathlib.Path], parallel):
    result = run_linter(["-p", str(parallel), *map(str, source_files)], tmp_path)

    assert result.returncode == 1, result.stderr
    for file in source_files:
        assert f"issues in {file}" in result.stdout


@pytest.mark.parametrize("parallel", [1, 4])
def test_cli_clean_file(tmp_path: pathlib.Path, parallel):
    file = tmp_path / "good.f90"
    file.write_bytes(GOOD_CODE)

    result = run_linter(["-p", str(parallel), str(file)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert f"0 issues in {file}" in result.stdout


def test_cli_writes_reports(tmp_path: pathlib.Path, source_files: list[pathlib.Path]):
    xml_file = tmp_path / "report.xml"
    json_file = tmp_path / "report.json"
    codeclimate_file = tmp_path / "codeclimate.json"

    args = ["-q", "-p", "4", "-x", str(xml_file), "-j", str(json_file), "-c", str(codeclimate_file)]
    result = run_linter([*args, *map(str, source_files)], tmp_path)

    assert result.returncode == 1, result.stderr
    assert xml_file.read_text().strip()
    assert json.loads(json_file.read_text())["issues"]
    assert json.loads(codeclimate_file.read_text())


def test_cli_codeclimate_fingerprints_stable(
    tmp_path: pathlib.Path, source_files: list[pathlib.Path]
):
    # Each run is a new Python process, so this would catch use of the randomised hash()
    fingerprints = []
    for run in range(2):
        report = tmp_path / f"codeclimate_{run}.json"
        run_linter(["-q", "-c", str(report), *map(str, source_files)], tmp_path)
        fingerprints.append([i["fingerprint"] for i in json.loads(report.read_text())])

    assert fingerprints[0] == fingerprints[1]
    assert len(set(fingerprints[0])) == len(fingerprints[0])


# One finding of each severity: Info for the missing trace calls (line 3), an Error for the
# declaration (line 4) and a Warning for the allocate (line 5)
LEVELS_CODE = b"""module foo
contains
subroutine x()
  real :: a
  allocate(b(10))
end subroutine x
end module foo
"""

INFO_ONLY_CODE = b"""module foo
contains
subroutine x()
end subroutine x
end module foo
"""

WARNING_ONLY_CODE = b"""module foo
contains
subroutine x()
  call trace_entry("x", stat)
  allocate(b(10))
  call trace_exit("x", stat)
end subroutine x
end module foo
"""


@pytest.fixture
def cli_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Directory holding a file for each mix of severities, named by its contents"""
    for name, code in [
        ("levels.f90", LEVELS_CODE),
        ("info_only.f90", INFO_ONLY_CODE),
        ("warning_only.f90", WARNING_ONLY_CODE),
        ("clean.f90", GOOD_CODE),
    ]:
        (tmp_path / name).write_bytes(code)
    return tmp_path


def test_cli_annotated_output(cli_dir: pathlib.Path):
    result = run_linter(["levels.f90"], cli_dir)

    lines = result.stdout.splitlines()
    assert "Error: No kind specifier" in lines
    # The source line, with the finding underlined
    line_index = next(i for i, line in enumerate(lines) if line.endswith(">  real :: a"))
    assert lines[line_index + 1].strip() == "^^^^^^^^^"
    assert lines[-1] == "4 issues in levels.f90 (1 errors, 1 warnings, 2 info)"


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (
            "Info",
            [
                "levels.f90:3:1: Info: Missing trace_entry in x",
                "levels.f90:3:1: Info: Missing trace_exit in x",
                "levels.f90:4:3: Error: No kind specifier",
                "levels.f90:5:3: Warning: No stat on allocate statement",
            ],
        ),
        (
            "Warn",
            [
                "levels.f90:4:3: Error: No kind specifier",
                "levels.f90:5:3: Warning: No stat on allocate statement",
            ],
        ),
        ("Error", ["levels.f90:4:3: Error: No kind specifier"]),
    ],
)
def test_cli_level_filters_output(cli_dir: pathlib.Path, level, expected):
    result = run_linter(["-l", level, "-f", "GCC", "levels.f90"], cli_dir)

    # Findings below the level are not printed, but are still counted in the summary
    assert result.stdout.splitlines() == [
        *expected,
        "4 issues in levels.f90 (1 errors, 1 warnings, 2 info)",
    ]


def test_cli_format_case_insensitive(cli_dir: pathlib.Path):
    upper = run_linter(["-f", "GCC", "levels.f90"], cli_dir)
    lower = run_linter(["-f", "gcc", "levels.f90"], cli_dir)
    assert lower.stdout == upper.stdout


@pytest.mark.parametrize(
    ("file", "level", "exit_code"),
    [
        ("clean.f90", "Info", 0),
        ("info_only.f90", "Info", 1),
        ("info_only.f90", "Warn", 0),
        ("warning_only.f90", "Warn", 1),
        ("warning_only.f90", "Error", 0),
        ("levels.f90", "Error", 1),
    ],
)
def test_cli_exit_code_follows_level(cli_dir: pathlib.Path, file, level, exit_code):
    # Fails only if there is a finding at or above the level
    result = run_linter(["-q", "-l", level, file], cli_dir)
    assert result.returncode == exit_code, result.stderr


def test_cli_reports_follow_level(cli_dir: pathlib.Path):
    args = ["-q", "-l", "Error", "-x", "report.xml", "-j", "jenkins.json", "-c", "codeclimate.json"]
    run_linter([*args, "levels.f90"], cli_dir)

    jenkins = json.loads((cli_dir / "jenkins.json").read_text())["issues"]
    assert [i["message"] for i in jenkins] == ["No kind specifier"]
    codeclimate = json.loads((cli_dir / "codeclimate.json").read_text())
    assert [i["description"] for i in codeclimate] == ["No kind specifier"]

    # JUnit XML keeps findings below the level, but marks them as skipped
    # The report was just written by the linter, so is trusted
    testcases = ET.parse(cli_dir / "report.xml").getroot().iter("testcase")  # noqa: S314
    results = {case.get("name"): [child.tag for child in case] for case in testcases}
    assert results == {
        "Info: Missing trace_entry in x": ["skipped"],
        "Info: Missing trace_exit in x": ["skipped"],
        "Error: No kind specifier": ["error"],
        "Warning: No stat on allocate statement": ["skipped"],
    }


def test_cli_quiet(cli_dir: pathlib.Path):
    result = run_linter(["-q", "levels.f90"], cli_dir)
    assert result.stdout == ""
    assert result.returncode == 1


def test_cli_print_tree(cli_dir: pathlib.Path):
    result = run_linter(["-q", "--print-tree", "clean.f90"], cli_dir)
    tree = [line.strip(" │├") for line in result.stdout.splitlines()]
    assert tree[0] == "translation_unit"
    assert "subroutine_call" in tree
    assert result.returncode == 0


def test_cli_debug(cli_dir: pathlib.Path):
    result = run_linter(["-q", "-d", "clean.f90"], cli_dir)
    assert result.returncode == 0, result.stderr


def test_cli_missing_file(cli_dir: pathlib.Path):
    result = run_linter(["missing.f90"], cli_dir)
    assert result.returncode == 2
    assert "The file missing.f90 does not exist!" in result.stderr


@pytest.mark.parametrize("args", [["-l", "Bogus"], ["-f", "bogus"], ["-p", "two"]])
def test_cli_invalid_option(cli_dir: pathlib.Path, args):
    result = run_linter([*args, "clean.f90"], cli_dir)
    assert result.returncode == 2
    assert "usage: castep-linter" in result.stderr
