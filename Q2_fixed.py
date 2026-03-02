"""Fixed version of buggy Python code — Part C Q2."""


def check_version():
    """Check Python version and print result."""
    import sys

    v = sys.version_info
    if v.minor >= 11:
        print("Python 3.11+ detected.")
    else:
        print("Python version is older than 3.11.")


check_version()
