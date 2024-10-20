import os
import subprocess
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
        help="Port to run on (random by default)",
    )


def main(directory, name, port):
    if name is None:
        name = f"os-rstudio-{directory.name}"

    if port is None:
        port = str(utils.get_free_port())

    url = f"http://localhost:{port}"

    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    # check for rstudio image, if not present pull image
    imgchk = subprocess.run(
        ["docker", "image", "inspect", "ghcr.io/opensafely-core/rstudio:latest"],
        capture_output=True,
    )
    if imgchk.returncode == 1:
        subprocess.run(
            [
                "docker",
                "pull",
                "--platform=linux/amd64",
                "ghcr.io/opensafely-core/rstudio:latest",
            ],
            check=True,
        )

    docker_args = [
        f"-p={port}:8787",
        f"--name={name}",
        f"--hostname={name}",
        f"--env=HOSTPLATFORM={platform}",
        f"--env=HOSTUID={uid}",
    ]

    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.exists():
        docker_args.append(f"--volume={gitconfig}:/home/rstudio/local-gitconfig")

    utils.debug("docker: " + " ".join(docker_args))
    print(
        f"Opening an RStudio Server session at {url}. "
        "When you are finished working please press Ctrl+C here to end the session"
    )

    utils.open_in_thread(utils.open_browser, (url,))

    ps = utils.run_docker(
        docker_args,
        image="rstudio",
        interactive=True,
        # rstudio needs to start as root, but drops privileges to uid later
        user="0:0",
        directory=directory,
    )

    # we want to exit with the same code that rstudio-server did
    return ps.returncode
