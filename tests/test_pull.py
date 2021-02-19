import argparse
import subprocess
from collections import deque

import pytest

from opensafely import pull


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


def tag(image):
    return f"{pull.REGISTRY}/{image}:latest"


def test_default_no_local_images(run, capsys):

    run.expect(["docker", "image", "ls", "--format='{{.Repository}}'"], stdout="")

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.strip() == "No OpenSAFELY docker images found to update."


def test_default_no_local_images_force(run, capsys):

    run.expect(["docker", "image", "ls", "--format='{{.Repository}}'"], stdout="")
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "pull", tag("python")])
    run.expect(["docker", "pull", tag("jupyter")])
    run.expect(["docker", "pull", tag("stata-mp")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="all", force=True)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Updating OpenSAFELY python image",
        "Updating OpenSAFELY jupyter image",
        "Updating OpenSAFELY stata-mp image",
        "Cleaning up old images",
    ]


def test_default_with_local_images(run, capsys):

    run.expect(
        ["docker", "image", "ls", "--format='{{.Repository}}'"],
        stdout="ghcr.io/opensafely-core/r",
    )
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Cleaning up old images",
    ]


def test_specific_image(run, capsys):

    run.expect(["docker", "image", "ls", "--format='{{.Repository}}'"], stdout="")
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="r", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Cleaning up old images",
    ]


def test_remove_deprecated_images(run):
    local_images = set(
        [
            "docker.opensafely.org/r",
            "ghcr.io/opensafely/r",
            "ghcr.io/opensafely-core/r",
        ]
    )

    run.expect(["docker", "image", "rm", "docker.opensafely.org/r"])
    run.expect(["docker", "image", "rm", "ghcr.io/opensafely/r"])

    pull.remove_deprecated_images(local_images)


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], argparse.Namespace(image="all", force=False)),
        (["--force"], argparse.Namespace(image="all", force=True)),
        (["r"], argparse.Namespace(image="r", force=False)),
        (["r", "--force"], argparse.Namespace(image="r", force=True)),
        (["invalid"], SystemExit()),
    ],
)
def test_pull_parser_valid(argv, expected, capsys):
    parser = argparse.ArgumentParser()
    pull.add_arguments(parser)
    if isinstance(expected, SystemExit):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
    else:
        assert parser.parse_args(argv) == expected
