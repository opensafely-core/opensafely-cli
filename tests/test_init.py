import os
import warnings
from datetime import datetime, timedelta

import pytest

import opensafely
from tests.test_pull import expect_local_images


@pytest.mark.parametrize(
    ("version_info", "expected_message"),
    [
        ((3, 9), "older than Python 3.10"),
        ((3, 10), None),
        ((3, 11), None),
        ((3, 12), None),
        ((3, 13), None),
        ((3, 14), "newer than Python 3.13"),
    ],
)
def test_warn_if_unsupported_python_version(
    capsys,
    monkeypatch,
    version_info,
    expected_message,
):
    monkeypatch.setattr(opensafely.sys, "version_info", version_info)

    opensafely.warn_if_unsupported_python_version()

    stderr = capsys.readouterr().err

    if expected_message is None:
        assert stderr == ""
    else:
        assert expected_message in stderr


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
        stdout="ghcr.io/opensafely-core/python:v1=sha256:oldsha",
    )

    opensafely.warn_if_updates_needed(["opensafely"])

    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        "Warning: the OpenSAFELY docker images for python:v1 actions are out of date - please update by running:",
        "    opensafely pull",
        "",
    ]


def test_warnings_patched_format_for_pipeline_warnings():
    # Warnings from the pipeline library (UserWarnings with a message that begins with
    # ProjectWarning) are formatted to display just the message.
    with pytest.warns(UserWarning) as raised_warnings:
        warnings.warn("Warning: foo", UserWarning)
        warnings.warn("ProjectWarning: foo", UserWarning)

    assert len(raised_warnings.list) == 2
    standard_warning, project_warning = raised_warnings.list

    # standard warning includes the warning category (and other standard warning formatting)
    assert "UserWarning: Warning: foo" in warnings.formatwarning(
        standard_warning.message,
        standard_warning.category,
        standard_warning.filename,
        standard_warning.lineno,
        standard_warning.line,
    )
    # project warning contains just the warning message
    assert "ProjectWarning: foo\n" == warnings.formatwarning(
        project_warning.message,
        project_warning.category,
        project_warning.filename,
        project_warning.lineno,
        project_warning.line,
    )
