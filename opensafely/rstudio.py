import os
from pathlib import Path
from sys import platform

from opensafely import utils


DESCRIPTION = "Run an RStudio Server session using the OpenSAFELY environment"


def add_arguments(parser):
    parser.add_argument(
        "--directory",
        "-d",
        default=os.getcwd(),
        type=Path,
        help="Directory to run the RStudio Server session in (default is current dir)",
    )
    parser.add_argument(
        "--name", help="Name of docker image (defaults to use directory name)"
    )

    parser.add_argument(
        "--port",
        "-p",
        default=None,
        help="Port to run on",
    )


def main(directory, name, port):
    if name is None:
        name = f"os-rstudio-{directory.name}"

    if port is None:
        port = str(utils.get_free_port())

    url = f"http://localhost:{port}"

    # Determine if on Linux, if so obtain user id
    # And need to know in Windows win32 for text file line endings setting
    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    docker_args = [
        f"-p={port}:8787",
        f"--name={name}",
        f"--hostname={name}",
        "--volume="
        + os.path.join(os.path.expanduser("~"), ".gitconfig")
        + ":/home/rstudio/local-gitconfig",
        f"--env=HOSTPLATFORM={platform}",
        f"--env=HOSTUID={uid}",
    ]

    utils.debug("docker: " + " ".join(docker_args))
    print(
        f"Opening an RStudio Server session at http://localhost:{port}/ when "
        "you are finished working please press Ctrl+C here to end the session"
    )

    utils.open_in_thread(utils.open_browser, (url,))

    ps = utils.run_docker(
        docker_args, "rstudio", "", interactive=True, user="0:0", directory=directory
    )

    # we want to exit with the same code that rstudio-server did
    return ps.returncode
