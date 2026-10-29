"""Module to write code linting errors in Jenkins json format"""

import json
from pathlib import Path
from typing import Literal, TypedDict

from castep_linter.error_logging.error_types import FORTRAN_ERRORS, UNKNOWN_CHECK
from castep_linter.error_logging.logger import ErrorLogger

JenkinsSeverityLevel = Literal["LOW", "NORMAL", "HIGH", "ERROR"]
Jenkins_severity_dict: dict[int, JenkinsSeverityLevel] = {
    FORTRAN_ERRORS["Error"].ERROR_SEVERITY: "HIGH",
    FORTRAN_ERRORS["Warn"].ERROR_SEVERITY: "NORMAL",
    FORTRAN_ERRORS["Info"].ERROR_SEVERITY: "LOW",
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
