"""
Collection of utility methods
"""

import subprocess
from pathlib import Path
from typing import Union

from rich.progress import (
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def buf_count_newlines(path: Union[Path, str]) -> int:
    # https://stackoverflow.com/questions/845058
    def _make_gen(reader):
        while True:
            b = reader(2**16)
            if not b:
                break
            yield b

    with open(path, "rb") as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count


def get_git_root() -> str:
    # E.g. '/Users/ericjanto/Developer/Projects/lex'
    command = ["git", "rev-parse", "--show-toplevel"]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def absolutify_path_from_root(path_from_root: str) -> str:
    # e.g. /backend/api/_db.py
    #   => /Users/ericjanto/Developer/Projects/lex/backend/api/_db.py
    return f"{get_git_root() + path_from_root}"


def enhanced_progress_params():
    return (
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        "Elapsed:",
        TimeElapsedColumn(),
        "Remaining:",
        TimeRemainingColumn(),
    )
