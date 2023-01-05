import argparse
import os

from opensafely import utils
from opensafely._vendor.jobrunner.cli.local_run import (
    STATA_ERROR_MESSGE,
    docker_preflight_check,
    get_stata_license,
)


DESCRIPTION = "Run an OpenSAFELY action outside of the `project.yaml` pipeline"


def add_arguments(parser):
    # these three arguments are direct copies of docker run arguments. The must be
    # supplied before the image name, just like docker run.
    parser.add_argument("--entrypoint", default=None, help="Set docker entrypoint")
    parser.add_argument("--env", "-e", action="append", default=[], help="Set env vars")
    parser.add_argument(
        "--user",
        "-u",
        help=f"Unix user/group to run as (uid:gid). Defaults to current uid/gid {utils.DEFAULT_USER}",
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

    docker_args = []
    cmd_env = environ.copy()

    # let user disable default uid:gid usage on linux (e.g. rootless docker)
    if user and user.lower() in ("none", "no", "false"):
        user = False

    docker_args.extend(["--env", "OPENSAFELY_BACKEND=expectations"])

    for e in env:
        docker_args.extend(["--env", e])

    if image.startswith("stata"):
        if "STATA_LICENSE" not in cmd_env:
            license = get_stata_license()
            if license is None:
                print(STATA_ERROR_MESSGE)
                return False
            else:
                cmd_env["STATA_LICENSE"] = license

        docker_args.extend(["--env", "STATA_LICENSE"])

    if entrypoint:
        docker_args.append(f"--entrypoint={entrypoint}")

    proc = utils.run_docker(
        docker_args, image, cmd_args, interactive=True, user=user, env=cmd_env
    )
    return proc.returncode
