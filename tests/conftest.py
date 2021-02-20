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
        if check and returncode != 0:
            value = subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
        else:
            value = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
        self.append((cmd, value))

    def run(self, cmd, *args, **kwargs):
        """The replacement run() function."""
        expected, value = self.popleft()

        if expected == cmd:
            if isinstance(value, Exception):
                raise value
            return value

        if self.strict:
            raise AssertionError(f"run fixture got unexpected call: {cmd}")
        else:
            # pass through to system
            return _actual_run(cmd, *args, **kwargs)


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
