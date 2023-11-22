from pathlib import Path
from typing import Dict
from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error

from castep_linter.error_logging.logger import ErrorLogger


def write_xml(file: Path, error_logs: Dict[str, ErrorLogger]):

    xml = JUnitXml()
    for scanned_file, log in error_logs.items():

        suite = TestSuite(scanned_file)

        for error in log.errors:
            case = TestCase(str(error))
            case.result = [Error(error.context(scanned_file))]
            suite.add_testcase(case)

        xml.add_testsuite(suite)

    xml.write(file)

