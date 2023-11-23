from typing import List, Optional, Tuple

from tree_sitter import Node


class WrongNodeError(Exception):
    """Exception thrown when an invalid node is passed to a typed function"""


class FortranNode:
    """Wrapper for tree_sitter Node type to add extra functionality"""

    def __init__(self, node: Node):
        self.node = node

        self.type: Optional[str]

        if self.node.is_named:
            self.type = self.node.type
        else:
            self.type = None

    def get_children(self) -> List["FortranNode"]:
        return [FortranNode(c) for c in self.node.children]

    def next_named_sibling(self) -> Optional["FortranNode"]:
        if self.node.next_named_sibling:
            return FortranNode(self.node.next_named_sibling)
        else:
            return None

    def get_child_by_name(self, typename: str) -> "FortranNode":
        """Return the first child node with the requested type"""
        for c in self.node.named_children:
            if c.type == typename:
                return FortranNode(c)

        err = f'"{typename}" not found in children of node {self.raw()}'
        raise KeyError(err)

    def get_children_by_name(self, typename: str) -> List["FortranNode"]:
        """Return all the children with the requested type"""
        return [FortranNode(c) for c in self.node.named_children if c.type == typename]

    def get_child_property(self, prop: str) -> "FortranNode":
        """Finds a nested property of the form node.subroutine_statment.name"""
        properties = prop.split(".")
        cursor = self
        for p in properties:
            cursor = cursor.get_child_by_name(p)
        return cursor

    def split(self) -> Tuple["FortranNode", "FortranNode"]:
        """Split a relational node with a left and right part into the two child nodes"""
        left = self.node.child_by_field_name("left")

        if left is None:
            err = f"Unable to find left part of node pair: {self.raw()}"
            raise KeyError(err)

        right = self.node.child_by_field_name("right")

        if right is None:
            err = f"Unable to find right part of node pair: {self.raw()}"
            raise KeyError(err)

        return FortranNode(left), FortranNode(right)

    def raw(self, *, lower=False) -> str:
        """Return a string of all the text in a node as unicode"""
        if lower:
            return self.node.text.decode().lower()
        else:
            return self.node.text.decode()

    def parse_string_literal(self) -> str:
        "Parse a string literal object to get the string"
        if not self.type == "string_literal":
            err = f"Tried to parse {self.raw()} as string literal"
            raise WrongNodeError(err)
        return self.raw().strip("\"'")
