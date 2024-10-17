import os
import pathlib
from sys import platform

from opensafely import rstudio
from tests.conftest import run_main


def test_rstudio(run):
    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--platform=linux/amd64",
            "--interactive",
            "--user=0:0",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "-p=8787:8787",
            "--name=test_rstudio",
            "--hostname=test_rstudio",
            "--volume="
            + os.path.join(os.path.expanduser("~"), ".gitconfig")
            + ":/home/rstudio/local-gitconfig",
            "--env=HOSTPLATFORM=" + platform,
            f"--env=HOSTUID={uid}",
            "ghcr.io/opensafely-core/rstudio",
        ]
    )

    assert run_main(rstudio, "--port 8787 --name test_rstudio") == 0
