"""Support functions for running on windows."""

import os
import pathlib
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser

from opensafely._vendor import requests
from opensafely._vendor.jobrunner import config


# all docker containers we run will be tagged with this label
DOCKER_LABEL = "opensafely"


def debug(msg):
    """Windows threaded debugger."""
    if os.environ.get("DEBUG", False):
        # threaded output for some reason needs the carriage return or else
        # it doesn't reset the cursor.
        sys.stderr.write("DEBUG: " + msg.replace("\n", "\r\n") + "\r\n")
        sys.stderr.flush()


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


def git_bash_tty_wrapper():
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
        return

    winpty = shutil.which("winpty")

    if winpty is None:
        # not git-bash
        return

    if sys.stdin.isatty() and sys.stdout.isatty():
        # already sorted, possibly user already ran us with winpty
        return

    if "MSYSTEM" not in os.environ:
        # not in MINGW terminal, so we can trust isatty
        return

    # At this point, we know that we are almost certainly in git-bash terminal on windows.
    # Because isatty() always returns false in this situation, we don't know if
    # we have a terminal or not, and we don't know any other way to test.
    #
    # So, we chose to always assume a tty in this scenario, so that a bare
    # `opensafely exec ...` will work as expected. This means that piping input
    # into `opensafely exec` will not work in this scenario.

    # avoid using explicit path, as it can trip things up.
    return [winpty, "--"]


def run_docker(
    docker_args,
    image,
    cmd=(),
    directory=None,
    interactive=False,
    detach=False,
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

    if interactive and detach:
        raise Exception("Cannot use both interactive and background")

    if user is None:
        user = DEFAULT_USER

    base_cmd = [
        "docker",
        "run",
        "--rm",
        "--init",
        f"--label={DOCKER_LABEL}",
        # all our docker images are this platform
        # helps when running on M-series macs.
        "--platform=linux/amd64",
    ]

    if detach:
        base_cmd += ["--detach"]
    elif interactive:
        base_cmd += ["--interactive"]
        wrapper = git_bash_tty_wrapper()
        if (sys.stdin.isatty() and sys.stdout.isatty()) or wrapper:
            base_cmd += ["--tty"]

        if wrapper:
            base_cmd = wrapper + base_cmd

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

    cmd = " ".join(docker_cmd)
    if verbose:
        print(cmd)
    else:
        debug(cmd)

    return subprocess.run(docker_cmd, *args, **kwargs)


def dockerctl(cmd, *args, check=True, capture_output=True, text=True, **kwargs):
    """Utility function to docker commands that are *not* run.

    Sets some defaults:
     - check=True
     - capture_output=True
     - text=True

    Also ensures
    """

    assert cmd != "run", "Use run_docker not dockerctl"

    return subprocess.run(
        ["docker", cmd] + list(args),
        check=check,
        capture_output=capture_output,
        text=text,
        **kwargs,
    )


def get_free_port(default=None):
    """Get a port that is free on the users host machine"""
    # try the default first
    if default:
        with socket.socket() as sock:
            try:
                sock.bind(("0.0.0.0", int(default)))
            except OSError:
                # the socket is busy
                pass
            else:
                return default

    # this is a race condition, as something else could consume the socket
    # before docker binds to it, but the chance of that on a user's
    # personal machine is very small.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    return str(port)


def print_exception_from_thread(*exc_info):
    # reformat exception printing to work from thread in windows
    import traceback

    sys.stderr.write("Error in background thread:\r\n")
    tb = "".join(traceback.format_exception(*exc_info)).replace("\n", "\r\n")
    sys.stderr.write(tb)
    sys.stderr.flush()


def open_browser(url, timeout=30.0):
    try:
        debug(f"open_browser: url={url}")

        # wait for port to be open
        debug("open_browser: waiting for port")
        start = time.time()
        response = None
        while time.time() - start < timeout:
            try:
                response = requests.get(url, timeout=1)
            except Exception:
                time.sleep(0.5)
            else:
                break

        if not response:
            # always write a failure message
            sys.stderr.write(f"Could not connect to {url} to open browser\r\n")
            sys.stderr.flush()
            return

        # open a webbrowser pointing to the docker container
        debug("open_browser: opening browser window")
        webbrowser.open(url, new=2)

    except Exception:
        print_exception_from_thread(*sys.exc_info())


def open_in_thread(target, args):
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.name = "browser thread"
    debug("starting browser thread")
    thread.start()
    return thread
