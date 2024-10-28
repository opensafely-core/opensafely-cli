import pathlib
from unittest import mock

from opensafely import jupyter, utils
from tests.conftest import run_main


def test_jupyter(run, no_user, monkeypatch):
    # easier to monkeypatch open_browser that try match the underlying
    # subprocess calls.
    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(utils, "open_browser", mock_open_browser)

    # these calls are done in different threads, so can come in any order
    run.concurrent = True

    run.expect(["docker", "info"])

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
    # fetch the metadata
    run.expect(
        [
            "docker",
            "exec",
            "test_jupyter",
            "bash",
            "-c",
            "cat /tmp/.local/share/jupyter/runtime/nbserver-*.json",
        ],
        stdout='{"token": "TOKEN"}',
    )

    assert run_main(jupyter, "--port 1234 --name test_jupyter foo") == 0
    mock_open_browser.assert_called_with("http://localhost:1234/?token=TOKEN")
