import os
from datetime import datetime, timedelta

import opensafely
from tests.test_pull import expect_local_images


def test_should_version_check():
    opensafely.VERSION_FILE.unlink(missing_ok=True)

    assert opensafely.should_version_check() is True
    opensafely.update_version_check()
    assert opensafely.should_version_check() is False

    timestamp = (datetime.utcnow() - timedelta(hours=5)).timestamp()
    os.utime(opensafely.VERSION_FILE, (timestamp, timestamp))

    assert opensafely.should_version_check() is True


def test_warn_if_updates_needed_package_outdated(
    capsys, monkeypatch, tmp_path, set_current_version, set_pypi_version
):

    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")
    monkeypatch.setattr(opensafely, "VERSION_FILE", tmp_path / "timestamp")
    opensafely.warn_if_updates_needed(["opensafely"])

    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        "Warning: there is a newer version of opensafely available (1.1.0) - please upgrade by running:",
        "    opensafely upgrade",
        "",
    ]


def test_warn_if_updates_needed_images_outdated(capsys, monkeypatch, tmp_path, run):
    monkeypatch.setattr(opensafely, "VERSION_FILE", tmp_path / "timestamp")
    expect_local_images(
        run,
        stdout="ghcr.io/opensafely-core/python:latest=sha256:oldsha",
    )

    opensafely.warn_if_updates_needed(["opensafely"])

    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        "Warning: the OpenSAFELY docker images for python:latest actions are out of date - please update by running:",
        "    opensafely pull",
        "",
    ]
