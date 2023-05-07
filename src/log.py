import sys


def log(*args, **kwargs):
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)


def warn(*args, **kwargs):
    kwargs.setdefault("file", sys.stderr)
    print("WARN:", *args, **kwargs)