# pylint: disable=W0621,C0116,C0114
from castep_linter.fortran.identifier import Identifier


def test_identifier_equals():
    assert Identifier("x") == Identifier("x")
    assert Identifier("X") == Identifier("x")
    assert Identifier("x") == Identifier("X")
    assert Identifier("X") == Identifier("X")


def test_identifier_not_equals():
    assert Identifier("x") != Identifier("y")
    assert Identifier("X") != Identifier("y")
    assert Identifier("x") != Identifier("Y")
    assert Identifier("X") != Identifier("Y")


def test_string_equals():
    assert Identifier("x") == "x"
    assert Identifier("X") == "x"
    assert Identifier("x") == "X"
    assert Identifier("X") == "X"


def test_string_not_equals():
    assert Identifier("x") != "y"
    assert Identifier("X") != "y"
    assert Identifier("x") != "Y"
    assert Identifier("X") != "Y"
