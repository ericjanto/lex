import subprocess

import pytest

from const import Const
from utils import buf_count_newlines

base_vocab_changed = pytest.mark.skipif(
    condition=not bool(
        subprocess.run(
            ["git", "diff", "--exit-code", Const.PATH_BASE_VOCAB]
        ).returncode
    ),
    reason="base vocabulary has not changed",
)

irrelevant_vocab_changed = pytest.mark.skipif(
    condition=not bool(
        subprocess.run(
            ["git", "diff", "--exit-code", Const.PATH_IRRELEVANT_VOCAB]
        ).returncode
    ),
    reason="irrelevant vocabulary has not changed",
)


@base_vocab_changed
def test_no_base_duplicates():
    total_count = buf_count_newlines(Const.PATH_BASE_VOCAB)
    with open(Const.PATH_BASE_VOCAB) as f:
        set_count = len(set(f.readlines()))
    assert total_count == set_count


@irrelevant_vocab_changed
def test_no_irrelevant_duplicates():
    total_count = buf_count_newlines(Const.PATH_IRRELEVANT_VOCAB)
    with open(Const.PATH_IRRELEVANT_VOCAB) as f:
        set_count = len(set(f.readlines()))
    assert total_count == set_count
