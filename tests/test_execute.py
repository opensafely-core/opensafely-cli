import pathlib

import pytest

from opensafely import execute, utils
from tests.conftest import run_main


def test_execute_main_args(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ],
    )
    assert run_main(execute, "databuilder:v1 foo bar baz") == 0


def test_execute_main_entrypoint(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--entrypoint=/entrypoint",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    run_main(execute, "--entrypoint /entrypoint databuilder:v1")


def test_execute_main_env(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--env",
            "FOO",
            "--env",
            "BAR",
            "--env",
            "BAZ=1",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    run_main(execute, "-e=FOO -e BAR --env BAZ=1 databuilder:v1")


def test_execute_main_env_in_env(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=tpp",
            "--env",
            "HOME=/foo",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    run_main(execute, "-e OPENSAFELY_BACKEND=tpp -e HOME=/foo databuilder:v1")


@pytest.mark.parametrize("default", [None, "uid:gid"])
def test_execute_main_user_cli_arg_overrides(default, run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", default)

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            "--user=1234:5678",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    run_main(execute, "-u 1234:5678 databuilder:v1")


def test_execute_main_user_linux_disble(run, monkeypatch):
    monkeypatch.setattr(utils, "DEFAULT_USER", "uid:gid")

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/databuilder:v1",
        ],
    )
    run_main(execute, "-u None databuilder:v1")


def test_execute_main_stata_license(run, monkeypatch, no_user):
    monkeypatch.setattr(execute, "get_stata_license", lambda: "LICENSE")

    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "--env",
            "OPENSAFELY_BACKEND=expectations",
            "--env",
            "HOME=/tmp",
            "--env",
            "STATA_LICENSE",
            "--cpus=2.0",
            "--memory=4G",
            "ghcr.io/opensafely-core/stata-mp",
            "analysis.do",
        ],
        env={"STATA_LICENSE": "LICENSE"},
    )
    run_main(execute, "stata-mp analysis.do")
