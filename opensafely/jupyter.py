import json
import os
import subprocess
import sys
import time
from pathlib import Path

from opensafely import utils
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check


DESCRIPTION = "Run a jupyter lab notebook using the OpenSAFELY environment"


def add_arguments(parser):
    parser.add_argument(
        "--directory",
        "-d",
        default=os.getcwd(),
        type=Path,
        help="Directory to run the jupyter server in (default is current dir)",
    )
    parser.add_argument(
        "--name",
        help="Name of docker image (defaults to use directory name)",
    )

    # we copy a number of standard jupyter lab arguments, and capture them to handle them ourselves
    parser.add_argument(
        "--no-browser",
        "-n",
        default=False,
        action="store_true",
        help="Do not attempt to open a browser",
    )
    parser.add_argument(
        "--port",
        "-p",
        default=None,
        help="Port to run on (random by default)",
    )


def get_metadata(name, timeout=30.0):
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
        utils.debug("get_metadata: Could not get jupyter metadata")
        utils.debug(ps.stderr)
        return None

    return metadata


def read_metadata_and_open(name, port):
    try:
        metadata = get_metadata(name)
        if metadata:
            url = f"http://localhost:{port}/?token={metadata['token']}"
            utils.open_browser(url)
        else:
            utils.debug("could not retrieve login token from jupyter container")
    except Exception:
        utils.print_exception_from_thread(*sys.exc_info())


def main(directory, name, port, no_browser):
    if not docker_preflight_check():
        return False

    if name is None:
        name = f"os-jupyter-{directory.name}"

    if port is None:
        port = str(utils.get_free_port())

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
        utils.open_in_thread(read_metadata_and_open, (name, port))

    utils.debug("docker: " + " ".join(docker_args))

    ps = utils.run_docker(
        docker_args, "python", jupyter_cmd, interactive=True, directory=directory
    )

    # we want to exit with the same code that jupyter did
    return ps.returncode
