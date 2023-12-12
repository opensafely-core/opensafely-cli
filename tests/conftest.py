import argparse
import shlex
import subprocess
import sys
from collections import deque
from pathlib import Path

# ensure pkg_resources can find the package metadata we have included, as the
# opentelemetry packages need it
import pkg_resources


opensafely_module_dir = Path(__file__).parent
pkg_resources.working_set.add_entry(f"{opensafely_module_dir}/_vendor")

import pytest  # noqa: E402

from opensafely import utils  # noqa: E402


_actual_run = subprocess.run


class SubprocessRunFixture(deque):
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
        expected, value, exc, env = self.popleft()
        # text and check affect the return value and behaviour of run()
        text = kwargs.get("text", False)
        check = kwargs.get("check", False)
        actual_env = kwargs.get("env", None)

        # handle some windows calls being wrapped in winpty
        winpty = False
        if sys.platform == "win32":
            if "winpty" in cmd[0] and cmd[1] == "--":
                # strip winpty from cmd, do compare the wrapper
                cmd = cmd[2:]
                winpty = True

        # first up, do we expect this cmd?
        cmd_matches = expected == cmd

        # windows/git-bash interative docker commands will always include tty,
        # so check if we match w/o it
        if not cmd_matches and winpty and "--tty" in cmd:
            cmd_no_tty = cmd[:]
            cmd_no_tty.remove("--tty")
            cmd_matches = expected == cmd_no_tty

        if not cmd_matches:
            if self.strict:
                raise AssertionError(
                    f"run fixture got unexpected call:\n"
                    f"Received: {cmd}\n"
                    f"Expected: {expected}"
                )
            else:
                # pass through to system
                return _actual_run(cmd, *args, **kwargs)

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
