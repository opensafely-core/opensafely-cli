import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib import request

DESCRIPTION = "Run a jupyter notebook using the OpenSAFELY environment"


def add_arguments(parser):
    pass


def open_browser(name):

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
        url = f"http://{ip}:8888"

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


def main():
    container = None
    pwd = Path(os.getcwd())
    name = f"opensafely-notebook-{pwd.name}"

    # start thread to open web browser
    thread = threading.Thread(target=open_browser, args=(name,), daemon=True)
    thread.start()

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
        "exec jupyter lab --ip 0.0.0.0 --allow-root --no-browser --LabApp.token= --LabApp.custom_display_url=http:/$(hostname -i):8888",
    ]

    ps = subprocess.Popen(docker_args)
    ps.wait()
