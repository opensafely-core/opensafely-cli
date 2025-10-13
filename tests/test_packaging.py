import os
import shutil
import subprocess
import sys
import time
from pathlib import Path, PurePath

import pytest

import opensafely
from opensafely.upgrade import get_latest_version


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


@pytest.fixture
def project_dir(tmp_path):
    project_dir = tmp_path / "project"
    shutil.copytree(project_fixture_path, project_dir)
    return project_dir


@pytest.mark.parametrize("package_type", ["sdist", "wheel"])
def test_packaging(package_type, tmp_path, older_version_file, project_dir):
    package_path = build_package(package_type, tmp_path)
    # Install it in a temporary virtualenv
    subprocess_run([sys.executable, "-m", "venv", tmp_path], check=True)
    subprocess_run([tmp_path / BIN_DIR / "pip", "install", package_path], check=True)

    # Smoketest it by running `--help` and `--version`. This is actually a more
    # comprehensive test than you might think as it involves importing
    # everything and because all the complexity in this project is in the
    # vendoring and packaging, issues tend to show up at import time.
    subprocess_run(
        [tmp_path / BIN_DIR / "opensafely", "--debug", "run", "--help"], check=True
    )
    ps = subprocess_run(
        [tmp_path / BIN_DIR / "opensafely", "--debug", "--version"],
        check=True,
        text=True,
        capture_output=True,
    )
    version_before = ps.stdout.strip()

    assert version_before == "opensafely 0.1"

    # only on linux, as that has docker installed in GH
    if sys.platform == "linux":
        # deeper integration test
        subprocess_run(
            [tmp_path / BIN_DIR / "opensafely", "--debug", "run", "python"],
            check=True,
            cwd=project_dir,
        )

    # Grab the version we expect to upgrade to. We can't really fake this, is
    # we're doing a full functional test.
    # Note: there's a small chance of a race condition here, if the version is
    # actually updated in between this call and the call as part of the upgrade
    # subprocess.
    latest = get_latest_version()

    # This always triggers an upgrade because the development version is always
    # considered lower than any other version
    result = subprocess_run(
        [tmp_path / BIN_DIR / "opensafely", "--debug", "upgrade"],
        check=True,
        capture_output=True,
        text=True,
    )

    if sys.platform == "win32":
        # wait a little for background process to finish the pip upgrade.
        # Should usually only happen CI
        time.sleep(5)

    ps = subprocess_run(
        [tmp_path / BIN_DIR / "opensafely", "--debug", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    version_after = ps.stdout.strip()
    # try handle race condition, as post-merge CI runs publish
    next_latest = get_latest_version()
    assert (
        version_after == f"opensafely v{latest}"
        or version_after == f"opensafely v{next_latest}"
    )

    assert "Attempting uninstall: opensafely" in result.stdout
    assert "Successfully installed opensafely" in result.stdout


def test_installing_with_uv(tmp_path, older_version_file, project_dir):
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("Skipping as `uv` not installed")

    package_path = build_package("wheel", tmp_path)
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
    subprocess_run([bin_path / "opensafely", "--debug", "--version"], check=True)

    if sys.platform == "linux":
        # run an actual job to test the install
        subprocess_run(
            [bin_path / "opensafely", "--debug", "run", "python"],
            check=True,
            cwd=project_dir,
        )
    else:  # e.g. windows/mac CI
        # Basic smoketest that doesn't need docker
        subprocess_run([bin_path / "opensafely", "run", "--help"], check=True)

    # The `upgrade` command should prompt the user to use `uv upgrade` instead
    result = subprocess_run(
        [bin_path / "opensafely", "upgrade"], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "uv tool upgrade opensafely" in result.stdout


def test_installing_otel_with_uv(tmp_path, older_version_file, project_dir):
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("Skipping as `uv` not installed")

    package_path = build_package("wheel", tmp_path)
    install_target = str(package_path) + "[tracing]"
    bin_path = tmp_path / "bin"
    uv_env = dict(
        os.environ,
        UV_TOOL_BIN_DIR=bin_path,
        UV_TOOL_DIR=tmp_path / "tools",
    )
    python_version = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    subprocess_run(
        [uv_bin, "tool", "install", "--python", python_version, install_target],
        env=uv_env,
        check=True,
    )
    # check we are installed
    subprocess_run([bin_path / "opensafely", "--version"], check=True)

    if sys.platform == "linux":
        # run an actual job to test the install
        env = os.environ.copy()
        env["OTEL_EXPORTER_CONSOLE"] = "true"
        ps = subprocess_run(
            [bin_path / "opensafely", "run", "python"],
            check=True,
            text=True,
            capture_output=True,
            cwd=project_dir,
            env=env,
        )
        # we should be seeing otel traces
        assert '"trace_id":' in ps.stdout
    else:  # e.g. windows/mac CI
        # Basic smoketest that doesn't need docker
        subprocess_run([bin_path / "opensafely", "run", "--help"], check=True)


def build_package(package_type, tmp_path):
    extension = {"sdist": "tar.gz", "wheel": "whl"}[package_type]
    project_root = Path(__file__).parent.parent
    # Build the package
    subprocess_run(
        [sys.executable, "-m", "build", f"--{package_type}", "--outdir", tmp_path],
        check=True,
        cwd=project_root,
    )
    package_path = list(tmp_path.glob(f"*.{extension}"))[0]
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
    print(f"Executing: {' '.join(cmd_args)}")
    try:
        return subprocess.run(cmd_args, **kwargs)
    except subprocess.CalledProcessError as exc:
        print("STDOUT:")
        print(exc.stdout)
        print("STDERR:")
        print(exc.stderr)
        raise


def to_str(value):
    # PurePath is the base class for all pathlib classes
    if isinstance(value, PurePath):
        return str(value)
    return value
