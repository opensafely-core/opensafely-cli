"""Support functions for running on windows."""

import os
import shutil
import sys


# poor mans debugging because debugging threads on windows is hard
if os.environ.get("DEBUG", False):

    def debug(msg):
        # threaded output for some reason needs the carriage return or else
        # it doesn't reset the cursor.
        sys.stderr.write("DEBUG: " + msg.replace("\n", "\r\n") + "\r\n")
        sys.stderr.flush()

else:

    def debug(msg):
        pass


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

    debug(f"detected no tty, found winpty at {winpty}, wrapping docker with it")
    # avoid using explicit path, as it can trip things up.
    return [winpty, "--"] + docker_cmd
