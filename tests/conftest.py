import subprocess
from collections import deque

import pytest

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

    def expect(self, cmd, returncode=0, stdout=None, stderr=None, check=False):
        value = exc = None
        if check and returncode != 0:
            exc = subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
        else:
            value = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
        self.append((cmd, value, exc))

    def run(self, cmd, *args, **kwargs):
        """The replacement run() function."""
        expected, value, exc = self.popleft()
        # text and check affect the return value and behaviour of run()
        text = kwargs.get("text", False)
        check = kwargs.get("check", False)

        # first up, do we expect this cmd?
        if expected != cmd:
            if self.strict:
                raise AssertionError(f"run fixture got unexpected call: {cmd}")
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

        # check bytes/string
        valid_type = str if text else bytes
        for output in ["stdout", "stderr"]:
            output_value = getattr(value, output)
            if output_value is None:
                continue

            assert isinstance(
                output_value, valid_type
            ), f"run fixture called with text={text} but expected {output} is of type {type(output_value)}"

        return value


@pytest.fixture
def run(monkeypatch):
    fixture = SubprocessRunFixture()
    monkeypatch.setattr(subprocess, "run", fixture.run)
    yield fixture
    if len(fixture) != 0:
        remaining = "\n".join(str(cmd) for cmd, _ in fixture)
        raise AssertionError(
            f"run fixture had unused remaining expected cmds:\n{remaining}"
        )
