"""Support functions for running on windows."""

import os
import pathlib
import shutil
import subprocess
import sys

from opensafely._vendor.jobrunner import config


def get_default_user():
    try:
        # On ~unix, in order for any files that get created to have the
        # appropriate owner/group we run the command using the current user's
        # UID/GID
        return f"{os.getuid()}:{os.getgid()}"
    except Exception:
        # These aren't available on Windows; but then on Windows we don't have to deal
        # with the same file ownership problems which require us to match the UID in the
        # first place.
        return None


DEFAULT_USER = get_default_user()


def ensure_tty(docker_cmd):
    """Ensure that we have a valid tty to use to run docker.

    This is needed as we want the user to be able to kill jupyter with Ctrl-C
    as normal, which requires a tty on their end.

    Nearly every terminal under the sun gives you a valid tty. Except
    git-bash's default terminal, which happens to be the one a lot of our users
    use.

    git-bash provides the `wintpy` tool as a workaround, so detect we are in
    that situation and use it if so.

    """
    # Note: we don't use platform.system(), as it uses subprocess.run, and this mucks up our test expectations
    if sys.platform != "win32":
        return docker_cmd

    winpty = shutil.which("winpty")

    if winpty is None:
        # not git-bash
        return docker_cmd

    if sys.stdin.isatty() and sys.stdout.isatty():
        # already sorted, possibly user already ran us with winpty
        return docker_cmd

    # avoid using explicit path, as it can trip things up.
    return [winpty, "--"] + docker_cmd


def run_docker(
    docker_args,
    image,
    cmd,
    directory=None,
    interactive=False,
    user=None,
    verbose=False,
    *args,
    **kwargs,
):
    """Run opensafely docker image.

    - mounts given directory as /workspace (cwd by default).
    - run as invoking user on linux to avoid permissions issues (user=False disables)
    - runs with stdin/tty if interactive=True, handling git-bash on windows.
    - passes through any other args to subprocess.run
    """

    if user is None:
        user = DEFAULT_USER

    base_cmd = [
        "docker",
        "run",
        "--rm",
        "--init",
        "--label=opensafely",
    ]

    if interactive:
        base_cmd = ensure_tty(base_cmd + ["-it"])

    if user:
        base_cmd.append(f"--user={user}")

    if directory is None:
        directory = pathlib.Path.cwd()

    # note: // is to avoid git-bash path translation
    base_cmd.append(f"--volume={directory.resolve()}://workspace")

    docker_cmd = [
        *base_cmd,
        *docker_args,
        f"{config.DOCKER_REGISTRY}/{image}",
        *cmd,
    ]

    if verbose:
        print(" ".join(docker_cmd))

    return subprocess.run(docker_cmd, *args, **kwargs)
