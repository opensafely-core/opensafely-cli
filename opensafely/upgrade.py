from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path
import tempfile

import opensafely
from opensafely._vendor import requests


DESCRIPTION = "Upgrade the opensafely cli tool."

CACHE_FILE = Path(tempfile.gettempdir()) / "opensafely-latest-version"


def add_arguments(parser):
    parser.add_argument(
        "version",
        nargs="?",
        default="latest",
        help="Version to upgrade to (default: latest)",
    )


def main(version):
    if version == "latest":
        version = get_latest_version(force=True)

    if not need_to_update(version):
        print(f"opensafely is already at version {version}")
        return 0

    pkg = "opensafely==" + version

    try:
        subprocess.run(["pip", "install", "--upgrade", pkg], check=True)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc)


def get_latest_version(force=False):
    latest = None
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)

    if CACHE_FILE.exists():
        if CACHE_FILE.stat().st_mtime > two_hours_ago.timestamp():
            latest = CACHE_FILE.read_text().strip()

    if force or latest is None:
        resp = requests.get("https://pypi.org/pypi/opensafely/json").json()
        latest = resp["info"]["version"]
        CACHE_FILE.write_text(latest)

    return latest


def comparable(version_string):
    try:
        return tuple(int(s) for s in version_string.split("."))
    except Exception:
        raise Exception(f"Invalid version string: {version_string}")


def need_to_update(latest):
    current = None
    current = opensafely.__version__.lstrip("v")
    return comparable(latest) > comparable(current)


def check_version():
    try:
        latest = get_latest_version()
        update = need_to_update(latest)
        if update:
            print(
                f"Warning: there is a newer version of opensafely available - please run 'opensafely upgrade' to update to {latest}\n"
            )
        return update
    except Exception:
        pass  # this is an optional check, it should never stop the program
