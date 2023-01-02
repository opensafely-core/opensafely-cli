import argparse
import pathlib
import shlex
from unittest import mock

import pytest

from opensafely import execute


@mock.patch("opensafely.execute.os")
def test_execute_get_default_user(mock_os):
    mock_os.getuid.return_value = 12345
    mock_os.getgid.return_value = 67890
    assert execute.get_default_user() == "12345:67890"


@mock.patch("opensafely.execute.os")
def test_execute_main_on_windows(mock_os):
    mock_os.getuid.side_effect = AttributeError()
    mock_os.getgid.side_effect = AttributeError()
    assert execute.get_default_user() is None


@pytest.fixture
def no_user(monkeypatch):
    """run a test with both linux and windows values."""
    monkeypatch.setattr(execute, "DEFAULT_USER", None)


def run_main(invocation):
    """Helper to use argparse then exec.

    This helps us functionally test our logic from a user perspective.
    """
    parser = argparse.ArgumentParser()
    execute.add_arguments(parser)
    argv = shlex.split(invocation)
    args = parser.parse_args(argv)
    return execute.main(**vars(args))


def test_execute_main(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ],
        winpty=True,
    )
    run_main("databuilder:v1 foo bar baz")


def test_execute_main_entrypoint(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--entrypoint=/entrypoint",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("--entrypoint /entrypoint databuilder:v1")


def test_execute_main_env(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--env",
            "FOO",
            "--env",
            "BAR",
            "--env",
            "BAZ=1",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("-e=FOO -e BAR --env BAZ=1 databuilder:v1")


def test_execute_main_user_windows(run, monkeypatch):
    monkeypatch.setattr(execute, "DEFAULT_USER", None)
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("databuilder:v1")


def test_execute_main_user_linux(run, monkeypatch):
    monkeypatch.setattr(execute, "DEFAULT_USER", "uid:gid")

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--user=uid:gid",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("databuilder:v1")


@pytest.mark.parametrize("default", [None, "uid:gid"])
def test_execute_main_user_cli_arg_overrides(default, run, monkeypatch):
    monkeypatch.setattr(execute, "DEFAULT_USER", default)

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--user=1234:5678",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("-u 1234:5678 databuilder:v1")


def test_execute_main_user_linux_disble(run, monkeypatch):
    monkeypatch.setattr(execute, "DEFAULT_USER", "uid:gid")

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
        winpty=True,
    )
    run_main("-u None databuilder:v1")


def test_execute_main_stata_license(run, monkeypatch, no_user):
    monkeypatch.setattr(execute, "get_stata_license", lambda: "LICENSE")

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--env",
            "STATA_LICENSE",
            "ghcr.io/opensafely-core/stata-mp",
            "analysis.do",
        ],
        env={"STATA_LICENSE": "LICENSE"},
        winpty=True,
    )
    run_main("stata-mp analysis.do")
