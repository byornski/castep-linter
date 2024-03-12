"""Commonly used identifiers in CASTEP"""

from castep_linter.fortran.identifier import Identifier

# TRACE THINGS
TRACE_ENTRY = Identifier("trace_entry")
TRACE_EXIT = Identifier("trace_exit")
TRACE_STRING = Identifier("string")


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

IO_ABORT = Identifier("io_abort")
IO_ALLOCATE_ABORT = Identifier("io_allocate_abort")

IO_ABORT_ANY = {IO_ABORT, IO_ALLOCATE_ABORT}

ARRAY = Identifier("---NONE---")


IO_AA_ARRAY = Identifier("array_name")
IO_AA_ROUTINE = Identifier("routine_name")
