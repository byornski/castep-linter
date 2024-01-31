"""Module to write code linting errors in Jenkins json format"""
import json

from pathlib import Path
from typing import Dict, Union

from castep_linter.error_logging.logger import ErrorLogger


SEVERITY = ("LOW", "NORMAL", "HIGH", "ERROR")
JSONCompat = Dict[str, Union[str, int, list]]


def write_json(file: Path, error_logs: Dict[str, ErrorLogger], error_level: int):
    """write code linting errors in Jenkins json format"""

    report: JSONCompat = {"_class": "io.jenkins.plugins.analysis.core.restapi.ReportApi"}

    report["issues"] = [{"fileName": scanned_file,
                         "severity": SEVERITY[error.ERROR_SEVERITY],
                         "message": error.message,
                         "lineStart": error.start_point[0]+1,  # Jenkins lines 1-indexed
                         "lineEnd": error.end_point[0]+1,
                         "columnStart": error.start_point[1]+1,
                         "columnEnd": error.end_point[1]+1}

                        for scanned_file, log in error_logs.items()
                        for error in log.errors
                        if error.ERROR_SEVERITY >= error_level]
    report["size"] = len(report["issues"])

    with open(file, "w", encoding="utf-8") as out_file:
        json.dump(report, out_file, indent=2)
