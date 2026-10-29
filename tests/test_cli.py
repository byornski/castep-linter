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
from typing import List

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


def run_linter(args: List[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
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
def source_files(tmp_path: pathlib.Path) -> List[pathlib.Path]:
    """Several files with errors so that results come back from more than one worker"""
    files = []
    for i in range(4):
        file = tmp_path / f"bad_{i}.f90"
        file.write_bytes(BAD_CODE)
        files.append(file)
    return files


@pytest.mark.parametrize("parallel", [1, 4])
def test_cli_reports_errors(tmp_path: pathlib.Path, source_files: List[pathlib.Path], parallel):
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


def test_cli_writes_reports(tmp_path: pathlib.Path, source_files: List[pathlib.Path]):
    xml_file = tmp_path / "report.xml"
    json_file = tmp_path / "report.json"
    codeclimate_file = tmp_path / "codeclimate.json"

    args = ["-q", "-p", "4", "-x", str(xml_file), "-j", str(json_file), "-c", str(codeclimate_file)]
    result = run_linter([*args, *map(str, source_files)], tmp_path)

    assert result.returncode == 1, result.stderr
    assert xml_file.read_text().strip()
    assert json.loads(json_file.read_text())["issues"]
    assert json.loads(codeclimate_file.read_text())
