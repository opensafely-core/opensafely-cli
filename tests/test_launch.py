import os
import pathlib
from sys import platform
from unittest import mock

import pytest

from opensafely import launch, utils
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
            "cat /tmp/.local/share/jupyter/runtime/*server-*.json",
        ],
        stdout='{"token": "TOKEN"}',
    )

    assert run_main(launch, "jupyter --port 1234 --name test_jupyter") == 0
    mock_open_browser.assert_called_with("http://localhost:1234/?token=TOKEN")


@pytest.mark.parametrize("gitconfig_exists", [True, False])
def test_rstudio(run, tmp_path, monkeypatch, gitconfig_exists):

    home = tmp_path / "home"
    home.mkdir()
    # linux/macos
    monkeypatch.setitem(os.environ, "HOME", str(home))
    # windows
    monkeypatch.setitem(os.environ, "USERPROFILE", str(home))

    # mock the open_browser call
    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(utils, "open_browser", mock_open_browser)

    if gitconfig_exists:
        (home / ".gitconfig").touch()

    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    run.expect(["docker", "info"])

    run.expect(["docker", "image", "inspect", "ghcr.io/opensafely-core/rstudio:latest"])

    expected = [
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
        "--env=HOSTPLATFORM=" + platform,
        f"--env=HOSTUID={uid}",
    ]

    if gitconfig_exists:
        expected.append(
            "--volume="
            + os.path.join(os.path.expanduser("~"), ".gitconfig")
            + ":/home/rstudio/local-gitconfig",
        )

    run.expect(expected + ["ghcr.io/opensafely-core/rstudio"])

    assert run_main(launch, "rstudio --port 8787 --name test_rstudio") == 0
    mock_open_browser.assert_called_with("http://localhost:8787")
