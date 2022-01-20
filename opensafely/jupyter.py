import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib import request

DESCRIPTION = "Run a jupyter lab notebook using the OpenSAFELY environment"


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
        help="Port to run on",
    )
    # opt into looser argument parsing
    parser.set_defaults(handles_unknown_args=True)


def ensure_tty(docker_cmd):
    """Ensure that we have a valid tty to use to run docker.

    This is needed as we want the user to be able to kill jupyter with Ctrl-C
    as normal, which requires a tty on their end.

    Nearly every terminal under the sun gives you a valid tty. Except
    git-bash's default terminal, which happens to be the one a lot of our users
    use.

    git-bash provides the `wintpy` tool as a workaround, so detect we are in
    that situation and use it if so.
    
    """
    if platform.system() != "Windows":
        return docker_cmd

    winpty = shutil.which("winpty")
    
    if winpty is None:
        # not git-bash
        return docker_cmd

    if sys.stdin.isatty() and sys.stdout.isatty():
        # already sorted, possibly user already ran us with winpty
        return docker_cmd

    debug(f"detected no tty, found winpty at {winpty}, wrapping docker with it")
    # avoid using explicit path, as it can trip things up.
    return ["winpty", "--"] + docker_cmd


def open_browser(name, port):

    try:
        metadata = None
        metadata_path = "/root/.local/share/jupyter/runtime/nbserver-*.json"

        # wait for jupyter to be set up
        start = time.time()
        while metadata is None and time.time() - start < 120.0:
            ps = subprocess.run(
                ["docker", "exec", name, "bash", "-c", f"cat {metadata_path}"],
                text=True,
                capture_output=True,
            )
            if ps.returncode == 0:
                debug(ps.stdout)
                metadata = json.loads(ps.stdout)
            else:
                time.sleep(1)

        if metadata is None:
            debug("open_browser: Could not get metadata")
            return

        url = f"http://localhost:{port}/?token={metadata['token']}"
        debug(f"open_browser: url={url}")

        # wait for port to be open
        debug("open_browser: waiting for port")
        start = time.time()
        while time.time() - start < 60.0:
            try:
                response = request.urlopen(url, timeout=1)
            except (request.URLError, socket.error):
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
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main(directory, name, port, no_browser, unknown_args):
    if name is None:
        name = f"os-jupyter-{directory.name}"

    if port is None:
        # this is a race condition, as something else could consume the socket
        # before docker binds to it, but the chance of that on a user's
        # personal machine is very small.
        port = str(get_free_port())

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

    if not no_browser:
        # start thread to open web browser
        thread = threading.Thread(target=open_browser, args=(name, port), daemon=True)
        thread.name = "browser thread"
        debug("starting open_browser thread")
        thread.start()

    docker_cmd = [
        "docker",
        "run",
        # running with -t gives us colors and Ctrl-C interupts.
        "-it",
        "--rm",
        "--init",
        # we use our port on both sides of the docker port mapping so that
        # jupyter has all the info
        f"-p={port}:{port}",
        f"--name={name}",
        f"--hostname={name}",
        "--label=opensafely",
        # note: // is to avoid git-bash path translation
        f"-v={directory.resolve()}://workspace",
        "ghcr.io/opensafely-core/python",
    ]

    docker_cmd = ensure_tty(docker_cmd)

    debug("docker: " + " ".join(docker_cmd))
    ps = subprocess.Popen(docker_cmd + jupyter_cmd)
    ps.wait()
    sys.exit(ps.returncode)
