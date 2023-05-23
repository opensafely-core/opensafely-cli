import argparse
import sys

import pytest
from requests_mock import mocker

import opensafely
from opensafely import upgrade
from opensafely._vendor import requests


# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


@pytest.fixture
def set_current_version(monkeypatch):
    def set(value):  # noqa: A001
        assert value[0] == "v", "Current __version__ must start with v"
        monkeypatch.setattr(opensafely, "__version__", value)

    yield set


@pytest.fixture
def set_pypi_version(requests_mock):
    def set(version):  # noqa: A001
        requests_mock.get(
            "https://pypi.org/pypi/opensafely/json",
            json={"info": {"version": version}},
        )

    return set


def test_main_latest_upgrade(set_pypi_version, run, set_current_version):
    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")
    run.expect(
        [sys.executable, "-m", "pip", "install", "--upgrade", "opensafely==1.1.0"]
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


def test_check_version_needs_updating(set_current_version, set_pypi_version, capsys):
    set_pypi_version("1.1.0")
    set_current_version("v1.0.0")
    assert upgrade.check_version()
    _, err = capsys.readouterr()
    assert err.splitlines() == [
        "Warning: there is a newer version of opensafely available (1.1.0) - please upgrade by running:",
        "    opensafely upgrade",
        "",
    ]


def test_check_version_not_need_updating(set_current_version, set_pypi_version, capsys):
    set_pypi_version("1.0.0")
    set_current_version("v1.0.0")
    assert not upgrade.check_version()
    out, _ = capsys.readouterr()
    assert out.strip() == ""


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
