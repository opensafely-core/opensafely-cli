import argparse
import os
import pathlib
import subprocess

from opensafely._vendor.jobrunner import config
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check


DESCRIPTION = "Run an OpenSAFELY action outside of the `project.yaml` pipeline"


def add_arguments(parser):
    parser.add_argument(
        "image",
        metavar="IMAGE_NAME:VERSION",
        help="OpenSAFELY image and version (e.g. databuilder:v1)",
    )
    parser.add_argument(
        "docker_args",
        nargs=argparse.REMAINDER,
        metavar="...",
        help="Any additional arguments to pass to the image",
    )
    return parser


def main(image, docker_args):
    if not docker_preflight_check():
        return False

    try:
        # In order for any files that get created to have the appropriate owner/group we
        # run the command using the current user's UID/GID
        uid = os.getuid()
        gid = os.getgid()
    except Exception:
        # These aren't available on Windows; but then on Windows we don't have to deal
        # with the same file ownership problems which require us to match the UID in the
        # first place.
        user_args = []
    else:
        user_args = ["--user", f"{uid}:{gid}"]

    proc = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            *user_args,
            f"{config.DOCKER_REGISTRY}/{image}",
            *docker_args,
        ]
    )
    return proc.returncode == 0
