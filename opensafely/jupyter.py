import argparse
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib import request

DESCRIPTION = "Run a jupyter lab notebook using the OpenSAFELY environment"


# quick and directy debugging hack, as due to threads and windos this is tricky
# to debug

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
        default="8888",
        help="Port to run on",
    )
    # opt into looser argument parsing
    parser.set_defaults(handles_unknown_args=True)


def open_browser(name, port):

    if os.environ.get("DEBUG", False):
        def debug(msg):
            sys.stderr.write(msg + "\r\n")
            sys.stderr.flush()
    else:
        def debug(msg):
            pass

    try:
        # wait for container to be up
        debug("open_browser: waiting for container")
        while True:
            ps = subprocess.run(
                ["docker", "inspect", name],
                capture_output=True,
                text=True,
            )
            if ps.returncode == 0:
                break
            time.sleep(0.5)

        # figure out the url
        metadata = json.loads(ps.stdout)[0]
        debug(json.dumps(metadata, indent=2).replace("\n", "\r\n"))
        ip = metadata["NetworkSettings"]["IPAddress"]
        url = f"http://{ip}:{port}"
        debug(f"open_browser: url={url}")

        # wait for port to be open
        debug("open_browser: waiting for port")
        while True:
            try:
                response = request.urlopen(url, timeout=0.5)
            except request.URLError:
                pass
            else:
                break

        # open a webbrowser pointing to the docker container
        debug("open_browser: opening browser window")
        webbrowser.open(url, new=2)

    except Exception as exc:
        print(exc)

    debug("open_browser: done")


def main(directory, name, port, no_browser, unknown_args):
    container = None
    if name is None:
        name = f"os-jupyter-{directory.name}"

    if not no_browser:
        # start thread to open web browser
        thread = threading.Thread(target=open_browser, args=(name, port), daemon=True)
        thread.name = "browser thread"
        thread.start()

    base_cmd = f"jupyter lab --ip 0.0.0.0 --port={port} --allow-root --no-browser"
    extra_args = (
        f" --LabApp.token= --LabApp.custom_display_url=http://$(hostname -i):{port}"
    )
    jupyter_cmd = base_cmd + " " + " ".join(unknown_args)

    docker_args = [
        "docker",
        "run",
        "--rm",
        "--init",
        "-it",
        f"--name={name}",
        f"--hostname={name}",
        "--label=opensafely",
        # note: on windows this will preserve drive letter, but swtitch to unix
        # separators, which is what docker understands
        f"-v={directory.resolve().as_posix()}:/workspace",
        "ghcr.io/opensafely-core/python",
        # we wrap the jupyter command in a bash invocation, so we can use
        # hostname -i to find out the containers IP address, which allows us to
        # set the correct url to show in the output.
        "bash",
        "-c",
        "exec " + jupyter_cmd + extra_args,
    ]

    print(f"Running following jupyter cmd in OpenSAFELY docker container {name}...")
    print(jupyter_cmd)

    ps = subprocess.Popen(docker_args)
    ps.wait()
