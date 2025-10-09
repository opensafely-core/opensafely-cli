import argparse
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from opensafely import upgrade


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_main_latest_upgrade_windows(
    set_pypi_version, set_current_version, monkeypatch
):
    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")

    expected = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "opensafely==1.1.0",
    ]

    mock = MagicMock(spec=subprocess.Popen)
    monkeypatch.setattr(upgrade.subprocess, "Popen", mock)

    try:
        upgrade.main("latest")
    except SystemExit as exc:
        assert exc.code == 0

    mock.assert_called_once_with(expected)


@pytest.mark.skipif(sys.platform == "win32", reason="Not on Windows")
def test_main_latest_upgrade(set_pypi_version, set_current_version, run):
    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")

    run.expect(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "opensafely==1.1.0",
        ],
        check=True,
    )

    upgrade.main("latest")


def test_main_latest_no_upgrade(set_pypi_version, run, set_current_version, capsys):
    set_pypi_version("1.0.0")
    set_current_version("v1.0.0")
    upgrade.main("latest")
    out, err = capsys.readouterr()
    assert out.strip() == "opensafely is already at version 1.0.0"


def test_main_specific_no_upgrade(run, set_current_version, capsys):
    set_current_version("v1.1.0")
    upgrade.main("1.1.0")
    out, err = capsys.readouterr()
    assert out.strip() == "opensafely is already at version 1.1.0"


def test_need_to_update(set_current_version):
    set_current_version("v1.0.0")
    assert upgrade.need_to_update("1.1.0")
    set_current_version("v1.1.0")
    assert not upgrade.need_to_update("1.1.0")
    assert not upgrade.need_to_update("1.0.0")
    # check version comparision is not lexographical
    set_current_version("v1.11.0")
    assert not upgrade.need_to_update("1.2.0")
    set_current_version("v1.2.0")
    assert upgrade.need_to_update("1.11.0")


def test_check_version_needs_updating(set_current_version, set_pypi_version):
    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")
    assert upgrade.check_version()


def test_check_version_not_need_updating(set_current_version, set_pypi_version):
    set_pypi_version("1.0.0")
    set_current_version("v1.0.0")
    assert not upgrade.check_version()


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], argparse.Namespace(version="latest")),
        (["1.0.0"], argparse.Namespace(version="1.0.0")),
    ],
)
def test_pull_parser_valid(argv, expected, capsys):
    parser = argparse.ArgumentParser()
    upgrade.add_arguments(parser)
    if isinstance(expected, SystemExit):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
    else:
        assert parser.parse_args(argv) == expected
