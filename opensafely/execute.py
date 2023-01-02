import argparse
import os
import pathlib
import subprocess

from opensafely._vendor.jobrunner import config
from opensafely._vendor.jobrunner.cli.local_run import (
    STATA_ERROR_MESSGE,
    docker_preflight_check,
    get_stata_license,
)
from opensafely.windows import ensure_tty


DESCRIPTION = "Run an OpenSAFELY action outside of the `project.yaml` pipeline"


def get_default_user():
    try:
        # On ~unix, in order for any files that get created to have the
        # appropriate owner/group we run the command using the current user's
        # UID/GID
        return f"{os.getuid()}:{os.getgid()}"
    except Exception:
        # These aren't available on Windows; but then on Windows we don't have to deal
        # with the same file ownership problems which require us to match the UID in the
        # first place.
        return None


DEFAULT_USER = get_default_user()


def add_arguments(parser):
    # these three arguments are direct copies of docker run arguments. The must be
    # supplied before the image name, just like docker run.
    parser.add_argument("--entrypoint", default=None, help="Set docker entrypoint")
    parser.add_argument("--env", "-e", action="append", default=[], help="Set env vars")
    parser.add_argument(
        "--user",
        "-u",
        default=DEFAULT_USER,
        help="Unix user/group to run as (uid:gid). Defaults to current user",
    )

    # this is specific to opensafely exec, and prints the full command line to
    # the console before executing.
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose debugging information",
    )

    parser.add_argument(
        "image",
        metavar="IMAGE_NAME:VERSION",
        help="OpenSAFELY image and version (e.g. databuilder:v1)",
    )
    parser.add_argument(
        "cmd_args",
        nargs=argparse.REMAINDER,
        metavar="...",
        help="Any additional arguments to pass to the image",
    )

    return parser


def main(
    image,
    entrypoint=None,
    env=[],
    user=None,
    verbose=False,
    cmd_args=[],
    environ=os.environ,
):
    if not docker_preflight_check():
        return False

    cmd_env = environ.copy()

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        f"--volume={pathlib.Path.cwd()}:/workspace",
    ]

    if user and user.lower() not in ("none", "no", "false"):
        docker_cmd.append(f"--user={user}")

    for e in env:
        docker_cmd.extend(["--env", e])

    if image.startswith("stata"):
        if "STATA_LICENSE" not in cmd_env:
            license = get_stata_license()
            if license is None:
                print(STATA_ERROR_MESSGE)
                return False
            else:
                cmd_env["STATA_LICENSE"] = license

        docker_cmd.extend(["--env", "STATA_LICENSE"])

    if entrypoint:
        docker_cmd.append(f"--entrypoint={entrypoint}")

    docker_cmd.extend(
        [
            f"{config.DOCKER_REGISTRY}/{image}",
            *cmd_args,
        ]
    )

    if verbose:
        print(" ".join(docker_cmd))

    proc = subprocess.run(ensure_tty(docker_cmd), env=cmd_env)
    return proc.returncode == 0
