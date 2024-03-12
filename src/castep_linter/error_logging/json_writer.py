"""Module to write code linting errors in Jenkins json format"""

import json
from pathlib import Path
from typing import Dict, List, Literal, TypedDict

from castep_linter.error_logging.error_types import FORTRAN_ERRORS
from castep_linter.error_logging.logger import ErrorLogger

JSONSeverityLevel = Literal["LOW", "NORMAL", "HIGH", "ERROR"]

JSON_severity_dict: Dict[int, JSONSeverityLevel] = {
    FORTRAN_ERRORS["Error"].ERROR_SEVERITY: "HIGH",
    FORTRAN_ERRORS["Warn"].ERROR_SEVERITY: "NORMAL",
    FORTRAN_ERRORS["Info"].ERROR_SEVERITY: "LOW",
}


class JSONIssue(TypedDict):
    """Represents a single issue in a Jenkins JSON report"""

    fileName: str
    severity: JSONSeverityLevel
    message: str
    type: str
    lineStart: int
    lineEnd: int
    columnStart: int
    columnEnd: int


class JSONReport(TypedDict):
    """Represents an entire report"""

    _class: str
    issues: List[JSONIssue]
    size: int


def write_json(file: Path, error_logs: Dict[str, ErrorLogger], error_level: int):
    """write code linting errors in Jenkins json format"""

    issues: List[JSONIssue] = [
        JSONIssue(
            fileName=scanned_file,
            severity=JSON_severity_dict[error.ERROR_SEVERITY],
            message=error.message,
            type=determine_type(error.message),
            lineStart=error.start_point[0] + 1,  # Jenkins lines 1-indexed
            lineEnd=error.end_point[0] + 1,
            columnStart=error.start_point[1] + 1,
            columnEnd=error.end_point[1] + 1,
        )
        for scanned_file, log in error_logs.items()
        for error in log.errors
        if error.ERROR_SEVERITY >= error_level
    ]

    report: JSONReport = {
        "_class": "io.jenkins.plugins.analysis.core.restapi.ReportApi",
        "issues": issues,
        "size": len(issues),
    }

    with open(file, "w", encoding="utf-8") as out_file:
        json.dump(report, out_file, indent=2)


def determine_type(message: str) -> str:
    """Determine type of error from key components"""
    if "alloc" in message.lower():
        return "ALLOC"

    if "complex intrinsic" in message:
        return "CMPLX_KIND"

    if "literal" in message:
        return "LITERAL_KIND"

    if "kind" in message or "Kind" in message:
        return "KIND"

    if "Missing trace_" in message or "Incorrect name" in message:
        return "TRACE"

    return "UNKNOWN"
