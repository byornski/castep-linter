""""Tests to be performed by the CASTEP Fortran linter"""
from .allocate_stat_checked import test_allocate_has_stat
from .complex_has_dp import test_complex_has_dp
from .has_trace_entry_exit import test_trace_entry_exit
from .number_literal_correct_kind import test_number_literal
from .real_declaration_has_dp import test_real_dp_declaration

all = [test_trace_entry_exit, test_real_dp_declaration, test_number_literal, test_complex_has_dp]

test_list = {
   "variable_declaration": [test_real_dp_declaration],
   "subroutine": [test_trace_entry_exit], 
   "function": [test_trace_entry_exit],
   "call_expression": [test_complex_has_dp, test_allocate_has_stat],
   "number_literal": [test_number_literal],
}