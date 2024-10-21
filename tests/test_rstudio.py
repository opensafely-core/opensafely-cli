import os
import pathlib
from sys import platform
from unittest import mock

import pytest

from opensafely import rstudio, utils
from tests.conftest import run_main


@pytest.mark.parametrize("gitconfig_exists", [True, False])
def test_rstudio(run, tmp_path, monkeypatch, gitconfig_exists):

    home = tmp_path / "home"
    home.mkdir()
    # linux/macos
    monkeypatch.setitem(os.environ, "HOME", str(home))
    # windows
    monkeypatch.setitem(os.environ, "USERPROFILE", str(home))

    # mock the webbrowser.open call
    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(utils, "open_browser", mock_open_browser)

    if gitconfig_exists:
        (home / ".gitconfig").touch()

    if platform == "linux":
        uid = os.getuid()
    else:
        uid = None

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

    assert run_main(rstudio, "--port 8787 --name test_rstudio") == 0
    mock_open_browser.assert_called_with("http://localhost:8787")
