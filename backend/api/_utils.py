"""
Collection of utility methods
"""

import os
from pathlib import Path
from typing import Union


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


def relativy_path(path: str) -> str:
    # TODO @ej I don't think this is working
    cwd = os.path.basename(os.getcwd())
    if path == "_db.py":
        return f"{'backend/api/' if cwd != 'backend/api' else ''}{path}"
    else:
        return f"{'backend/' if cwd != 'backend' else ''}{path}"
