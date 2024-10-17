import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from sys import platform
from urllib import request

from opensafely import utils


DESCRIPTION = "Run an RStudio Server session using the OpenSAFELY environment"


# poor mans debugging because debugging threads on windows is hard
if os.environ.get("DEBUG", False):

    def debug(msg):
        # threaded output for some reason needs the carriage return or else
        # it doesn't reset the cursor.
        sys.stderr.write("DEBUG: " + msg.replace("\n", "\r\n") + "\r\n")
        sys.stderr.flush()

else:

    def debug(msg):
        pass


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


def open_browser(name, port):
    try:
        url = f"http://localhost:{port}"
        debug(f"open_browser: url={url}")

        # wait for port to be open
        debug("open_browser: waiting for port")
        start = time.time()
        while time.time() - start < 60.0:
            try:
                response = request.urlopen(url, timeout=1)
            except (request.URLError, OSError):
                pass
            else:
                break

        if not response:
            debug("open_browser: open_browser: could not get response")
            return

        # open a webbrowser pointing to the docker container
        debug("open_browser: open_browser: opening browser window")
        webbrowser.open(url, new=2)

    except Exception:
        # reformat exception printing to work from thread
        import traceback

        sys.stderr.write("Error in open browser thread:\r\n")
        tb = traceback.format_exc().replace("\n", "\r\n")
        sys.stderr.write(tb)
        sys.stderr.flush()


def get_free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main(directory, name, port):
    if name is None:
        name = f"os-rstudio-{directory.name}"

    if port is None:
        # this is a race condition, as something else could consume the socket
        # before docker binds to it, but the chance of that on a user's
        # personal machine is very small.
        port = str(get_free_port())

    # if not no_browser:
    # start thread to open web browser
    thread = threading.Thread(target=open_browser, args=(name, port), daemon=True)
    thread.name = "browser thread"
    debug("starting open_browser thread")
    thread.start()

    # Determine if on Linux, if so obtain user id
    # And need to know in Windows win32 for text file line endings setting
    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    docker_args = [
        "--platform=linux/amd64",
        f"-p={port}:8787",
        f"--name={name}",
        f"--hostname={name}",
        "--volume="
        + os.path.join(os.path.expanduser("~"), ".gitconfig")
        + ":/home/rstudio/local-gitconfig",
        f"--env=HOSTPLATFORM={platform}",
        f"--env=HOSTUID={uid}",
    ]

    debug("docker: " + " ".join(docker_args))
    print(
        f"Opening an RStudio Server session at http://localhost:{port}/ when "
        "you are finished working please press Ctrl+C here to end the session"
    )
    ps = utils.run_docker(
        docker_args, "rstudio", "", interactive=True, user="0:0", directory=directory
    )
    # we want to exit with the same code that rstudio-server did
    return ps.returncode
