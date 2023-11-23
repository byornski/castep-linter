# pylint: disable=W0621,C0116,C0114,C0121
import pytest

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


def test_identifier_hash_eq():
    assert hash(Identifier("x")) == hash(Identifier("x"))
    assert hash(Identifier("X")) == hash(Identifier("x"))
    assert hash(Identifier("x")) == hash(Identifier("X"))
    assert hash(Identifier("X")) == hash(Identifier("X"))


def test_identifier_hash_not_equals():
    assert hash(Identifier("x")) != hash(Identifier("y"))
    assert hash(Identifier("X")) != hash(Identifier("y"))
    assert hash(Identifier("x")) != hash(Identifier("Y"))
    assert hash(Identifier("X")) != hash(Identifier("Y"))


def test_identifier_compare_none():
    assert Identifier("x") != None  # noqa: E711
    assert Identifier("X") != None  # noqa: E711
    assert None != Identifier("x")  # noqa: E711
    assert None != Identifier("X")  # noqa: E711


def test_identifier_compare_object():
    with pytest.raises(TypeError):
        assert Identifier("x") != object()
