import pathlib
import os

from opensafely import rstudio
from tests.conftest import run_main


def test_rstudio(run):
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--interactive",
            "--user=0:0",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--platform=linux/amd64",
            "-p=8787:8787",
            "--name=test_rstudio",
            "--hostname=test_rstudio",
            "--volume=" + os.path.join(os.path.expanduser('~'), ".gitconfig") + ":/home/rstudio/local-gitconfig",
            "--env=HOST=" + os.name,
            "ghcr.io/opensafely-core/rstudio",
        ]
    )

    assert run_main(rstudio, "--port 8787 --name test_rstudio") == 0
