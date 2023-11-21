import importlib.resources
from tree_sitter import Language
from importlib.resources import files, as_file

file_ref = files("castep_linter") / "tree_sitter_fortran"
with as_file(file_ref) as tree_sitter_dir:
    Language.build_library(str(tree_sitter_dir / "fortran.so"), [str(tree_sitter_dir)])
