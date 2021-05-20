import json
import os
from pathlib import Path
import shutil

import pytest
from requests_mock import mocker

from opensafely._vendor import requests
from opensafely import codelists

# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


def test_codelists_update(tmp_path, requests_mock):
    codelist_dir = tmp_path / "codelists"
    codelist_dir.mkdir()
    (codelist_dir / "project123-codelist456.csv").touch()
    (codelist_dir / "project123-codelist789.csv").touch()
    (codelist_dir / "codelists.txt").write_text(
        "project123/codelist456/version2\n  \nuser/user123/codelist098/version1\n"
    )
    os.chdir(tmp_path)
    requests_mock.get(
        "https://codelists.opensafely.org/"
        "codelist/project123/codelist456/version2/download.csv",
        text="foo",
    )
    requests_mock.get(
        "https://codelists.opensafely.org/"
        "codelist/user/user123/codelist098/version1/download.csv",
        text="bar",
    )
    codelists.update()
    assert (codelist_dir / "project123-codelist456.csv").read_text() == "foo"
    assert not (codelist_dir / "project123-codelist789-version1.csv").exists()
    assert (codelist_dir / "user-user123-codelist098.csv").read_text() == "bar"
    manifest = json.loads((codelist_dir / "codelists.json").read_text())
    assert manifest["files"].keys() == {
        "project123-codelist456.csv",
        "user-user123-codelist098.csv",
    }


@pytest.fixture
def codelists_path(tmp_path):
    fixture_path = Path(__file__).parent / "fixtures" / "codelists"
    shutil.copytree(fixture_path, tmp_path / "codelists")
    yield tmp_path


def test_codelists_check(codelists_path):
    os.chdir(codelists_path)
    codelists.check()


def test_codelists_check_fail_if_list_updated(codelists_path):
    with open(codelists_path / "codelists/codelists.txt", "a") as f:
        f.write("\nsomeproject/somelist/someversion")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.check()


def test_codelists_check_fail_if_file_added(codelists_path):
    codelists_path.joinpath("codelists", "my-new-file.csv").touch()
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.check()


def test_codelists_check_fail_if_file_modified(codelists_path):
    filename = codelists_path / "codelists" / "opensafely-covid-identification.csv"
    filename.write_text("blah")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.check()


def test_codelists_check_passes_if_no_codelists_dir(tmp_path):
    os.chdir(tmp_path)
    assert codelists.check()
