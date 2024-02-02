"""General fixtures for testing castep-linter"""

from typing import Callable

import pytest

from castep_linter.fortran.parser import FortranTree

Parser = Callable[[bytes], FortranTree]


@pytest.fixture
def parse() -> Parser:
    """Get a general code parser"""

    def _parse(code: bytes) -> FortranTree:
        return FortranTree(code)

    return _parse


CodeWrapper = Callable[[bytes], bytes]


@pytest.fixture
def subroutine_wrapper() -> CodeWrapper:
    """Wrapper to give a subroutine context to code"""

    def _subroutine_wrapper(code: bytes) -> bytes:
        return (
            b"""module foo
            subroutine x(y)
            """
            + code
            + b"""
            end subroutine x
            end module foo"""
        )

    return _subroutine_wrapper


@pytest.fixture
def function_wrapper() -> CodeWrapper:
    """Wrapper to give a function context to code"""

    def _function_wrapper(code: bytes) -> bytes:
        return (
            b"""module foo
            function x(y)
            """
            + code
            + b"""
            end function x
            end module foo"""
        )

    return _function_wrapper
