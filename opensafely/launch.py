import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from opensafely import utils
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check


DESCRIPTION = "Launch an RStudio Server or Jupyter Lab session in a browser"


def add_base_args(parser):
    parser.add_argument(
        "--directory",
        "-d",
        default=os.getcwd(),
        type=Path,
        help="Directory to run the RStudio Server session in (default is current dir)",
    )
    parser.add_argument(
        "--name", help="Name of docker container (defaults to use directory name)"
    )
    parser.add_argument(
        "--port",
        "-p",
        default=None,
        help="Port to run on (random by default)",
    )
    parser.add_argument(
        "--no-browser",
        "-n",
        default=False,
        action="store_true",
        help="Do not attempt to open a browser",
    )


def add_arguments(parser):
    parser.add_argument(
        "tool",
        help="Tool to launch e.g. rstudio",
    )
    add_base_args(parser)


def main(tool, directory, name, port, no_browser):

    if tool == "rstudio":
        func = launch_rstudio
    elif tool == "jupyter":
        func = launch_jupyter
    else:
        raise argparse.ArgumentTypeError(
            f"{tool} is not a recognised tool to launch. Choose from rstudio, jupyter"
        )

    if not docker_preflight_check():
        return False

    if name is None:
        name = f"os-{tool}-{directory.name}"

    if port is None:
        port = str(utils.get_free_port())

    return func(directory, name, port, no_browser)


def get_jupyter_metadata(name, timeout=30.0):
    """Read the login token from the generated json file in the container"""
    metadata = None
    metadata_path = "/tmp/.local/share/jupyter/runtime/*server-*.json"

    # wait for jupyter to be set up
    start = time.time()
    while metadata is None and time.time() - start < timeout:
        ps = subprocess.run(
            ["docker", "exec", name, "bash", "-c", f"cat {metadata_path}"],
            text=True,
            capture_output=True,
        )
        if ps.returncode == 0:
            utils.debug(ps.stdout)
            metadata = json.loads(ps.stdout)
        else:
            time.sleep(1)

    if metadata is None:
        utils.debug("get_jupyter_metadata: Could not get metadata")
        return None

    return metadata


def read_jupyter_metadata_and_open(name, port):
    try:
        metadata = get_jupyter_metadata(name)
        if metadata:
            url = f"http://localhost:{port}/?token={metadata['token']}"
            utils.open_browser(url)
        else:
            utils.debug("could not retrieve login token from jupyter container")
    except Exception:
        utils.print_exception_from_thread(*sys.exc_info())


def launch_jupyter(directory, name, port, no_browser):
    jupyter_cmd = [
        "jupyter",
        "lab",
        "--ip=0.0.0.0",
        f"--port={port}",
        "--allow-root",
        "--no-browser",
        # display the url from the hosts perspective
        f"--LabApp.custom_display_url=http://localhost:{port}/",
    ]

    print(f"Running following jupyter cmd in OpenSAFELY docker container {name}...")
    print(" ".join(jupyter_cmd))

    docker_args = [
        # we use our port on both sides of the docker port mapping so that
        # jupyter's logging uses the correct port from the user's perspective
        f"-p={port}:{port}",
        f"--name={name}",
        f"--hostname={name}",
        "--env",
        "HOME=/tmp",
        # allow importing from the top level
        "--env",
        "PYTHONPATH=/workspace",
    ]

    if not no_browser:
        utils.open_in_thread(read_jupyter_metadata_and_open, (name, port))

    utils.debug("docker: " + " ".join(docker_args))

    ps = utils.run_docker(
        docker_args, "python", jupyter_cmd, interactive=True, directory=directory
    )

    # we want to exit with the same code that jupyter did
    return ps.returncode


def launch_rstudio(directory, name, port, no_browser):
    url = f"http://localhost:{port}"

    if sys.platform == "linux":
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
        f"--env=HOSTPLATFORM={sys.platform}",
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

    if not no_browser:
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
