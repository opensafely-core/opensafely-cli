import subprocess
import sys
from pathlib import Path

from opensafely._vendor import requests

import opensafely


DESCRIPTION = "Upgrade the opensafely cli tool."


def add_arguments(parser):
    parser.add_argument(
        "version",
        nargs="?",
        default="latest",
        help="Version to upgrade to (default: latest)",
    )


def main(version):
    if version == "latest":
        version = get_latest_version()

    if not need_to_update(version):
        print(f"opensafely is already at version {version}")
        return 0

    if is_installed_with_uv():
        print(
            "The OpenSAFELY tool has been installed using `uv` so cannot be directly"
            " upgraded.\n"
            "\n"
            "Instead, please run:\n"
            "\n"
            "    uv tool upgrade opensafely\n"
        )
        return 1

    pkg = "opensafely==" + version

    if sys.platform == "win32":
        print(f"Upgrading opensafely tool to {version}.")
        # must use Popen directly, so we don't wait for it to complete.
        subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
        )
        # Due to Window's file locking behaviour, we exit to allow the pip
        # upgrade to update us
        sys.exit(0)

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg], check=True
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc)


def get_latest_version():
    resp = requests.get("https://pypi.org/pypi/opensafely/json").json()
    return resp["info"]["version"]


def comparable(version_string):
    if version_string == "not-from-a-package":
        return (0,)
    try:
        return tuple(int(s) for s in version_string.split("."))
    except Exception:
        raise Exception(f"Invalid version string: {version_string}")


def need_to_update(latest):
    current = None
    current = opensafely.__version__.lstrip("v")
    return comparable(latest) > comparable(current)


def check_version():
    latest = get_latest_version()
    if need_to_update(latest):
        return latest
    else:
        return False


def is_installed_with_uv():
    # This was the most robust way I could think of for detecting a `uv` installation.
    # I'm reasonably confident in its specificity. It's possible that a `uv` change will
    # cause this to give false negatives, but the tests should catch that.
    return Path(sys.prefix).joinpath("uv-receipt.toml").exists()
