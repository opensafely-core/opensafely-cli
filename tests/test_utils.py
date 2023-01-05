import pathlib
from unittest import mock

from opensafely import utils


@mock.patch("opensafely.utils.os")
def test_get_default_user_unix(mock_os):
    mock_os.getuid.return_value = 12345
    mock_os.getgid.return_value = 67890
    assert utils.get_default_user() == "12345:67890"


@mock.patch("opensafely.utils.os")
def test_get_default_user_windows(mock_os):
    mock_os.getuid.side_effect = AttributeError()
    mock_os.getgid.side_effect = AttributeError()
    assert utils.get_default_user() is None


def test_ensure_tty_not_utils(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")
    assert utils.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_no_winpty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: None)
    assert utils.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_isatty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: True)
    assert utils.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_winpty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: False)
    assert utils.ensure_tty(["cmd"]) == ["/path/winpty", "--", "cmd"]


def test_run_docker_user_default(run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", None)
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    utils.run_docker([], "databuilder:v1", [])


def test_run_docker_user_linux(run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", "uid:gid")

    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--user=uid:gid",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    utils.run_docker([], "databuilder:v1", [])


def test_run_docker_interactive(run, no_user):
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    utils.run_docker([], "databuilder:v1", [], interactive=True)
