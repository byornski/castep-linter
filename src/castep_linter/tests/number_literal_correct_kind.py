"""Test that a number literal has a dp (if real) or no dp if of any other type"""
from tree_sitter import Node

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import parser


@parser.node_type_check("number_literal")
def test_number_literal(node: Node, error_log: ErrorLogger) -> None:
    """Test that a number literal has a dp (if real) or no dp if of any other type"""

    def is_int(x: str) -> bool:
        return not any(c in x.lower() for c in [".", "e", "d"])

    literal_string = node.raw(lower=True)

    if "_" in literal_string:
        value, kind = literal_string.split("_", maxsplit=1)

        if is_int(value):
            error_log.add_msg("Error", node, f"Integer literal with {kind=}")
        elif kind != "dp":
            error_log.add_msg("Error", node, f"Float literal with {kind=}")

    elif "d" in literal_string:
        pass  # eg 5.0d4
    elif not is_int(literal_string):
        error_log.add_msg("Error", node, "Float literal without kind")
