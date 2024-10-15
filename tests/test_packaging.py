import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePath

import pytest

import opensafely


BIN_DIR = "bin" if os.name != "nt" else "Scripts"

project_fixture_path = Path(__file__).parent / "fixtures" / "projects"


@pytest.fixture
def older_version_file():
    # This is really not very nice, but short of reworking the way versioning is handled
    # (which I don't want to do at the moment) I can't think of another way. In order to
    # build a package with the right version (both in the metadata and in the code
    # itself) we need to temporarily update the VERSION file.
    version_file_path = Path(opensafely.__file__).parent / "VERSION"
    orig_contents = version_file_path.read_bytes()
    try:
        version_file_path.write_text("0.1")
        yield
    finally:
        version_file_path.write_bytes(orig_contents)


@pytest.mark.parametrize("package_type", ["sdist", "bdist_wheel"])
def test_packaging(package_type, tmp_path, older_version_file):
    package_path = build_package(package_type)
    # Install it in a temporary virtualenv
    subprocess_run([sys.executable, "-m", "venv", tmp_path], check=True)
    # sdist requires wheel to build
    subprocess_run([tmp_path / BIN_DIR / "pip", "install", "wheel"], check=True)
    subprocess_run([tmp_path / BIN_DIR / "pip", "install", package_path], check=True)

    # Smoketest it by running `--help` and `--version`. This is actually a more
    # comprehensive test than you might think as it involves importing
    # everything and because all the complexity in this project is in the
    # vendoring and packaging, issues tend to show up at import time.
    subprocess_run([tmp_path / BIN_DIR / "opensafely", "run", "--help"], check=True)
    subprocess_run([tmp_path / BIN_DIR / "opensafely", "--version"], check=True)

    # only on linux, as that has docker installed in GH
    if sys.platform == "linux":
        # deeper integration test
        subprocess_run(
            [tmp_path / BIN_DIR / "opensafely", "run", "python"],
            check=True,
            cwd=str(project_fixture_path),
        )

    # This always triggers an upgrade because the development version is always
    # considered lower than any other version
    result = subprocess_run(
        [tmp_path / BIN_DIR / "opensafely", "upgrade"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Attempting uninstall: opensafely" in result.stdout
    assert "Successfully installed opensafely" in result.stdout


def test_installing_with_uv(tmp_path, older_version_file):
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("Skipping as `uv` not installed")

    package_path = build_package("bdist_wheel")
    bin_path = tmp_path / "bin"
    uv_env = dict(
        os.environ,
        UV_TOOL_BIN_DIR=bin_path,
        UV_TOOL_DIR=tmp_path / "tools",
    )
    python_version = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    subprocess_run(
        [uv_bin, "tool", "install", "--python", python_version, package_path],
        env=uv_env,
        check=True,
    )
    # Basic smoketest
    subprocess_run([bin_path / "opensafely", "run", "--help"], check=True)
    subprocess_run([bin_path / "opensafely", "--version"], check=True)
    # The `upgrade` command should prompt the user to use `uv upgrade` instead
    result = subprocess_run(
        [bin_path / "opensafely", "upgrade"], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "uv tool upgrade opensafely" in result.stdout


def build_package(package_type):
    extension = {"sdist": "tar.gz", "bdist_wheel": "whl"}[package_type]
    project_root = Path(__file__).parent.parent
    # This is pretty yucky. Ideally we'd stick all the build artefacts in a
    # temporary directory but I can't seem to persuade setuptools to do this
    shutil.rmtree(project_root / "dist", ignore_errors=True)
    shutil.rmtree(project_root / "build", ignore_errors=True)
    # Build the package
    subprocess_run(
        [sys.executable, "setup.py", package_type],
        check=True,
        cwd=project_root,
    )
    package_path = list(project_root.glob(f"dist/*.{extension}"))[0]
    return package_path


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
