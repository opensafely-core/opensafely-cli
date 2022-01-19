import json
import os
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


def open_browser(name, port):

    # because debugging threads is hard
    if os.environ.get("DEBUG", False):

        def debug(msg):
            # threaded output for some reason needs the carriage return or else
            # it doesn't reset the cursor.
            msg = msg.replace("\n", "\r\n")
            sys.stderr.write(f"open_browser: {msg}" + "\r\n")
            sys.stderr.flush()

    else:

        def debug(msg):
            pass

    try:
        metadata = None
        metadata_path = "/root/.local/share/jupyter/runtime/nbserver-*.json"

        # wait for jupyter to be set up
        start = time.time()
        while metadata is None and time.time() - start < 30.0:
            ps = subprocess.run(
                ["docker", "exec", name, "bash", "-c", f"cat {metadata_path}"],
                text=True,
                capture_output=True,
            )
            if ps.returncode == 0:
                debug(ps.stdout)
                metadata = json.loads(ps.stdout)
            else:
                time.sleep(0.5)

        if metadata is None:
            debug("Could not get metadata")
            return

        url = f"http://localhost:{port}/?token={metadata['token']}"
        debug(f"url={url}")

        # wait for port to be open
        debug("waiting for port")
        start = time.time()
        while time.time() - start < 30.0:
            try:
                response = request.urlopen(url, timeout=0.5)
            except (request.URLError, socket.error):
                pass
            else:
                break

        if not response:
            debug("open_browser: could not get response")
            return

        # open a webbrowser pointing to the docker container
        debug("open_browser: opening browser window")
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
        thread.start()

    docker_args = [
        "docker",
        "run",
        "-it",
        "--rm",
        "--init",
        # we use our port on both sides of the docker port mapping so that
        # jupyter has all the info
        f"-p={port}:{port}",
        f"--name={name}",
        f"--hostname={name}",
        "--label=opensafely",
        # note: on windows this will preserve drive letter, but switch to unix
        # separators, which is what docker understands
        f"-v={directory.resolve().as_posix()}:/workspace",
        "ghcr.io/opensafely-core/python",
    ]

    # on windows, we need to wrap command in winpty to for docker run -it
    winpty = shutil.which("winpty")
    if winpty:
        docker_args = [winpty] + docker_args

    ps = subprocess.Popen(docker_args + jupyter_cmd)
    ps.wait()
