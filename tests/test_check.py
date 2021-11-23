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


class Dataset(Enum):
    RESTRICTED = True
    UNRESTRICTED = False


STUDY_DEF_HEADER = """from cohortextractor import (StudyDefinition, patients)
study = StudyDefinition ("""


UNRESTRICTED_FUNCTION = "with_these_medications"
RESTRICTED_FUNCTION = "admitted_to_icu"


def format_function_call(func):
    return (
        f"patients.{func}("
        "between=['2021-01-01','2022-02-02'], "
        "find_first_match_in_period=True, "
        "returning='binary_flag')"
    )


def write_study_def(path, dataset):
    restricted = dataset.value
    for a in [1, 2]:
        f = (
            path
            / f"study_definition_{'' if restricted else 'un'}restricted_{a}.py"
        )
        f.write_text(
            textwrap.dedent(
                f"""\
                {STUDY_DEF_HEADER}
                {'a='+format_function_call(RESTRICTED_FUNCTION)+',' if restricted else ''}
                #b={format_function_call(RESTRICTED_FUNCTION)},
                c={format_function_call(UNRESTRICTED_FUNCTION)},
                #d={format_function_call(UNRESTRICTED_FUNCTION)},
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
    "repo, protocol, dataset",
    itertools.chain(
        itertools.product(list(Repo), list(Protocol), list(Dataset)),
        itertools.product([None], [None], list(Dataset)),
    ),
)
def test_check(repo_path, capsys, monkeypatch, repo, protocol, dataset):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    write_study_def(repo_path, dataset)

    if repo:
        repo_name = repo.value
        if protocol == Protocol.ENVIRON:
            monkeypatch.setenv("GITHUB_REPOSITORY", repo_name)
        else:
            if protocol == Protocol.SSH:
                url = f"git@github.com:{repo_name}.git"
            elif protocol == Protocol.HTTPS:
                url = f"https://github.com/{repo_name}"
            else:
                url = ""
            git_init(url)

    if dataset.value and repo not in [Repo.PERMITTED, Repo.PERMITTED_MULTIPLE]:
        validate_fail(capsys)
    else:
        validate_pass(capsys)
