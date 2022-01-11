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


def add_arguments(parser):
    # we copy a number of standard jupyter lab arguments, and capture them to handle them ourselves
    parser.add_argument(
        "--no-browser",
        default=False,
        action="store_true",
        help="Do not attempt to open a browser",
    )
    parser.add_argument(
        "--port",
        default="8888",
        help="Port to run on",
    )
    # opt into looser argument parsing
    return True


def open_browser(name, port):

    try:
        # wait for container to be up
        while True:
            ps = subprocess.run(
                ["docker", "inspect", name],
                capture_output=True,
                universal_newlines=True,
            )
            if ps.returncode == 0:
                break
            time.sleep(0.5)

        # figure out the url
        metadata = json.loads(ps.stdout)[0]
        ip = metadata["NetworkSettings"]["IPAddress"]
        url = f"http://{ip}:{port}"

        # wait for port to be open
        while True:
            try:
                response = request.urlopen(url, timeout=0.5)
            except request.URLError:
                pass
            else:
                break

        # open a webbrowser pointing to the docker container
        webbrowser.open(url, new=2)

    except Exception as exc:
        print(exc)


def main(port, no_browser, unknown_args):
    container = None
    pwd = Path(os.getcwd())
    name = f"opensafely-notebook-{pwd.name}"

    if not no_browser:
        # start thread to open web browser
        thread = threading.Thread(target=open_browser, args=(name, port), daemon=True)
        thread.name = "browser thread"
        thread.start()

    base_cmd = f"jupyter lab --ip 0.0.0.0 --port={port} --allow-root --no-browser --LabApp.token= --LabApp.custom_display_url=http://$(hostname -i):{port}"
    jupyter_cmd = base_cmd + " " + " ".join(unknown_args)

    print("Running jupyter with OpenSAFELY python image:")
    print(jupyter_cmd)

    docker_args = [
        "docker",
        "run",
        "--rm",
        "--init",
        "-it",
        f"--name={name}",
        f"--hostname={name}",
        "--label=opensafely",
        f"-v=/{pwd}:/workspace",
        "ghcr.io/opensafely-core/python",
        # we wrap the jupyter command in a bash invocation, so we can use
        # hostname -i to find out the containers IP address, which allows us to
        # set the correct url to show in the output.
        "bash",
        "-c",
        "exec " + jupyter_cmd,
    ]

    ps = subprocess.Popen(docker_args)
    ps.wait()
