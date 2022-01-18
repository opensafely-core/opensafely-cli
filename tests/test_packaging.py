import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePath

import pytest

BIN_DIR = "bin" if os.name != "nt" else "Scripts"


@pytest.mark.parametrize(
    "package_type,ext", [("sdist", "tar.gz"), ("bdist_wheel", "whl")]
)
def test_packaging(package_type, ext, tmp_path):
    project_root = Path(__file__).parent.parent
    # This is pretty yucky. Ideally we'd stick all the build artefacts in a
    # temporary directory but I can't seem to persuade setuptools to do this
    shutil.rmtree(project_root / "dist", ignore_errors=True)
    shutil.rmtree(project_root / "build", ignore_errors=True)
    # Build the package
    subprocess_run(
        [sys.executable, "setup.py", "build", package_type],
        check=True,
        cwd=project_root,
    )
    # Install it in a temporary virtualenv
    subprocess_run([sys.executable, "-m", "venv", tmp_path], check=True)
    package = list(project_root.glob(f"dist/*.{ext}"))[0]
    subprocess_run([tmp_path / BIN_DIR / "pip", "install", package], check=True)
    # Smoketest it by running `--help` and `--version`. This is actually a more
    # comprehensive test than you might think as it involves importing
    # everything and because all the complexity in this project is in the
    # vendoring and packaging, issues tend to show up at import time.
    subprocess_run([tmp_path / BIN_DIR / "opensafely", "run", "--help"], check=True)
    subprocess_run([tmp_path / BIN_DIR / "opensafely", "--version"], check=True)
    # This always triggers an upgrade because the development version is always
    # considered lower than any other version
    subprocess_run([tmp_path / BIN_DIR / "opensafely", "upgrade", "1.7.0"], check=True)


def subprocess_run(cmd_args, **kwargs):
    """
    Thin wrapper around `subprocess.run` which ensures that any arguments which
    are pathlib instances get coerced to strings, which is necessary for them
    to work on Windows (but not POSIX). Most of these issues are fixed in
    Python 3.8 so it's possible we can drop this later. (The exception being
    the `env` argument which the documentation doesn't mention so we'll have to
    wait and see.)
    """
    assert not kwargs.get("shell"), "Don't use shell as we need to work cross-platform"
    cmd_args = list(map(to_str, cmd_args))
    if "cwd" in kwargs:
        kwargs["cwd"] = to_str(kwargs["cwd"])
    if "env" in kwargs:
        kwargs["env"] = {key: to_str(value) for (key, value) in kwargs["env"].items()}
    return subprocess.run(cmd_args, **kwargs)


def to_str(value):
    # PurePath is the base class for all pathlib classes
    if isinstance(value, PurePath):
        return str(value)
    return value
