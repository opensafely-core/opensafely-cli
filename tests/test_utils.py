import os
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


def test_git_bash_tty_wrapper_not_utils(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "linux")
    assert utils.git_bash_tty_wrapper() is None


def test_git_bash_tty_wrapper_no_winpty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: None)
    assert utils.git_bash_tty_wrapper() is None


def test_git_bash_tty_wrapper_isatty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: True)


def test_git_bash_tty_wrapper_not_mingw(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: False)
    assert utils.git_bash_tty_wrapper() is None


def test_git_bash_tty_wrapper_winpty(monkeypatch):
    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setattr(utils.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: False)
    monkeypatch.setitem(os.environ, "MSYSTEM", "foo")
    assert utils.git_bash_tty_wrapper() == ["/path/winpty", "--"]


def test_run_docker_user_default(run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", None)
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--platform=linux/amd64",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/ehrql:v1",
        ],
    )
    utils.run_docker([], "ehrql:v1", [])


def test_run_docker_user_linux(run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", "uid:gid")

    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--platform=linux/amd64",
            "--user=uid:gid",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/ehrql:v1",
        ],
    )
    utils.run_docker([], "ehrql:v1", [])


def test_run_docker_interactive(run, no_user):
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
            "ghcr.io/opensafely-core/ehrql:v1",
        ],
    )
    utils.run_docker([], "ehrql:v1", [], interactive=True)


def test_run_docker_interactive_tty(run, no_user, monkeypatch):
    monkeypatch.setattr(utils.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(utils.sys.stdout, "isatty", lambda: True)
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "--platform=linux/amd64",
            "--interactive",
            "--tty",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/ehrql:v1",
        ],
    )
    utils.run_docker([], "ehrql:v1", [], interactive=True)
