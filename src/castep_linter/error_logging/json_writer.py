"""Module to write code linting errors in Jenkins json format"""

import hashlib
import json
from collections import Counter
from enum import Enum, auto
from pathlib import Path
from typing import Literal, TypedDict

from castep_linter.error_logging.error_types import FORTRAN_ERRORS
from castep_linter.error_logging.logger import ErrorLogger

# Reported for anything not found by a named check
UNKNOWN_CHECK = "UNKNOWN"

JenkinsSeverityLevel = Literal["LOW", "NORMAL", "HIGH", "ERROR"]
Jenkins_severity_dict: dict[int, JenkinsSeverityLevel] = {
    FORTRAN_ERRORS["Error"].ERROR_SEVERITY: "HIGH",
    FORTRAN_ERRORS["Warn"].ERROR_SEVERITY: "NORMAL",
    FORTRAN_ERRORS["Info"].ERROR_SEVERITY: "LOW",
}

CodeClimateSeverityLevel = Literal["info", "minor", "major", "critical", "blocker"]
CodeClimate_severity_dict: dict[int, CodeClimateSeverityLevel] = {
    FORTRAN_ERRORS["Error"].ERROR_SEVERITY: "critical",
    FORTRAN_ERRORS["Warn"].ERROR_SEVERITY: "minor",
    FORTRAN_ERRORS["Info"].ERROR_SEVERITY: "info",
}


class JenkinsIssue(TypedDict):
    """Represents a single issue in a Jenkins JSON report"""

    fileName: str
    severity: JenkinsSeverityLevel
    message: str
    type: str
    lineStart: int
    lineEnd: int
    columnStart: int
    columnEnd: int


class JenkinsReport(TypedDict):
    """Represents an entire report"""

    _class: str
    issues: list[JenkinsIssue]
    size: int


class Lines(TypedDict):
    begin: int


class CodeClimateLocation(TypedDict):
    path: str
    lines: Lines


class CodeClimateIssue(TypedDict):
    description: str
    check_name: str
    fingerprint: str
    severity: CodeClimateSeverityLevel
    location: CodeClimateLocation


class Formats(Enum):
    Jenkins = auto()
    CodeClimate = auto()


def write_jenkins(file: Path, error_logs: dict[str, ErrorLogger], error_level: int):
    """write code linting errors in Jenkins json format"""

    issues: list[JenkinsIssue] = [
        JenkinsIssue(
            fileName=scanned_file,
            severity=Jenkins_severity_dict[error.ERROR_SEVERITY],
            message=error.message,
            type=error.check or UNKNOWN_CHECK,
            lineStart=error.start_point[0] + 1,  # Jenkins lines 1-indexed
            lineEnd=error.end_point[0] + 1,
            columnStart=error.start_point[1] + 1,
            columnEnd=error.end_point[1] + 1,
        )
        for scanned_file, log in error_logs.items()
        for error in log.errors
        if error.ERROR_SEVERITY >= error_level
    ]

    report: JenkinsReport = {
        "_class": "io.jenkins.plugins.analysis.core.restapi.ReportApi",
        "issues": issues,
        "size": len(issues),
    }

    with open(file, "w", encoding="utf-8") as out_file:
        json.dump(report, out_file, indent=2)


def fingerprints(scanned_file: str, log: ErrorLogger) -> list[str]:
    """
    Fingerprints identifying each error between runs. They are built from the text of the line
    rather than its number, so they do not change when code above moves, and identical errors
    are numbered so that each has its own fingerprint.
    """
    try:
        lines = Path(scanned_file).read_bytes().splitlines()
    except OSError:
        lines = []

    occurrences: Counter[str] = Counter()
    result = []
    for error in log.errors:
        row = error.start_point[0]
        line = lines[row].decode(errors="replace").strip() if row < len(lines) else ""
        key = "\0".join([scanned_file, error.check or UNKNOWN_CHECK, error.message, line])
        result.append(hashlib.sha256(f"{key}\0{occurrences[key]}".encode()).hexdigest())
        occurrences[key] += 1
    return result


def write_codeclimate(file: Path, error_logs: dict[str, ErrorLogger], error_level: int) -> None:
    issues: list[CodeClimateIssue] = [
        CodeClimateIssue(
            check_name=error.check or UNKNOWN_CHECK,
            description=error.message,
            fingerprint=fingerprint,
            severity=CodeClimate_severity_dict[error.ERROR_SEVERITY],
            # CodeClimate lines 1-indexed
            location={"path": scanned_file, "lines": {"begin": error.start_point[0] + 1}},
        )
        for scanned_file, log in error_logs.items()
        for error, fingerprint in zip(log.errors, fingerprints(scanned_file, log), strict=True)
        if error.ERROR_SEVERITY >= error_level
    ]

    with open(file, "w", encoding="utf-8") as out_file:
        json.dump(issues, out_file, indent=2)


def write_json(
    file: Path,
    error_logs: dict[str, ErrorLogger],
    error_level: int,
    *,
    out_format: Formats = Formats.Jenkins,
):
    if out_format is Formats.CodeClimate:
        write_codeclimate(file, error_logs, error_level)
    elif out_format is Formats.Jenkins:
        write_jenkins(file, error_logs, error_level)
    else:
        msg = "Unrecognised out format."
        raise KeyError(msg)
