"""Module to write code linting errors in JUnit XML format"""

from pathlib import Path
from typing import Dict

from junitparser import Error, JUnitXml, Skipped, TestCase, TestSuite  # type: ignore

from castep_linter.error_logging.logger import ErrorLogger


def write_xml(file: Path, error_logs: Dict[str, ErrorLogger], error_level: int):
    """write code linting errors in JUnit XML format"""
    xml = JUnitXml()
    for scanned_file, log in error_logs.items():
        suite = TestSuite(scanned_file)

        for error in log.errors:
            case = TestCase(str(error))
            if error.ERROR_SEVERITY >= error_level:
                case.result = [Error(error.context(scanned_file, underline=True))]
            else:
                case.result = [Skipped(error.context(scanned_file, underline=True))]
            suite.add_testcase(case)

        xml.add_testsuite(suite)

    xml.write(str(file))
