from enum import Enum, auto


class Fortran(Enum):
    """Represents raw fortran source code tree elements"""

    COMMENT = "comment"
    SUBROUTINE = "subroutine"
    SUBROUTINE_STMT = "subroutine_statement"
    FUNCTION = "function"
    FUNCTION_STMT = "function_statement"
    INTERFACE = "interface"
    PROGRAM = "program"
    PROGRAM_STMT = "program_statement"
    INTERNAL_PROCEDURES = "internal_procedures"
    NAME = "name"
    SIZE = "size"
    KIND = "kind"
    INTRINSIC_TYPE = "intrinsic_type"
    ASSIGNMENT_STMT = "assignment_statement"
    INIT_DECLARATOR = "init_declarator"
    ARGUMENT_LIST = "argument_list"
    SUBROUTINE_CALL = "subroutine_call"
    IDENTIFIER = "identifier"
    VARIABLE_DECLARATION = "variable_declaration"
    RELATIONAL_EXPR = "relational_expression"
    IF_STMT = "if_statement"
    ELSEIF_CLAUSE = "elseif_clause"
    ELSE_CLAUSE = "else_clause"
    END_IF_STMT = "end_if_statement"
    END_SUBROUTINE_STMT = "end_subroutine_statement"
    END_FUNCTION_STMT = "end_function_statement"
    KEYWORD_STMT = "keyword_statement"
    STOP_STMT = "stop_statement"
    STATEMENT_LABEL = "statement_label"
    FORMAT_STMT = "format_statement"
    PAREN_EXPRESSION = "parenthesized_expression"
    KEYWORD_ARGUMENT = "keyword_argument"
    STRING_LITERAL = "string_literal"
    NUMBER_LITERAL = "number_literal"
    TYPE_QUALIFIER = "type_qualifier"
    CALL_EXPRESSION = "call_expression"
    ALLOCATE_STMT = "allocate_statement"
    SIZED_ALLOCATION = "sized_allocation"
    DERIVED_TYPE_MEMBER = "derived_type_member_expression"

    UNKNOWN = "unknown"


class FType(Enum):
    """Intrinsic variable types in fortran"""

    REAL = auto()
    DOUBLE = auto()
    COMPLEX = auto()
    DOUBLE_COMPLEX = auto()
    INTEGER = auto()
    LOGICAL = auto()
    CHARACTER = auto()
    OTHER = auto()


FortranLookup = {k.value: k for k in Fortran}
FortranContexts = {Fortran.SUBROUTINE, Fortran.FUNCTION}
