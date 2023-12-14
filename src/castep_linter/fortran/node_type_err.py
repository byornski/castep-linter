"""Module holding methods for type checking tree_sitter Node functions"""


class WrongNodeError(Exception):
    """Exception thrown when an invalid node is passed to a typed function"""


class FortranContextError(Exception):
    """Exception thrown when some fortran code does not have a containing context (eg subroutine or function)"""
