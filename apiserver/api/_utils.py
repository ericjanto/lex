"""
Collection of utility methods
"""

import subprocess


def get_git_root() -> str:
    # E.g. '/Users/ericjanto/Developer/Projects/lex'
    command = ["git", "rev-parse", "--show-toplevel"]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def absolutify_path_from_root(path_relative_from_root: str) -> str:
    # NOTE: get_git_root() does not have trailing slash
    # e.g. /apiserver/api/_db.py
    #   => /Users/ericjanto/Developer/Projects/lex/apiserver/api/_db.py
    return f"{get_git_root()}{path_relative_from_root}"
