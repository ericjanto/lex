"""
Collection of utility methods
"""

import os
from pathlib import Path


def buf_count_newlines(path: Path | str) -> int:
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
    cwd = os.path.basename(os.getcwd())
    return f"{'backend/' if cwd != 'backend' else ''}{path}"
