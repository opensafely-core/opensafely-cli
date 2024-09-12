import pathlib

from opensafely import rstudio
from tests.conftest import run_main


def test_rstudio(run, no_user):
    run.expect(
        [
            "docker",
            "run",
            "--rm",
#            "--label=opensafely",
            "--interactive",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "-p=8787:8787",
            "--name=test_rstudio",
            "--hostname=test_rstudio",
            "rstudio", # "ghcr.io/opensafely-core/rstudio",
        ]
    )

    assert run_main(rstudio, "--port 8787 --name test_rstudio --no-browser foo") == 0
