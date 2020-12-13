from sys import stderr
from sys import stdout


def test_quiet():
    pass


def test_stdout():
    print("some text on stdout", file=stdout)


def test_stderr():
    print("some text on stderr", file=stderr)
