import pytest
from requests_mock import mocker
from opensafely._vendor import requests
from opensafely import check
import os
import subprocess
import textwrap
from enum import Enum

# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


RESTRICTED_FUNCTION_CALL = (
    "patients.admitted_to_icu("
    "between=['2021-01-01','2022-02-02'], "
    "find_first_match_in_period=True, "
    "returning='binary_flag')"
)

UNRESTRICTED_FUNCTION_CALL = (
    "patients.with_these_medications("
    "between=['2021-01-01','2022-02-02'], "
    "find_first_match_in_period=True, "
    "returning='binary_flag')"
)


PERMISSIONS_TEXT = """
opensafely/dummy_icnarc:
    allow: ['icnarc']
opensafely/dummy_ons:
    allow: ['ons']
opensafely/dummy_icnarc_ons:
    allow: ['icnarc','ons']
"""


class Repo(Enum):
    PERMITTED = "opensafely/dummy_icnarc"
    PERMITTED_MULTIPLE = "opensafely/dummy_icnarc_ons"
    UNPERMITTED = "opensafely/dummy_ons"
    UNKNOWN = "opensafely/dummy"


class Protocol(Enum):
    HTTPS = 1
    SSH = 2
    ENVIRON = 3


STUDY_DEF_HEADER = """from cohortextractor import (StudyDefinition, patients)
study = StudyDefinition ("""


def write_restricted_files(path):
    for a in [1, 2]:
        f = path / f"study_definition_restricted_{a}.py"
        f.write_text(
            textwrap.dedent(
                f"""\
                {STUDY_DEF_HEADER}
                a={RESTRICTED_FUNCTION_CALL},
                #b={RESTRICTED_FUNCTION_CALL},
                c={UNRESTRICTED_FUNCTION_CALL},
                #d={UNRESTRICTED_FUNCTION_CALL},
                )"""
            )
        )


def write_unrestricted_files(path):
    for a in [1, 2]:
        f = path / f"study_definition_unrestricted_{a}.py"
        f.write_text(
            textwrap.dedent(
                f"""\
                {STUDY_DEF_HEADER}
                #a={RESTRICTED_FUNCTION_CALL},
                b={UNRESTRICTED_FUNCTION_CALL},
                #c={UNRESTRICTED_FUNCTION_CALL},
                )"""
            )
        )


def git_init(url):
    subprocess.run(["git", "init"])
    subprocess.run(["git", "remote", "add", "origin", url])


def validate_pass(capsys):
    check.main()
    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    assert stdout == "Success\n"


def validate_fail(capsys):
    with pytest.raises(SystemExit):
        check.main()
        stdout, stderr = capsys.readouterr()
        assert stdout != "Success\n"
        assert stderr.startswith("Usage of restricted datasets found:")
        assert "icnarc" in stderr
        assert "admitted_to_icu" in stderr
        assert "3:" in stderr
        assert "4:" not in stderr
        assert "5:" not in stderr
        assert "#b=" not in stderr
        assert "#d=" not in stderr
        assert "unrestricted" not in stderr
        assert "study_definition_restricted_1.py" in stderr
        assert "study_definition_restricted_2.py" in stderr


@pytest.fixture
def repo_path(tmp_path):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev_dir)


def run_test(repo_path, capsys, monkeypatch, repo, protocol, restricted):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    if restricted:
        write_restricted_files(repo_path)
    else:
        write_unrestricted_files(repo_path)

    if repo:
        if protocol == Protocol.ENVIRON:
            monkeypatch.setenv("GITHUB_REPOSITORY", repo.value)
        else:
            if protocol == Protocol.SSH:
                url = f"git@github.com:{repo.value}.git"
            elif protocol == Protocol.HTTPS:
                url = f"https://github.com/{repo.value}"
            else:
                url = ""
            git_init(url)

    if restricted and repo not in [Repo.PERMITTED, Repo.PERMITTED_MULTIPLE]:
        validate_fail(capsys)
    else:
        validate_pass(capsys)


def test_unrestricted_local_norepo(repo_path, capsys, monkeypatch):
    run_test(repo_path, capsys, monkeypatch, repo=None, protocol=None, restricted=False)


def test_restricted_local_norepo(repo_path, capsys, monkeypatch):
    run_test(repo_path, capsys, monkeypatch, repo=None, protocol=None, restricted=True)


def test_unrestricted_unknown_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.HTTPS,
        restricted=False,
    )


def test_unrestricted_unknown_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.SSH,
        restricted=False,
    )


def test_unrestricted_permitted_multiple_local_https(
    repo_path, capsys, monkeypatch
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.HTTPS,
        restricted=False,
    )


def test_unrestricted_permitted_multiple_local_ssh(
    repo_path, capsys, monkeypatch
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.SSH,
        restricted=False,
    )


def test_restricted_unknown_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.HTTPS,
        restricted=True,
    )


def test_restricted_unknown_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.SSH,
        restricted=True,
    )


def test_restricted_permitted_multiple_local_https(
    repo_path, capsys, monkeypatch
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.HTTPS,
        restricted=True,
    )


def test_restricted_permitted_multiple_local_ssh(
    repo_path, capsys, monkeypatch
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.SSH,
        restricted=True,
    )


def test_restricted_permitted_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.HTTPS,
        restricted=True,
    )


def test_restricted_permitted_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED,
        Protocol.SSH,
        restricted=True,
    )


def test_unrestricted_permitted_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED,
        Protocol.HTTPS,
        restricted=False,
    )


def test_unrestricted_permitted_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED,
        Protocol.SSH,
        restricted=False,
    )


def test_restricted_unpermitted_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.HTTPS,
        restricted=True,
    )


def test_restricted_unpermitted_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.SSH,
        restricted=True,
    )


def test_unrestricted_unpermitted_local_https(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.HTTPS,
        restricted=False,
    )


def test_unrestricted_unpermitted_local_ssh(repo_path, capsys, monkeypatch):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.SSH,
        restricted=False,
    )


def test_unrestricted_unpermitted_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.ENVIRON,
        restricted=False,
    )


def test_unrestricted_permitted_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED,
        Protocol.ENVIRON,
        restricted=False,
    )


def test_restricted_permitted_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED,
        Protocol.ENVIRON,
        restricted=True,
    )


def test_restricted_unpermitted_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNPERMITTED,
        Protocol.ENVIRON,
        restricted=True,
    )


def test_restricted_permitted_multiple_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.ENVIRON,
        restricted=True,
    )


def test_unrestricted_permitted_multiple_action(
    monkeypatch, repo_path, capsys
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.PERMITTED_MULTIPLE,
        Protocol.ENVIRON,
        restricted=False,
    )


def test_restricted_unknown_action(monkeypatch, repo_path, capsys):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.ENVIRON,
        restricted=True,
    )


def test_unrestricted_nonexistent_multiple_action(
    monkeypatch, repo_path, capsys
):
    run_test(
        repo_path,
        capsys,
        monkeypatch,
        Repo.UNKNOWN,
        Protocol.ENVIRON,
        restricted=True,
    )
