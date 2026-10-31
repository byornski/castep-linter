"""Commonly used identifiers in CASTEP"""

from castep_linter.fortran.identifier import Identifier

# TRACE THINGS
TRACE_ENTRY = Identifier("trace_entry")
TRACE_EXIT = Identifier("trace_exit")
TRACE_STRING = Identifier("string")

# Exceptions for trace subroutine names
CASTEP_TRACE = Identifier("castep")
TRACE_NAME_EXCEPTIONS = [CASTEP_TRACE]


CMPLX = Identifier("cmplx")

# Parameters
DP = Identifier("dp")
DPREC = Identifier("dprec")
DI_DP = Identifier("di_dp")
VERSION_KIND = Identifier("version_kind")

DP_ALL = {DP, DPREC, DI_DP, VERSION_KIND}

# Integer kinds
INT32 = Identifier("int32")
INT64 = Identifier("int64")
INT_KINDS = {INT32, INT64}

# Special keywords
STAT = Identifier("stat")
KIND = Identifier("kind")
ALLOCATE = Identifier("allocate")

# Routines which stop the program, so never return to their caller. io_abort, io_allocate_abort
# and comms_abort also do, but should no longer be called, so are not included
ERR_ABORT = Identifier("err_abort")
ERR_ALLOCATE_ABORT = Identifier("err_allocate_abort")
NEVER_RETURN = {ERR_ABORT, ERR_ALLOCATE_ABORT}

# Routines given the names of the array and the routine when an allocate fails
ALLOCATE_ABORTS = {ERR_ALLOCATE_ABORT}

# The only routines accepted for reporting a failed allocate. err_assert stops the program only
# when its condition is false, so does not count as never returning
ERR_ASSERT = Identifier("err_assert")
ERROR_ROUTINES = {*NEVER_RETURN, ERR_ASSERT}


ALLOCATE_ABORT_ARRAY = Identifier("array_name")
ALLOCATE_ABORT_ROUTINE = Identifier("routine_name")
