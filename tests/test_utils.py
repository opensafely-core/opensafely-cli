import os
import pathlib
import socket
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


def test_open_browser_timeout(monkeypatch, capsys):
    monkeypatch.setitem(os.environ, "DEBUG", "TRUE")

    mock_open = mock.Mock(spec=utils.webbrowser.open)
    monkeypatch.setattr(utils.webbrowser, "open", mock_open)

    port = utils.get_free_port()
    url = f"http://localhost:{port}/"
    utils.open_browser(url, timeout=0.01)

    assert not mock_open.called
    _, err = capsys.readouterr()
    assert f"Could not connect to {url}" in err


def test_open_browser_error(monkeypatch, capsys):
    # turn on debug logging
    monkeypatch.setitem(os.environ, "DEBUG", "TRUE")

    # return successful response from poll
    mock_get = mock.Mock(spec=utils.requests.get)
    response = utils.requests.Response()
    response.status_code = 200
    mock_get.return_value = response
    monkeypatch.setattr(utils.requests, "get", mock_get)

    # raise exception when calling webbrowser.open
    mock_open = mock.Mock(spec=utils.webbrowser.open)
    mock_open.side_effect = Exception("TEST ERROR")
    monkeypatch.setattr(utils.webbrowser, "open", mock_open)

    port = utils.get_free_port()
    url = f"http://localhost:{port}/"
    utils.open_browser(url, timeout=0.01)

    mock_open.assert_called_with(url, new=2)
    out, err = capsys.readouterr()
    assert out == ""
    assert "TEST ERROR" in err


def test_get_free_port():
    # test basic usage, then use that port as the default port for later assertions
    free_port = utils.get_free_port()
    assert isinstance(free_port, int)
    # use free_port as we know its free!
    default_port = free_port

    # check passing a default,
    port = utils.get_free_port(default_port)
    assert isinstance(default_port, int)
    assert port == default_port

    # check the default being already bound
    with socket.socket() as sock:
        sock.bind(("0.0.0.0", default_port))
        port = utils.get_free_port(default_port)
        assert isinstance(default_port, int)
        assert port != default_port
