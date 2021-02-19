import argparse
from datetime import datetime, timedelta
import os

import pytest

import opensafely
from opensafely import upgrade

from requests_mock import mocker
from opensafely._vendor import requests

# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


@pytest.fixture(autouse=True)
def clean_cache_file():
    upgrade.CACHE_FILE.unlink(missing_ok=True)


@pytest.fixture
def set_current_version(monkeypatch):
    def set(value):
        assert value[0] == "v", "Current __version__ must start with v"
        monkeypatch.setattr(opensafely, "__version__", value)

    yield set


def test_main_latest_upgrade(requests_mock, run, set_current_version):
    requests_mock.get(
        "https://pypi.org/pypi/opensafely/json",
        json={"info": {"version": "1.1.0"}},
    )
    set_current_version("v1.0.0")
    run.expect(["pip", "install", "--upgrade", "opensafely==1.1.0"])
    upgrade.main("latest")


def test_main_latest_no_upgrade(requests_mock, run, set_current_version, capsys):
    requests_mock.get(
        "https://pypi.org/pypi/opensafely/json",
        json={"info": {"version": "1.0.0"}},
    )
    set_current_version("v1.0.0")
    upgrade.main("latest")
    out, err = capsys.readouterr()
    assert out.strip() == "opensafely is already at version 1.0.0"


def test_main_specifi_no_upgrade(run, set_current_version, capsys):
    set_current_version("v1.1.0")
    upgrade.main("1.1.0")
    out, err = capsys.readouterr()
    assert out.strip() == "opensafely is already at version 1.1.0"


def test_get_latest_version_no_cache(requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/opensafely/json",
        json={"info": {"version": "1.1.0"}},
    )

    assert not upgrade.CACHE_FILE.exists()
    assert upgrade.get_latest_version() == "1.1.0"
    assert upgrade.CACHE_FILE.read_text() == "1.1.0"


def test_get_latest_version_with_cache(requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/opensafely/json",
        json={"info": {"version": "1.1.0"}},
    )
    upgrade.CACHE_FILE.write_text("1.0.0")
    assert upgrade.get_latest_version() == "1.0.0"
    assert upgrade.get_latest_version(force=True) == "1.1.0"


def test_get_latest_version_cache_expired(requests_mock):
    requests_mock.get(
        "https://pypi.org/pypi/opensafely/json",
        json={"info": {"version": "1.1.0"}},
    )
    upgrade.CACHE_FILE.write_text("1.0.0")
    # set mtime to 1 day ago
    a_day_ago = (datetime.utcnow() - timedelta(days=1)).timestamp()
    os.utime(upgrade.CACHE_FILE, (a_day_ago, a_day_ago))

    # ignores cache and uses the newer latest version from requests
    # check cache updated
    assert upgrade.get_latest_version() == "1.1.0"
    assert upgrade.CACHE_FILE.read_text() == "1.1.0"


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


def test_check_version_needs_updating(set_current_version, capsys):
    upgrade.CACHE_FILE.write_text("1.1.0")
    set_current_version("v1.0.0")
    assert upgrade.check_version()
    out, _ = capsys.readouterr()
    assert out.strip() == (
        f"Warning: there is a newer version of opensafely available - please run 'opensafely upgrade' to update to 1.1.0"
    )


def test_check_version_needs_updating(set_current_version, capsys):
    upgrade.CACHE_FILE.write_text("1.0.0")
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
