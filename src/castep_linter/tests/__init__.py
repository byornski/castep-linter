""""Tests to be performed by the CASTEP Fortran linter"""
from castep_linter.tests.allocate_stat_checked import check_allocate_has_stat
from castep_linter.tests.complex_has_dp import check_complex_has_dp
from castep_linter.tests.has_trace_entry_exit import test_trace_entry_exit
from castep_linter.tests.number_literal_correct_kind import test_number_literal
from castep_linter.tests.real_declaration_has_dp import check_real_dp_declaration

test_list = {
    "variable_declaration": [check_real_dp_declaration],
    "subroutine": [test_trace_entry_exit],
    "function": [test_trace_entry_exit],
    "call_expression": [check_complex_has_dp, check_allocate_has_stat],
    "number_literal": [test_number_literal],
}
