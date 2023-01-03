import argparse

from opensafely import utils
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check


DESCRIPTION = "Run an OpenSAFELY action outside of the `project.yaml` pipeline"


def add_arguments(parser):
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


def main(image, cmd_args):
    if not docker_preflight_check():
        return False

    proc = utils.run_docker([], image, cmd_args, interactive=True)
    return proc.returncode
