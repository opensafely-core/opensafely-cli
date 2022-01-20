import itertools
import os
import subprocess
import textwrap
from enum import Enum

import pytest
from requests_mock import mocker

from opensafely import check
from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml.comments import CommentedMap

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

PERMISSIONS_URL = "https://raw.githubusercontent.com/opensafely-core/opensafely-cli/main/tests/fixtures/permissions/repository_permisisons.yaml"


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


def validate_pass(capsys, continue_on_error):
    check.main(continue_on_error)
    stdout, stderr = capsys.readouterr()
    if not continue_on_error:
        assert stderr == ""
        assert stdout == "Success\n"
    else:
        assert stdout == ""


def validate_fail(capsys, continue_on_error):
    def validate_fail_output(stdout, stderr):
        assert stdout != "Success\n"
        assert (
            "Usage of restricted datasets found:" in stderr
            or "git config" in stderr.lower()
        )
        if "Usage of restricted datasets found:" in stderr:
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

    if not continue_on_error:
        with pytest.raises(SystemExit):
            check.main(continue_on_error)
            stdout, stderr = capsys.readouterr()
            validate_fail_output(stdout, stderr)

    else:
        check.main(continue_on_error)
        stdout, stderr = capsys.readouterr()
        validate_fail_output(stdout, stdout)


@pytest.fixture
def repo_path(tmp_path):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev_dir)


@pytest.mark.parametrize(
    "repo, protocol, dataset, continue_on_error",
    itertools.chain(
        itertools.product(
            list(Repo), list(Protocol), list(Dataset), [True, False]
        ),
        itertools.product([None], [None], list(Dataset), [True, False]),
    ),
)
def test_check(
    repo_path, capsys, monkeypatch, repo, protocol, dataset, continue_on_error
):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    monkeypatch.setenv("OPENSAFELY_PERMISSIONS_URL", PERMISSIONS_URL)

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

    if not repo or (
        dataset == Dataset.RESTRICTED
        and repo
        not in [
            Repo.PERMITTED,
            Repo.PERMITTED_MULTIPLE,
        ]
    ):
        validate_fail(capsys, continue_on_error)
    else:
        validate_pass(capsys, continue_on_error)


def test_repository_permissions_yaml():
    permissions = check.get_datasource_permissions(check.PERMISSIONS_URL)
    assert permissions, "empty permissions file"
    assert type(permissions) == CommentedMap, "invalid permissions file"
    for k, v in permissions.items():
        assert len(v.keys()) == 1, f"multiple keys specified for {k}"
        assert "allow" in v.keys(), f"allow key not present for {k}"
