"""Tests to be performed by the CASTEP Fortran linter"""

from collections.abc import Callable

from castep_linter.error_logging.logger import ErrorLogger
from castep_linter.fortran.fortran_nodes import FortranNode
from castep_linter.tests.allocate_stat_checked import check_allocate_has_stat
from castep_linter.tests.complex_has_dp import check_complex_has_dp
from castep_linter.tests.has_trace_entry_exit import check_trace_entry_exit
from castep_linter.tests.number_literal_correct_kind import check_number_literal
from castep_linter.tests.real_declaration_has_dp import check_real_dp_declaration

CheckFunction = Callable[[FortranNode, ErrorLogger], None]
CheckFunctionDict = dict[str, list[CheckFunction]]

test_list: CheckFunctionDict = {
    "variable_declaration": [check_real_dp_declaration],
    "subroutine": [check_trace_entry_exit],
    "function": [check_trace_entry_exit],
    "call_expression": [check_complex_has_dp],
    "allocate_statement": [check_allocate_has_stat],
    "number_literal": [check_number_literal],
}

# Names used to refer to each check, eg in "! castep-lint: disable=TRACE" comments
CHECK_NAMES: dict[CheckFunction, str] = {
    check_trace_entry_exit: "TRACE",
    check_allocate_has_stat: "ALLOC",
    check_real_dp_declaration: "KIND",
    check_number_literal: "LITERAL_KIND",
    check_complex_has_dp: "CMPLX_KIND",
}
