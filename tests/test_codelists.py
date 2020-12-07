import os

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
        "project123/codelist456/version2\n  \nproject123/codelist098/version1\n"
    )
    os.chdir(tmp_path)
    requests_mock.get(
        "https://codelists.opensafely.org/"
        "codelist/project123/codelist456/version2/download.csv",
        text="foo",
    )
    requests_mock.get(
        "https://codelists.opensafely.org/"
        "codelist/project123/codelist098/version1/download.csv",
        text="bar",
    )
    codelists.update()
    assert (codelist_dir / "project123-codelist456.csv").read_text() == "foo"
    assert not (codelist_dir / "project123-codelist789-version1.csv").exists()
    assert (codelist_dir / "project123-codelist098.csv").read_text() == "bar"
