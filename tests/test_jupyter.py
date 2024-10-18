import pathlib

from opensafely import jupyter
from tests.conftest import run_main


def test_jupyter(run, no_user):
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--platform=linux/amd64",
            "--interactive",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "-p=1234:1234",
            "--name=test_jupyter",
            "--hostname=test_jupyter",
            "--env",
            "HOME=/tmp",
            "--env",
            "PYTHONPATH=/workspace",
            "ghcr.io/opensafely-core/python",
            "jupyter",
            "lab",
            "--ip=0.0.0.0",
            "--port=1234",
            "--allow-root",
            "--no-browser",
            # display the url from the hosts perspective
            "--LabApp.custom_display_url=http://localhost:1234/",
            "foo",
        ]
    )

    assert run_main(jupyter, "--port 1234 --name test_jupyter --no-browser foo") == 0
