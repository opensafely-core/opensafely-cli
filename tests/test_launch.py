import os
import pathlib
import secrets
import sys
from unittest import mock

import pytest

from opensafely import launch, utils
from tests.conftest import run_main


@pytest.mark.parametrize("version", ["", "v2"])
def test_jupyter(run, no_user, monkeypatch, version):

    if not version:
        tool = "jupyter"
        used_version = "v2"
    else:
        tool = f"jupyter:{version}"
        used_version = version

    # easier to monkeypatch open_browser that try match the underlying
    # subprocess calls.
    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(utils, "open_browser", mock_open_browser)

    mock_token_hex = mock.Mock(spec=secrets.token_urlsafe)
    mock_token_hex.return_value = "TOKEN"
    monkeypatch.setattr(launch.secrets, "token_urlsafe", mock_token_hex)

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
            "--env",
            "JUPYTER_TOKEN=TOKEN",
            f"ghcr.io/opensafely-core/python:{used_version}",
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
    assert run_main(launch, f"{tool} --port 1234 --name test_jupyter") == 0
    mock_open_browser.assert_called_with("http://localhost:1234/?token=TOKEN")


@pytest.mark.parametrize("version", ["", "v2"])
@pytest.mark.parametrize("gitconfig_exists", [True, False])
def test_rstudio(run, tmp_path, monkeypatch, gitconfig_exists, version):

    if not version:
        tool = "rstudio"
        used_version = "v2"
    else:
        tool = f"rstudio:{version}"
        used_version = version

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

    if sys.platform == "linux":
        uid = os.getuid()
    else:
        uid = None

    run.expect(["docker", "info"])

    run.expect(
        [
            "docker",
            "image",
            "inspect",
            f"ghcr.io/opensafely-core/rstudio:{used_version}",
        ]
    )

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
        "--env=HOSTPLATFORM=" + sys.platform,
        f"--env=HOSTUID={uid}",
    ]

    if gitconfig_exists:
        expected.append(
            "--volume="
            + os.path.join(os.path.expanduser("~"), ".gitconfig")
            + ":/home/rstudio/local-gitconfig",
        )

    run.expect(expected + [f"ghcr.io/opensafely-core/rstudio:{used_version}"])

    assert run_main(launch, f"{tool} --port 8787 --name test_rstudio") == 0
    mock_open_browser.assert_called_with("http://localhost:8787")
