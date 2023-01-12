import os
import shutil
import subprocess
import sys
from pathlib import Path

import opensafely
from opensafely._vendor import requests


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

    # Windows shennanigans: pip triggers a permissions error when it tries to
    # update the currently executing binary. However if we replace the binary
    # with a copy of itself (i.e. copy to a temporary file and then move the
    # copy over the original) it runs quite happily. This is fine.
    entrypoint_bin = Path(sys.argv[0]).with_suffix(".exe")
    if os.name == "nt" and entrypoint_bin.exists():
        tmp_file = entrypoint_bin.with_suffix(".exe._opensafely_.tmp")
        # copy2 attempts to preserve all file metadata
        shutil.copy2(entrypoint_bin, tmp_file)
        # Under some circumstances we can move the copy directly over the
        # existing file, which is safer because at no point does the file not
        # exist and cleaner because it doesn't leave an old file lying around
        try:
            tmp_file.replace(entrypoint_bin)
        # Sometimes, however, this doesn't work in which case we have to move
        # the original file out of the way first
        except PermissionError:
            entrypoint_bin.replace(entrypoint_bin.with_suffix(".exe._old_.tmp"))
            tmp_file.replace(entrypoint_bin)

    pkg = "opensafely==" + version

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
    update = need_to_update(latest)
    if update:
        print(
            f"Warning: there is a newer version of opensafely available ({latest}) - please upgrade by running:\n"
            "    opensafely upgrade\n",
            file=sys.stderr,
        )
    return update
