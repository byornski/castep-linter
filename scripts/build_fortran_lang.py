import shutil
import os
from typing import Any
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class TreeSitterBuildHook(BuildHookInterface):
    PLUGIN_NAME = "TreeSitterFortran"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        from tree_sitter import Language
        fortran_language_so = "build/fortran.so"
        Language.build_library(fortran_language_so, ["tree_sitter_fortran"])
        build_data['artifacts'].append(fortran_language_so)

    def clean(self, versions: list[str]) -> None:
        try:
            shutil.rmtree(os.path.join(self.directory, "..", "build"))
        except FileNotFoundError:
            pass
