from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from castep_linter.fortran.fortran_nodes import FortranNode


@dataclass
class ArgumentItem:
    """Item in argument list"""

    value: "FortranNode"


@dataclass
class KeywordArgument(ArgumentItem):
    """Item in argument list specified by keyword"""


@dataclass
class PositionalArgument(ArgumentItem):
    """Item in argument list specified by position"""
