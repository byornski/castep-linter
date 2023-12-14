from enum import Enum, auto


class Fortran(Enum):
    """Represents raw fortran source code tree elements"""

    COMMENT = "comment"
    SUBROUTINE = "subroutine"
    SUBROUTINE_STMT = "subroutine_statement"
    FUNCTION = "function"
    FUNCTION_STMT = "function_statement"
    NAME = "name"
    SIZE = "size"
    INTRINSIC_TYPE = "intrinsic_type"
    ASSIGNMENT_STMT = "assignment_statement"
    ARGUMENT_LIST = "argument_list"
    SUBROUTINE_CALL = "subroutine_call"
    IDENTIFIER = "identifier"
    VARIABLE_DECLARATION = "variable_declaration"
    RELATIONAL_EXPR = "relational_expression"
    IF_STMT = "if_statement"
    PAREN_EXPRESSION = "parenthesized_expression"
    KEYWORD_ARGUMENT = "keyword_argument"
    STRING_LITERAL = "string_literal"
    NUMBER_LITERAL = "number_literal"
    TYPE_QUALIFIER = "type_qualifier"
    CALL_EXPRESSION = "call_expression"

    UNKNOWN = "unknown"


class FType(Enum):
    """Intrinsic variable types in fortran"""

    REAL = auto()
    DOUBLE = auto()
    COMPLEX = auto()
    INTEGER = auto()
    LOGICAL = auto()
    CHARACTER = auto()
    OTHER = auto()


FortranLookup = {k.value: k for k in Fortran}
FortranContexts = {Fortran.SUBROUTINE, Fortran.FUNCTION}
