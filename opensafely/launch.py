import argparse
import os
import secrets
import subprocess
import sys
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
    parser.add_argument(
        "--background",
        "-b",
        default=False,
        action="store_true",
        help="Run docker container in background",
    )


def add_arguments(parser):
    parser.add_argument(
        "tool",
        help="Tool to launch e.g. rstudio",
    )
    add_base_args(parser)


def main(tool, directory, name, port, no_browser, background):

    tool_name, _, version = tool.partition(":")

    if tool_name == "rstudio":
        func = launch_rstudio
    elif tool_name == "jupyter":
        func = launch_jupyter
    else:
        raise argparse.ArgumentTypeError(
            f"{tool_name} is not a recognised tool to launch. Choose from rstudio, jupyter"
        )

    if not docker_preflight_check():
        return False

    if name is None:
        name = f"os-{tool_name}-{directory.name}"

    if port is None:
        port = str(utils.get_free_port())

    return func(version, directory, name, port, no_browser, background)


def launch_jupyter(version, directory, name, port, no_browser, background):

    if not version:
        version = "v2"

    token = secrets.token_urlsafe(8)
    url = f"http://localhost:{port}/?token={token}"

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
        # fix the token ahead of time
        "--env",
        f"JUPYTER_TOKEN={token}",
    ]

    kwargs = dict(
        image=f"python:{version}",
        cmd=jupyter_cmd,
        directory=directory,
    )

    print(f"Starting a Jupyter Lab session at {url}.")
    return run_tool(docker_args, kwargs, background, no_browser, url)


def launch_rstudio(version, directory, name, port, no_browser, background):
    if not version:
        version = "v2"

    url = f"http://localhost:{port}"

    if sys.platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    # check for rstudio image, if not present pull image
    imgchk = subprocess.run(
        ["docker", "image", "inspect", f"ghcr.io/opensafely-core/rstudio:{version}"],
        capture_output=True,
    )
    if imgchk.returncode == 1:
        subprocess.run(
            [
                "docker",
                "pull",
                "--platform=linux/amd64",
                f"ghcr.io/opensafely-core/rstudio:{version}",
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

    kwargs = dict(
        image=f"rstudio:{version}",
        # rstudio needs to start as root, but drops privileges to uid later
        user="0:0",
        directory=directory,
    )

    utils.debug("docker: " + " ".join(docker_args))
    print(f"Opening an RStudio Server session at {url}.")
    return run_tool(docker_args, kwargs, background, no_browser, url)


def run_tool(docker_args, kwargs, background, no_browser, url):
    if background:
        kwargs["detach"] = True
        kwargs["capture_output"] = True
        kwargs["text"] = True
    else:
        kwargs["interactive"] = True
        print(
            "When you are finished working please press Ctrl+C here to end the session."
        )
        # running in foreground, so use thread to open browser
        if not no_browser:
            utils.open_in_thread(utils.open_browser, (url,))

    ps = utils.run_docker(docker_args, **kwargs)

    if background:
        if ps.returncode == 0:
            if not no_browser:
                utils.open_browser(url)
        else:
            print(ps.stdout)
            print(ps.stderr, file=sys.stderr)

    # we want to exit with the same code that docker did
    return ps.returncode
