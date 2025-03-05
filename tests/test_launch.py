import os
import pathlib
import secrets
import sys
from unittest import mock

import pytest

from opensafely import launch, utils
from tests.conftest import run_main


@pytest.mark.parametrize("version", ["", "v1"])
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
    monkeypatch.setattr(launch.utils, "open_browser", mock_open_browser)

    mock_token_hex = mock.Mock(spec=secrets.token_urlsafe)
    mock_token_hex.return_value = "TOKEN"
    monkeypatch.setattr(launch.secrets, "token_urlsafe", mock_token_hex)

    # these calls are done in different threads, so can come in any order
    run.concurrent = True

    run.expect(["docker", "info"])
    run.expect(["docker", "inspect", "test_jupyter"], returncode=1)
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
            "-p=8888:8888",
            "--name=test_jupyter",
            "--hostname=test_jupyter",
            "--env",
            "HOME=/tmp",
            "--env",
            "PYTHONPATH=/workspace",
            "--env",
            "JUPYTER_TOKEN=TOKEN",
            "--label=url=http://localhost:8888/?token=TOKEN",
            f"ghcr.io/opensafely-core/python:{used_version}",
            "jupyter",
            "lab",
            "--ip=0.0.0.0",
            "--port=8888",
            "--no-browser",
            "--ServerApp.custom_display_url=http://localhost:8888/",
            "-y",  # do not ask for confirmation on quiting
            "--Application.log_level=ERROR",  # errors only please
        ]
    )
    assert run_main(launch, f"{tool} --name test_jupyter") == 0
    mock_open_browser.assert_called_with("http://localhost:8888/?token=TOKEN")


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

    run.expect(["docker", "inspect", "test_rstudio"], returncode=1)
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
        "--label=url=http://localhost:8787",
    ]

    if gitconfig_exists:
        expected.append(
            "--volume="
            + os.path.join(os.path.expanduser("~"), ".gitconfig")
            + ":/home/rstudio/local-gitconfig",
        )

    run.expect(expected + [f"ghcr.io/opensafely-core/rstudio:{used_version}"])

    assert run_main(launch, f"{tool} --name test_rstudio") == 0
    mock_open_browser.assert_called_with("http://localhost:8787")


@pytest.mark.skipif(sys.platform != "linux", reason="Only runs on Linux")
@pytest.mark.parametrize("tool", ["jupyter", "rstudio"])
@pytest.mark.functional
def test_launch_browser(monkeypatch, docker, tool):
    """This tests the --background flag, as well as providing base functional tests."""

    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(launch.utils, "open_browser", mock_open_browser)

    args = f"{tool} --port 1234 --name test_launch_browser_{tool} --background"

    assert run_main(launch, args) == 0
    assert mock_open_browser.mock_calls[0].args[0].startswith("http://localhost:1234")


@pytest.mark.skipif(sys.platform != "linux", reason="Only runs on Linux")
@pytest.mark.functional
def test_launch_no_browser(monkeypatch, docker):
    """Just test rstudio, as the logic is the same for each"""

    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(launch.utils, "open_browser", mock_open_browser)

    args = "rstudio --name test_launch_no_browser --background --no-browser"

    assert run_main(launch, args) == 0
    assert not mock_open_browser.called


@pytest.mark.skipif(sys.platform != "linux", reason="Only runs on Linux")
@pytest.mark.functional
def test_launch_force(monkeypatch, docker):
    mock_open_browser = mock.Mock(spec=utils.open_browser)
    monkeypatch.setattr(launch.utils, "open_browser", mock_open_browser)

    # start rstuido
    assert run_main(launch, "rstudio --port 1234 --name test_force --background") == 0
    assert mock_open_browser.call_count == 1
    assert mock_open_browser.mock_calls[0].args[0] == "http://localhost:1234"

    # try again, without ---force
    # should not error, but still open browser, but on original port, not requested port
    assert run_main(launch, "rstudio --port 4321 --name test_force --background") == 0
    assert mock_open_browser.call_count == 2
    assert mock_open_browser.mock_calls[1].args[0] == "http://localhost:1234"

    # try agin, but with --force, whcih should kill the old one and start new one on requested port
    assert (
        run_main(launch, "rstudio --port 4321 --name test_force --background --force")
        == 0
    )
    assert mock_open_browser.call_count == 3
    assert mock_open_browser.mock_calls[2].args[0] == "http://localhost:4321"
