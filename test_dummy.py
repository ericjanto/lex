"""
Dummy test file to test pytest setup
"""


def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 4
