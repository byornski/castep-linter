"""Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

from collections.abc import Iterator

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


def correct_trace_name(trace_name: str, subroutine_name: Identifier):
    """Checks whether a subroutine name given to trace is fine. Allows exceptions from the global list"""
    trace_name = trace_name.lower()
    if trace_name in castep_identifiers.TRACE_NAME_EXCEPTIONS:
        return True
    else:
        return trace_name == subroutine_name


def nested_calls(routine: FortranNode) -> Iterator[FortranCallExpression]:
    """Subroutine calls inside blocks in a routine, eg if or do, but not in routines it contains"""
    stack = [c for c in routine.children if not c.is_type(Fortran.SUBROUTINE_CALL)]
    while stack:
        node = stack.pop()
        if node.ftype in FortranContexts or node.is_type(Fortran.INTERNAL_PROCEDURES):
            continue
        if isinstance(node, FortranCallExpression) and node.is_type(Fortran.SUBROUTINE_CALL):
            yield node
        else:
            stack.extend(node.children)


def trace_name(
    routine: FortranCallExpression, const_string_vars: dict[Identifier, str]
) -> str | None:
    """The name passed to a trace call, if it is a string or a known character parameter"""
    try:
        trace_node = routine.get_arg(position=1, keyword=castep_identifiers.TRACE_STRING).value
    except KeyError:
        return None
    if trace_node.is_type(Fortran.STRING_LITERAL):
        return trace_node.parse_string_literal().lower()
    if trace_node.is_type(Fortran.IDENTIFIER):
        return const_string_vars.get(Identifier.from_node(trace_node))
    return None


# Statements which do nothing when run, so are skipped when looking for the last one
NOT_EXECUTED = (Fortran.COMMENT, Fortran.STATEMENT_LABEL, Fortran.FORMAT_STMT)
NOT_BODY = (
    Fortran.SUBROUTINE_STMT,
    Fortran.FUNCTION_STMT,
    Fortran.END_SUBROUTINE_STMT,
    Fortran.END_FUNCTION_STMT,
    Fortran.INTERNAL_PROCEDURES,
)


def keyword(node: FortranNode) -> str:
    """The keyword of a keyword statement, eg "return" or "goto", or "" for anything else"""
    if not node.is_type(Fortran.KEYWORD_STMT):
        return ""
    return "".join(node.raw.split()).lower().rstrip("0123456789")


def is_one_line_if(node: FortranNode) -> bool:
    return node.is_type(Fortran.IF_STMT) and not any(
        c.is_type(Fortran.END_IF_STMT) for c in node.children
    )


def last_statement(statements: list[FortranNode]) -> FortranNode | None:
    """The last statement which does something, ignoring eg comments and trailing continues"""
    executed = [
        s for s in statements if s.node.is_named and not any(s.is_type(t) for t in NOT_EXECUTED)
    ]
    while executed and keyword(executed[-1]) == "continue":
        executed.pop()
    return executed[-1] if executed else None


def previous_statement(node: FortranNode) -> FortranNode | None:
    """The statement before this one in the same block, ignoring eg comments and labels"""
    sibling = node.node.prev_named_sibling
    while sibling is not None and any(FortranNode(sibling).is_type(t) for t in NOT_EXECUTED):
        sibling = sibling.prev_named_sibling
    return node_factory.wrap_node(sibling) if sibling is not None else None


def has_label(node: FortranNode) -> bool:
    """Whether a statement is labelled, so may be reached by a jump from elsewhere"""
    sibling = node.node.prev_named_sibling
    while sibling is not None and FortranNode(sibling).is_type(Fortran.COMMENT):
        sibling = sibling.prev_named_sibling
    return sibling is not None and FortranNode(sibling).is_type(Fortran.STATEMENT_LABEL)


def if_branches(if_node: FortranNode) -> list[list[FortranNode]]:
    """Statements in each branch of an if block, the first being the "then" branch"""
    branches: list[list[FortranNode]] = [[]]
    for child in if_node.children[1:]:
        if child.is_type(Fortran.ELSEIF_CLAUSE):
            branches.append(child.children[1:])
        elif child.is_type(Fortran.ELSE_CLAUSE):
            branches.append(child.children)
        elif child.node.is_named and not child.is_type(Fortran.PAREN_EXPRESSION):
            branches[0].append(child)
    return [[s for s in branch if not s.is_type(Fortran.END_IF_STMT)] for branch in branches]


def check_return_paths(
    node: FortranNode,
    subroutine_name: Identifier,
    const_string_vars: dict[Identifier, str],
    error_log: ErrorLogger,
) -> bool:
    """
    Test that a routine which calls trace_entry calls trace_exit on every way out of it.
    Returns whether the routine calls trace_entry, so had its paths checked.
    """

    def is_own_trace(statement: FortranNode, trace: Identifier) -> bool:
        # A trace call alone in an if, eg "if (full_trace) call trace_exit(...)", counts as one
        if is_one_line_if(statement):
            statement = statement.children[-1]
        if not isinstance(statement, FortranCallExpression) or statement.name != trace:
            return False
        name = trace_name(statement, const_string_vars)
        return name is not None and correct_trace_name(name, subroutine_name)

    def never_returns(statement: FortranNode) -> bool:
        if isinstance(statement, FortranCallExpression):
            return statement.name in castep_identifiers.NEVER_RETURN
        return statement.is_type(Fortran.STOP_STMT) or keyword(statement) in ("goto", "return")

    def step_back(statement: FortranNode) -> FortranNode | None:
        """The statement run before this one, leaving enclosing blocks as needed"""
        previous = previous_statement(statement)
        while previous is None:
            parent = statement.node.parent
            if parent is None or parent == node.node:
                return None
            statement = node_factory.wrap_node(parent)
            if statement.is_type(Fortran.ELSEIF_CLAUSE) or statement.is_type(Fortran.ELSE_CLAUSE):
                continue
            previous = previous_statement(statement)
        return previous

    def traced_before(statement: FortranNode | None, *, after_label: bool = False) -> bool:
        """
        Whether trace_exit is called on the way to the end of this statement. after_label says
        whether the statement after it is labelled, so may also be reached by a jump.
        """
        while statement is not None:
            if is_own_trace(statement, castep_identifiers.TRACE_EXIT):
                return True
            if is_own_trace(statement, castep_identifiers.TRACE_ENTRY):
                return False
            # Nothing after these is reached, except by a jump to a label which cannot be followed
            if never_returns(statement):
                return not after_label
            # An if block with an else is fine if every branch is
            if statement.is_type(Fortran.IF_STMT) and any(
                c.is_type(Fortran.ELSE_CLAUSE) for c in statement.children
            ):
                return all(
                    traced_before(last_statement(branch) or step_back(statement))
                    for branch in if_branches(statement)
                )
            after_label = has_label(statement)
            statement = step_back(statement)
        return False

    def ends_properly(statement: FortranNode | None) -> bool:
        """Whether a statement ends a way out of the routine, eg trace_exit or err_abort"""
        if statement is None:
            return False
        if is_own_trace(statement, castep_identifiers.TRACE_EXIT) or never_returns(statement):
            return True
        # An if block with an else is fine if every branch is
        if statement.is_type(Fortran.IF_STMT) and any(
            c.is_type(Fortran.ELSE_CLAUSE) for c in statement.children
        ):
            return all(ends_properly(last_statement(branch)) for branch in if_branches(statement))
        return False

    def report(statement: FortranNode, *, traced: bool, at_end: bool) -> None:
        """Report a way out without trace_exit, saying whether trace_exit was called earlier"""
        if at_end:
            if traced:
                err = f"trace_exit is not at the end of {subroutine_name}"
            else:
                err = f"Missing trace_exit at end of {subroutine_name}"
        elif traced:
            err = f"trace_exit is not immediately before return in {subroutine_name}"
        else:
            err = f"Missing trace_exit before return in {subroutine_name}"
        error_log.add_msg("Error", statement, err)

    # Every statement in the routine, but not in routines it contains, in source order
    statements = []
    stack = [c for c in reversed(node.children) if not c.is_type(Fortran.INTERNAL_PROCEDURES)]
    while stack:
        statement = stack.pop()
        if statement.ftype in FortranContexts or statement.is_type(Fortran.INTERNAL_PROCEDURES):
            continue
        statements.append(statement)
        stack.extend(reversed(statement.children))

    entries = [s for s in statements if is_own_trace(s, castep_identifiers.TRACE_ENTRY)]
    if not entries:
        return False
    traced_from = entries[0].node.start_byte

    for statement in statements:
        if keyword(statement) != "return" or statement.node.start_byte < traced_from:
            continue
        parent = statement.node.parent
        # "if (...) return" leaves no room for a trace_exit
        if parent is not None and is_one_line_if(node_factory.wrap_node(parent)):
            report(statement, traced=False, at_end=False)
            continue

        # trace_exit must be immediately before the return, unless it cannot be reached
        previous = previous_statement(statement)
        if previous is not None and (
            is_own_trace(previous, castep_identifiers.TRACE_EXIT)
            or (never_returns(previous) and not has_label(statement))
        ):
            continue
        traced = traced_before(step_back(statement), after_label=has_label(statement))
        report(statement, traced=traced, at_end=False)

    # trace_exit must be at the end of the routine, if it can be reached
    body = [c for c in node.children if not any(c.is_type(t) for t in NOT_BODY)]
    last = last_statement(body)
    if last is not None and not ends_properly(last):
        report(last, traced=traced_before(last), at_end=True)

    return True


def check_trace_entry_exit(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

    if node.is_type(Fortran.SUBROUTINE) or node.is_type(Fortran.FUNCTION):
        subroutine_name = node.get_context_identifier()
    else:
        err = "Wrong node type passed"
        raise WrongNodeError(err)

    # Routines declared in an interface block have no body to call trace from
    parent = node.node.parent
    if parent is not None and FortranNode(parent).is_type(Fortran.INTERFACE):
        return

    has_trace_entry = False
    has_trace_exit = False

    const_string_vars = string_constants(node)

    for routine in node.get_children_by_name(Fortran.SUBROUTINE_CALL):
        if not isinstance(routine, FortranCallExpression):
            err = f"Expected subroutine call but got {node.type}"
            raise WrongNodeError(err)

        if routine.name == castep_identifiers.TRACE_ENTRY:
            has_trace_entry = True
        elif routine.name == castep_identifiers.TRACE_EXIT:
            has_trace_exit = True

        if routine.name not in [castep_identifiers.TRACE_ENTRY, castep_identifiers.TRACE_EXIT]:
            continue

        try:
            trace_node = routine.get_arg(position=1, keyword=castep_identifiers.TRACE_STRING).value
        except KeyError:
            err = f"No name passed to trace in {subroutine_name}"
            error_log.add_msg("Error", routine, err)
            continue

        if trace_node.is_type(Fortran.STRING_LITERAL):
            trace_string = trace_node.parse_string_literal().lower()
            if not correct_trace_name(trace_string, subroutine_name):
                err = f"Incorrect name passed to trace in {subroutine_name}"
                error_log.add_msg("Error", trace_node, err)

        elif trace_node.is_type(Fortran.IDENTIFIER):
            trace_sub_text = Identifier.from_node(trace_node)

            if trace_sub_text in const_string_vars:
                trace_string = const_string_vars[trace_sub_text]

                if not correct_trace_name(trace_string, subroutine_name):
                    err = (
                        f"Incorrect name passed to trace in {subroutine_name} "
                        f'by variable {trace_sub_text}="{trace_string}"'
                    )
                    error_log.add_msg("Error", trace_node, err)
            else:
                err = f"Unidentified variable {trace_sub_text} passed to trace in {subroutine_name}"
                error_log.add_msg("Error", trace_node, err)

        else:
            err = f"Unrecognised name passed to trace in {subroutine_name}"
            error_log.add_msg("Error", trace_node, err)

    # Trace calls inside blocks count if they name this routine; others time a section of it
    for routine in nested_calls(node):
        name = trace_name(routine, const_string_vars)
        if name is None or not correct_trace_name(name, subroutine_name):
            continue
        if routine.name == castep_identifiers.TRACE_ENTRY:
            has_trace_entry = True
        elif routine.name == castep_identifiers.TRACE_EXIT:
            has_trace_exit = True

    # Routines which call trace_entry are checked for trace_exit on each way out instead
    paths_checked = check_return_paths(node, subroutine_name, const_string_vars, error_log)

    if not has_trace_entry:
        error_log.add_msg("Info", node, f"Missing trace_entry in {subroutine_name}")
    if not has_trace_exit and not paths_checked:
        error_log.add_msg("Info", node, f"Missing trace_exit in {subroutine_name}")
