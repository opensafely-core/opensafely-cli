import argparse
import os
import secrets
import sys
from pathlib import Path

from opensafely import utils
from opensafely._vendor.jobrunner.cli.local_run import docker_preflight_check
from opensafely.pull import REGISTRY


DESCRIPTION = "Launch an RStudio Server or Jupyter Lab session in a browser"


def add_base_args(parser):
    parser.add_argument(
        "--directory",
        "-d",
        default=os.getcwd(),
        type=Path,
        help="Directory to run the tool from (default is current dir)",
    )
    parser.add_argument(
        "--name", help="Name of docker container (defaults to use directory name)"
    )
    parser.add_argument(
        "--port",
        "-p",
        default=None,
        type=int,
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
    parser.add_argument(
        "--force",
        "-f",
        default=False,
        action="store_true",
        help="Force a new version of the tool to run",
    )


def add_arguments(parser):
    parser.add_argument(
        "tool",
        help="Tool to launch e.g. rstudio",
    )
    add_base_args(parser)


def main(tool, directory, name, port, no_browser, background, force):

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

    # does the container for this tool/workspace already exist?
    ps = utils.dockerctl("inspect", name, check=False)
    if ps.returncode == 0:
        if force:
            # rename the current container, then stop it. Docker will clean it
            # up, and we free to reuse the name immeadiately
            old = name + "_deleting"
            utils.dockerctl("rename", name, old)
            utils.dockerctl("stop", old)
        else:  # re-use
            # check the label for url information
            url = utils.dockerctl(
                "inspect", "-f", '{{index .Config.Labels "url"}}', name
            ).stdout.strip()
            print(f"{tool_name} is already running at {url}")
            print("Use --force to force to remove it and start a new instance")
            if not no_browser:
                print(f"Opening browser at {url}")
                utils.open_browser(url)
            return 0

    return func(version, directory, name, port, no_browser, background)


def launch_jupyter(version, directory, name, port, no_browser, background):

    if not version:
        version = "v2"

    if port is None:
        # 8888 is default jupyter port
        port = utils.get_free_port(8888)

    token = secrets.token_urlsafe(8)
    url = f"http://localhost:{port}/?token={token}"

    jupyter_cmd = [
        "jupyter",
        "lab",
        "--ip=0.0.0.0",
        f"--port={port}",
        "--no-browser",  # we open the browser
        # display the url from the hosts perspective
        f"--ServerApp.custom_display_url=http://localhost:{port}/",
        "-y",  # do not ask for confirmation on quitting
        "--Application.log_level=ERROR",  # only log errors
    ]

    utils.debug(" ".join(jupyter_cmd))

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
        # store label for later use
        f"--label=url={url}",
    ]

    image = f"python:{version}"
    ensure_image(image)
    kwargs = dict(
        image=image,
        cmd=jupyter_cmd,
        directory=directory,
    )

    print(f"Starting a Jupyter Lab session at {url}.")
    return run_tool(docker_args, kwargs, background, no_browser, url)


def launch_rstudio(version, directory, name, port, no_browser, background):
    if not version:
        version = "v2"

    if port is None:
        # temporary hack to work around codespaces already running at 8787
        default_rstudio_port = 8788 if "CODESPACES" in os.environ else 8787
        port = utils.get_free_port(default_rstudio_port)

    url = f"http://localhost:{port}"

    if sys.platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    docker_args = [
        f"-p={port}:8787",
        f"--name={name}",
        f"--hostname={name}",
        # needed for rstudio user management
        f"--env=HOSTPLATFORM={sys.platform}",
        f"--env=HOSTUID={uid}",
        # store label for later use
        f"--label=url={url}",
    ]

    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.exists():
        docker_args.append(f"--volume={gitconfig}:/home/rstudio/local-gitconfig")

    image = f"rstudio:{version}"
    ensure_image(image)
    kwargs = dict(
        image=image,
        # rstudio needs to start as root, but drops privileges to uid later
        user="0:0",
        directory=directory,
    )

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


def ensure_image(image):
    """Ensure we have an image locally, and download it if not

    If we download, we show we are downloading to the user.
    """
    # When using launch, if we do not have image locally, it can take a while
    # to download.  While the `docker run ...` command would download it
    # automatically, this can take so long that the open browser thread times
    # out. Additionally this means that if running with --backround, the user
    # cannot see we are downloading the image and it looks like we've just
    # hung.
    #
    # So, instead, we eagerly ensure it is present before proceeding, so that
    # we are not blocked, and we show this download to the user.
    qualified_image = f"{REGISTRY}/{image}"
    ps = utils.dockerctl("image", "inspect", qualified_image, check=False)
    if ps.returncode != 0:
        utils.dockerctl("pull", qualified_image, capture_output=False)
