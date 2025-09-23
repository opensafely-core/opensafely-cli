import argparse
import shlex
import subprocess
import sys

import pytest  # noqa: E402
from opensafely._vendor import requests  # noqa: E402
from requests_mock import mocker  # noqa: E402

import opensafely  # noqa: E402
from opensafely import utils  # noqa: E402


# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
#
mocker.requests = requests
mocker._original_send = requests.Session.send

# save reference to actual run function
_actual_run = subprocess.run


class SubprocessRunFixture(list):
    """Fixture for mocking subprocess.run.

    Add expected calls and their responses to subprocess.run:

        run.expect(['your', 'cmd', 'here'], returncode=1, stderr='error!')

    And when subprocess.run is called with that command, it will return the
    appropriate CompletedProcess object.

    If your code is calling subprocess.run with check=True, pass that to the
    expect() call too, and a CalledProcessError will be raised if the
    returncode is not 0.

        run.expect(['your', 'cmd', 'here'], check=True, returncode=1, stderr='error!')

    By default, strict=True, which means all calls to subprocess.run must have
    a matching expect(), or an AssertionError will be raised.

    If strict is set to False, any unexpected calls are passed through to the
    real subprocess.run(). This allows you to only mock some calls to
    subprocess.run().
    """

    strict = True
    concurrent = False

    class CommandNotFound(Exception):
        pass

    def expect(
        self,
        cmd,
        returncode=0,
        stdout=None,
        stderr=None,
        check=False,
        env=None,
    ):
        value = exc = None
        if check and returncode != 0:
            exc = subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
        else:
            value = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
        self.append((cmd, value, exc, env))

    def run(self, cmd, *args, **kwargs):
        """The replacement run() function."""

        try:
            expected, value, exc, env = self.find_cmd(cmd)
        except self.CommandNotFound:
            if self.strict:
                expected = "\n".join(str(x[0]) for x in self)
                raise AssertionError(
                    f"run fixture got unexpected call:\n"
                    f"Received:\n{cmd}\n"
                    f"Expected:\n{expected}"
                )
            else:
                # pass through to system
                return _actual_run(cmd, *args, **kwargs)

        # text and check affect the return value and behaviour of run()
        text = kwargs.get("text", False)
        check = kwargs.get("check", False)
        actual_env = kwargs.get("env", None)

        # next: are we expecting an exception?
        if exc is not None:
            if check:
                # run called with check, and we are expecting exception, so raise
                raise value
            else:
                # expected to raise exception, but run was called without check
                raise AssertionError(f"run fixture expected check=True: {cmd}")

        # validate stdout/stderr are correct bytes/string
        valid_type = str if text else bytes
        for output in ["stdout", "stderr"]:
            output_value = getattr(value, output)
            if output_value is None:
                # if was set to None, set instead to empty string of correct type
                setattr(value, output, valid_type())
                continue

            assert isinstance(
                output_value, valid_type
            ), f"run fixture called with text={text} but expected {output} is of type {type(output_value)}"

        # check it was called with the expected env items in the actual env
        if env:
            for k, v in env.items():
                if k in actual_env:
                    assert (
                        actual_env[k] == v
                    ), "run fixture called with env value {k}={actual_env[k]}, expected {k}={v}"
                else:
                    raise AssertionError(
                        "run fixture called with no value {k}, expected {k}={v}"
                    )

        return value

    def find_cmd(self, cmd):
        """Search list and find command."""
        for i, (expected, value, exc, env) in enumerate(self):
            if self.cmd_matches(expected, cmd):
                del self[i]
                return expected, value, exc, env

            if not self.concurrent:
                raise self.CommandNotFound(cmd)

        raise self.CommandNotFound(cmd)

    def cmd_matches(self, expected, cmd):
        # handle some windows calls being wrapped in winpty
        winpty = False
        if sys.platform == "win32":
            if "winpty" in cmd[0] and cmd[1] == "--":
                # strip winpty from cmd, do compare the wrapper
                cmd = cmd[2:]
                winpty = True

        # first up, do we expect this cmd?
        matches = expected == cmd

        # windows/git-bash interative docker commands will always include tty,
        # so check if we match w/o it
        if not matches and winpty and "--tty" in cmd:
            cmd_no_tty = cmd[:]
            cmd_no_tty.remove("--tty")
            matches = expected == cmd_no_tty

        return matches


@pytest.fixture
def run(monkeypatch):
    fixture = SubprocessRunFixture()
    monkeypatch.setattr(subprocess, "run", fixture.run)
    yield fixture
    if len(fixture) != 0:
        remaining = "\n".join(str(f[0]) for f in fixture if f)
        raise AssertionError(
            f"run fixture had unused remaining expected cmds:\n{remaining}"
        )


@pytest.fixture
def no_user(monkeypatch):
    """run a test without any default user, as if it was windows.

    This avoids needing to handle --user only appearing in run calls on linux
    when running tests.
    """
    monkeypatch.setattr(utils, "DEFAULT_USER", None)


def run_main(module, cli_args):
    """Helper for testing a subcommand.

    Builds parser for a module, parsesarguments, then execute the main function
    with those arguments.

    This helps us functionally test our logic from a user perspective, and make
    sure we don't miss match arg parsing and function arguments.
    """
    parser = argparse.ArgumentParser()
    module.add_arguments(parser)
    argv = shlex.split(cli_args)
    args = parser.parse_args(argv)
    return module.main(**vars(args))


@pytest.fixture
def set_current_version(monkeypatch):
    def set(value):  # noqa: A001
        assert value[0] == "v", "Current __version__ must start with v"
        monkeypatch.setattr(opensafely, "__version__", value)

    yield set


@pytest.fixture
def set_pypi_version(requests_mock):
    def set(version):  # noqa: A001
        requests_mock.get(
            "https://pypi.org/pypi/opensafely/json",
            json={"info": {"version": version}},
        )

    return set


@pytest.fixture
def docker(monkeypatch):
    test_label = "opensafely-cli-tests"
    monkeypatch.setattr(utils, "DOCKER_LABEL", test_label)
    yield
    delete_docker_entities("container", test_label)


def delete_docker_entities(entity, label, ignore_errors=False):
    ls_args = [
        "docker",
        entity,
        "ls",
        "--all" if entity == "container" else None,
        "--filter",
        f"label={label}",
        "--quiet",
    ]
    ls_args = list(filter(None, ls_args))
    response = subprocess.run(
        ls_args, capture_output=True, encoding="ascii", check=not ignore_errors
    )
    ids = response.stdout.split()
    if ids and response.returncode == 0:
        rm_args = ["docker", entity, "rm", "--force"] + ids
        subprocess.run(rm_args, capture_output=True, check=not ignore_errors)
