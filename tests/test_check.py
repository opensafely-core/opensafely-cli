import pytest
from requests_mock import mocker
from opensafely._vendor import requests
from opensafely import check
import os
import subprocess
import textwrap
from enum import Enum
import itertools

# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send

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


def write_study_def(path, restricted):
    for a in [1, 2]:
        f = (
            path
            / f"study_definition_{'' if restricted else 'un'}restricted_{a}.py"
        )
        f.write_text(
            textwrap.dedent(
                f"""\
                {STUDY_DEF_HEADER}
                {'' if restricted else '#'}a={RESTRICTED_FUNCTION_CALL},
                #b={RESTRICTED_FUNCTION_CALL},
                c={UNRESTRICTED_FUNCTION_CALL},
                #d={UNRESTRICTED_FUNCTION_CALL},
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


@pytest.mark.parametrize(
    "repo, protocol, restricted",
    itertools.chain(
        itertools.product(list(Repo), list(Protocol), [True, False]),
        itertools.product([None], [None], [True, False]),
    ),
)
def test_check(repo_path, capsys, monkeypatch, repo, protocol, restricted):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    write_study_def(repo_path, restricted)

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
