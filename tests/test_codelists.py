import json
import os
import shutil
from pathlib import Path
from urllib.parse import parse_qs

import pytest
from requests_mock import mocker

from opensafely import codelists
from opensafely._vendor import requests


# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


@pytest.fixture
def mock_check(requests_mock):
    def _mock(response):
        mocked = requests_mock.post(
            "https://www.opencodelists.org/api/v1/check/",
            json=response,
            # require that the POST request has the correct headers (e.g. User-Agent)
            request_headers=codelists.request_headers(),
        )
        return mocked

    return _mock


@pytest.fixture(autouse=True)
def not_ci(monkeypatch):
    if "GITHUB_WORKFLOW" in os.environ:
        monkeypatch.delenv("GITHUB_WORKFLOW")


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
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version2/download.csv",
        text="foo",
        # require that the GET request has the correct headers (e.g. User-Agent)
        request_headers=codelists.request_headers(),
        headers={"content-type": "text/csv"},
    )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/user/user123/codelist098/version1/download.csv",
        text="bar",
        # require that the GET request has the correct headers (e.g. User-Agent)
        request_headers=codelists.request_headers(),
        headers={"content-type": "text/csv"},
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


def test_codelists_check(mock_check, codelists_path):
    mock_check(response={"status": "ok"})
    os.chdir(codelists_path)
    assert codelists.check()


def test_codelists_check_passes_if_opencodelists_is_down(requests_mock, codelists_path):
    requests_mock.post(
        "https://www.opencodelists.org/api/v1/check/",
        exc=requests.exceptions.ConnectionError,
    )
    os.chdir(codelists_path)
    assert codelists.check()


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


def test_codelists_check_fail_if_invalid_manifest_file(codelists_path):
    filename = codelists_path / "codelists" / "codelists.json"
    filename.write_text("blah")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.check()


def test_codelists_parse_fail_if_no_codelists_dir(tmp_path):
    os.chdir(tmp_path)
    with pytest.raises(SystemExit):
        codelists.parse_codelist_file(tmp_path)


def test_codelists_parse_fail_if_different_versions_of_same_list(codelists_path):
    with open(codelists_path / "codelists/codelists.txt", "a") as f:
        f.write("\nsomeproject/somelist/someversion")
        f.write("\nsomeproject/somelist/differentversion")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.parse_codelist_file(codelists_path / "codelists")


def test_codelists_parse_fail_if_duplicate_lines(codelists_path):
    with open(codelists_path / "codelists/codelists.txt", "a") as f:
        f.write("\nsomeproject/somelist/someversion")
        f.write("\nsomeproject/somelist/someversion")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.parse_codelist_file(codelists_path / "codelists")


def test_codelists_parse_fail_if_bad_codelist(codelists_path):
    with open(codelists_path / "codelists/codelists.txt", "a") as f:
        f.write("\nsomeproject/somelist/")
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.parse_codelist_file(codelists_path / "codelists")


def test_codelists_parse_fail_if_codelist_file_does_not_exist(codelists_path):
    (codelists_path / "codelists/codelists.txt").unlink()
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.parse_codelist_file(codelists_path / "codelists")


def test_codelists_parse_pass_if_different_lists_have_same_version(codelists_path):
    with open(codelists_path / "codelists/codelists.txt", "a") as f:
        f.write("\nsomeproject/somelist/someversion")
        f.write("\nsomeuser/anotherproject/somelist/someversion")
    os.chdir(codelists_path)
    assert codelists.parse_codelist_file(codelists_path / "codelists")


def test_codelists_check_upstream_passes_if_no_codelists_dir(tmp_path):
    os.chdir(tmp_path)
    assert codelists.check_upstream()


def test_codelists_check_upstream_fails_if_no_codelists_file(tmp_path):
    os.chdir(tmp_path)
    (tmp_path / "codelists").mkdir()
    with pytest.raises(SystemExit):
        codelists.check_upstream()


def test_codelists_check_upstream_fails_if_no_manifest_file(tmp_path, mock_check):
    mock_check(response={"status": "ok"})
    os.chdir(tmp_path)
    codelists_dir = tmp_path / "codelists"
    codelists_dir.mkdir()
    (codelists_dir / "codelists.txt").touch()
    with pytest.raises(SystemExit):
        codelists.check_upstream()
    (codelists_dir / "codelists.json").touch()
    assert codelists.check_upstream()


def test_codelists_check_upstream(codelists_path, mock_check):
    mocked = mock_check(response={"status": "ok"})
    os.chdir(codelists_path)
    assert codelists.check_upstream()

    # assert content sent to opencodelists
    assert mocked.called_once
    parsed_request = parse_qs(mocked.last_request.text)
    assert list(parsed_request.keys()) == ["codelists", "manifest"]

    assert (
        parsed_request["codelists"][0]
        == (codelists_path / "codelists/codelists.txt").read_text()
    )
    assert (
        parsed_request["manifest"][0]
        == (codelists_path / "codelists/codelists.json").read_text()
    )


def test_codelists_check_upstream_with_error(codelists_path, mock_check):
    mock_check(response={"status": "error", "data": {"error": "Any unknown error"}})
    with pytest.raises(SystemExit):
        codelists.check_upstream(codelists_path / "codelists")


@pytest.mark.parametrize(
    "response",
    [
        {"added": ["org/foo/123"], "removed": [], "changed": []},
        {"added": [], "removed": ["org/foo/123"], "changed": []},
        {"added": [], "removed": [], "changed": ["org/foo/123"]},
        {"added": ["org/bar/123"], "removed": [], "changed": ["org/foo/123"]},
    ],
)
def test_codelists_check_upstream_with_changes(codelists_path, mock_check, response):
    mock_check(response={"status": "error", "data": response})
    with pytest.raises(SystemExit):
        codelists.check_upstream(codelists_path / "codelists")


def test_codelists_check_with_upstream_changes(codelists_path, mock_check):
    mock_check(
        response={
            "status": "error",
            "data": {"added": [], "removed": [], "changed": ["org/foo/123"]},
        }
    )
    os.chdir(codelists_path)
    with pytest.raises(SystemExit):
        codelists.check()


def test_codelists_check_with_upstream_changes_in_CI(
    codelists_path, mock_check, monkeypatch
):
    monkeypatch.setenv("GITHUB_WORKFLOW", "test")
    mock_check(
        response={
            "status": "error",
            "data": {"added": [], "removed": [], "changed": ["org/foo/123"]},
        }
    )
    os.chdir(codelists_path)
    # check doesn't fail in CI if there are upstream errors only
    assert codelists.check()


def test_codelists_add(codelists_path, requests_mock):
    codelists_path /= "codelists"
    codelists_file = codelists_path / "codelists.txt"
    prior_codelists = codelists_file.read_text()
    for codelist in prior_codelists.splitlines():
        requests_mock.get(
            f"https://www.opencodelists.org/codelist/{codelist.rstrip('/')}/download.csv",
            text="foo",
            headers={"content-type": "text/csv"},
        )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version1/download.csv",
        text="foo",
        headers={"content-type": "text/csv"},
    )

    codelists.add(
        "https://www.opencodelists.org/codelist/project123/codelist456/version1",
        codelists_path,
    )

    assert (
        codelists_file.read_text()
        == prior_codelists + "project123/codelist456/version1\n"
    )
    assert (codelists_path / "project123-codelist456.csv").read_text() == "foo"


def test_codelists_add_with_anchor_url(codelists_path, requests_mock):
    codelists_path /= "codelists"
    codelists_file = codelists_path / "codelists.txt"
    prior_codelists = codelists_file.read_text()
    for codelist in prior_codelists.split("\n"):
        if codelist:
            requests_mock.get(
                f"https://www.opencodelists.org/codelist/{codelist.rstrip('/')}/download.csv",
                text="foo",
                headers={"content-type": "text/csv"},
            )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version1/download.csv",
        text="foo",
        headers={"content-type": "text/csv"},
    )

    codelists.add(
        "https://www.opencodelists.org/codelist/project123/codelist456/version1/#full-list",
        codelists_path,
    )

    assert (
        codelists_file.read_text()
        == prior_codelists + "project123/codelist456/version1/\n"
    )
    assert (codelists_path / "project123-codelist456.csv").read_text() == "foo"


def test_codelists_add_with_download_url(codelists_path, requests_mock):
    codelists_path /= "codelists"
    codelists_file = codelists_path / "codelists.txt"
    prior_codelists = codelists_file.read_text()
    for codelist in prior_codelists.split("\n"):
        if codelist:
            requests_mock.get(
                f"https://www.opencodelists.org/codelist/{codelist.rstrip('/')}/download.csv",
                text="foo",
                headers={"content-type": "text/csv"},
            )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version1/download.csv",
        text="foo",
        headers={"content-type": "text/csv"},
    )

    codelists.add(
        "https://www.opencodelists.org/codelist/project123/codelist456/version1/download.csv",
        codelists_path,
    )

    assert (
        codelists_file.read_text()
        == prior_codelists + "project123/codelist456/version1\n"
    )
    assert (codelists_path / "project123-codelist456.csv").read_text() == "foo"


def test_codelists_add_with_invalid_url(codelists_path):
    codelists_path /= "codelists"

    with pytest.raises(SystemExit):
        codelists.add("https://example.com/codelists/test/")


def test_codelists_add_with_draft_url(codelists_path, requests_mock, capsys):
    codelists_path /= "codelists"
    codelists_file = codelists_path / "codelists.txt"
    prior_codelists = codelists_file.read_text()
    for codelist in prior_codelists.splitlines():
        requests_mock.get(
            f"https://www.opencodelists.org/codelist/{codelist.rstrip('/')}/download.csv",
            text="foo",
        )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version1/download.csv",
        text="""
            <!DOCTYPE html>
            <html lang="en" class="h-100">
            <head>
            <meta charset="utf-8" />
            <title>OpenCodelists: Test Codelist 456 (Draft)</title>
            </head>
            <body>
            <div>
                <h1 class="h3">Test Codelist 456</h1>
                <p class="text-muted">This version is a draft</p>
            </div>
            </body>
            </html>
        """,
        headers={"content-type": "text/html; charset=utf-8"},
    )

    with pytest.raises(SystemExit):
        codelists.add(
            "https://www.opencodelists.org/codelist/project123/codelist456/version1",
            codelists_path,
        )
    stdout, _ = capsys.readouterr()
    assert "is a draft codelist and cannot be added" in stdout


def test_codelists_add_with_valid_non_codelist_url(
    codelists_path, requests_mock, capsys
):
    codelists_path /= "codelists"
    codelists_file = codelists_path / "codelists.txt"
    prior_codelists = codelists_file.read_text()
    for codelist in prior_codelists.splitlines():
        requests_mock.get(
            f"https://www.opencodelists.org/codelist/{codelist.rstrip('/')}/download.csv",
            text="foo",
        )
    requests_mock.get(
        "https://www.opencodelists.org/"
        "codelist/project123/codelist456/version1/download.csv",
        text="""
            <!DOCTYPE html>
            <html lang="en" class="h-100">
            <head>
            <meta charset="utf-8" />
            <title>Some Other Page</title>
            </head>
            <body>
            <div>
                <h1 class="h3">This is not a codelist</h1>
                <p class="text-muted">It cannot meaningfully be downloaded</p>
            </div>
            </body>
            </html>
        """,
        headers={"content-type": "text/html; charset=utf-8"},
    )

    with pytest.raises(SystemExit):
        codelists.add(
            "https://www.opencodelists.org/codelist/project123/codelist456/version1",
            codelists_path,
        )
    stdout, _ = capsys.readouterr()
    assert "No codelist found at URL" in stdout


def test_user_agent_value(set_current_version):
    version = "v.1.0.0"
    set_current_version(version)
    headers = codelists.request_headers()
    assert headers["User-Agent"] == f"OpenSAFELY-CLI/{version.lstrip('v')}"
