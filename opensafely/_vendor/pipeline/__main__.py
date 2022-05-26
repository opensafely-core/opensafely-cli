"""
This module is for testing in local development.
"""
import sys

from devtools import debug

from .main import load_pipeline


# just for testing locally
def cli():
    paths = sys.argv[1:]

    if not paths:
        print("No paths given, nothing to do.")
        sys.exit()

    for path in paths:
        with open(path) as f:
            contents = f.read()
        data = load_pipeline(contents, path)
        debug(data)


if __name__ == "__main__":
    cli()
