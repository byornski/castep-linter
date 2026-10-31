"""Test that allocate stat is used and checked, and that a failure is reported correctly"""

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import node_factory
from castep_linter.fortran.fortran_nodes import (
    FortranCallExpression,
    FortranNode,
    string_constants,
)
from castep_linter.fortran.fortran_raw_types import Fortran, FortranContexts
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.tests import castep_identifiers


def normalised(name: str) -> Identifier:
    """A variable name ignoring case and spaces, eg "obj % Arr" as "obj%arr" """
    return Identifier("".join(name.split()))


def allocate_statement(node: FortranNode) -> FortranCallExpression | None:
    """The node as an allocate statement, or None if it is something else"""
    if not isinstance(node, FortranCallExpression):
        err = f"Expected call expression but got {node.type}"
        raise WrongNodeError(err)
    if node.name != castep_identifiers.ALLOCATE:
        return None
    return node


def stat_checked_by(routine: FortranCallExpression) -> FortranNode | None:
    """The if statement straight after an allocate which checks its stat, if there is one"""
    try:
        stat_variable = Identifier.from_node(routine.get_arg(keyword=castep_identifiers.STAT).value)
    except KeyError:
        return None

    # Find the next non-comment line
    next_node = routine.next_named_sibling()
    while next_node and next_node.is_type(Fortran.COMMENT):
        next_node = next_node.next_named_sibling()

    if not next_node or not next_node.is_type(Fortran.IF_STMT):
        return None

    try:
        relational_expr = next_node.get(Fortran.PAREN_EXPRESSION).get(Fortran.RELATIONAL_EXPR)
    except KeyError:
        return None

    lhs, rhs = relational_expr.split()
    for side in (lhs, rhs):
        if side.is_type(Fortran.IDENTIFIER) and Identifier.from_node(side) == stat_variable:
            return next_node
    return None


def check_allocate_has_stat(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that allocate stat is used and checked"""

    routine = allocate_statement(node)
    if routine is None:
        return

    # First get the stat variable for this allocate statement
    try:
        stat_variable_node = routine.get_arg(keyword=castep_identifiers.STAT).value
    except KeyError:
        error_log.add_msg("Warning", node, "No stat on allocate statement")
        return

    if stat_checked_by(routine) is None:
        error_log.add_msg("Error", stat_variable_node, "Allocate status not checked")


def variable_names_from_allocate(routine: FortranCallExpression) -> list[Identifier]:
    """Names of the variables allocated, eg "x" and "obj%y" in "allocate(x(n), obj%y(m))" """
    args = routine.args.args
    # In a typed allocation, eg "allocate(param_type :: obj%param)", the type comes before "::"
    type_end = next((i for i, arg in enumerate(args) if arg.raw == "::"), None)
    if type_end is not None:
        args = args[type_end + 1 :]

    names = []
    for arg in args:
        # A sized allocation is the variable followed by its size
        variable = arg.children[0] if arg.is_type(Fortran.SIZED_ALLOCATION) else arg
        if variable.is_type(Fortran.IDENTIFIER) or variable.is_type(Fortran.DERIVED_TYPE_MEMBER):
            names.append(normalised(variable.raw))
    return names


def enclosing_routine(node: FortranNode) -> FortranNode | None:
    """The subroutine, function or program containing a node, if any"""
    parent = node.node.parent
    while parent is not None:
        routine = node_factory.wrap_node(parent)
        if routine.ftype in FortranContexts or routine.is_type(Fortran.PROGRAM):
            return routine
        parent = parent.parent
    return None


def routine_name(routine: FortranNode) -> Identifier | None:
    """Name of a subroutine, function or program"""
    if routine.is_type(Fortran.PROGRAM):
        try:
            return Identifier.from_node(routine.get(Fortran.PROGRAM_STMT).get(Fortran.NAME))
        except KeyError:
            return None
    return routine.get_context_identifier()


def name_given(
    arg: FortranNode | None, constants: dict[Identifier, str]
) -> tuple[str, Identifier | None] | None:
    """
    A name passed as a string, or in a character variable with a known value, with the variable
    it is in. Names which are not known until the program runs, eg in arguments, are None.
    """
    if arg is None:
        return None
    if arg.is_type(Fortran.STRING_LITERAL):
        return arg.parse_string_literal(), None
    if arg.is_type(Fortran.IDENTIFIER):
        variable = Identifier.from_node(arg)
        if variable in constants:
            return constants[variable], variable
    return None


def wrong_name(kind: str, given: tuple[str, Identifier | None], expected: str) -> str:
    """Message for a wrong name given to io_allocate_abort, saying which variable it was in"""
    value, variable = given
    by_variable = f' by variable {variable}="{value}"' if variable is not None else ""
    return f"Wrong {kind} name used in io_allocate_abort{by_variable}. Expected: {expected}"


def check_allocate_abort(node: FortranNode, error_log: ErrorLogger) -> None:
    """
    Test that a failed allocate is reported with one of the error routines, and that
    io_allocate_abort is told the names of the array and the routine
    """

    allocate = allocate_statement(node)
    if allocate is None:
        return

    # Allocates whose stat is not checked are reported by check_allocate_has_stat
    if_node = stat_checked_by(allocate)
    if if_node is None:
        return

    calls = [
        c
        for c in if_node.get_children_by_name(Fortran.SUBROUTINE_CALL)
        if isinstance(c, FortranCallExpression)
    ]
    if not any(c.name in castep_identifiers.ERROR_ROUTINES for c in calls):
        error_log.add_msg("Error", if_node, "Allocation failure does not raise an error")
        return

    abort = next((c for c in calls if c.name == castep_identifiers.IO_ALLOCATE_ABORT), None)
    if abort is None:
        return

    routine = enclosing_routine(allocate)
    constants = string_constants(routine) if routine is not None else {}

    try:
        array_node = abort.get_arg(position=1, keyword=castep_identifiers.IO_AA_ARRAY).value
    except KeyError:
        array_node = None
    given = name_given(array_node, constants)
    if array_node is not None and given is not None:
        variable_names = variable_names_from_allocate(allocate)
        if normalised(given[0]) not in variable_names:
            expected = " or ".join(str(name) for name in variable_names)
            error_log.add_msg("Error", array_node, wrong_name("array", given, expected))

    subroutine_name = routine_name(routine) if routine is not None else None
    try:
        routine_node = abort.get_arg(position=2, keyword=castep_identifiers.IO_AA_ROUTINE).value
    except KeyError:
        routine_node = None
    given = name_given(routine_node, constants)
    if (
        subroutine_name is not None
        and routine_node is not None
        and given is not None
        and Identifier(given[0]) != subroutine_name
    ):
        error_log.add_msg(
            "Error", routine_node, wrong_name("subroutine", given, str(subroutine_name))
        )
