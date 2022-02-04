import itertools
import os
import subprocess
import textwrap
from enum import Enum
from pathlib import Path

import pytest
from requests_mock import mocker

from opensafely import check
from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml.comments import CommentedMap
from opensafely._vendor.requests.exceptions import RequestException

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
opensafely/dummy_therapeutics:
    allow: ['therapeutics']
opensafely/dummy_isaric:
    allow: ['isaric']
opensafely/dummy_all:
    allow: ['icnarc','ons','therapeutics', 'isaric]
"""


class Repo(Enum):
    PERMITTED_ICNARC = "opensafely/dummy_icnarc"
    PERMITTED_THERAPEUTICS = "opensafely/dummy_therapeutics"
    PERMITTED_ISARIC = "opensafely/dummy_isaric"
    PERMITTED_MULTIPLE = "opensafely/dummy_icnarc_ons"
    PERMITTED_ALL = "opensafely/dummy_all"
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
RESTRICTED_FUNCTIONS = ["admitted_to_icu", "with_covid_therapeutics", "with_an_isaric_record"]


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
                a={format_function_call(RESTRICTED_FUNCTIONS[0])+',' if restricted else ''}
                #b={format_function_call(RESTRICTED_FUNCTIONS[0])},
                c={format_function_call(RESTRICTED_FUNCTIONS[1])+',' if restricted else ''},
                #d={format_function_call(RESTRICTED_FUNCTIONS[1])},
                e={format_function_call(RESTRICTED_FUNCTIONS[2])+',' if restricted else ''},
                #f={format_function_call(RESTRICTED_FUNCTIONS[2])},
                y={format_function_call(UNRESTRICTED_FUNCTION)},
                #z={format_function_call(UNRESTRICTED_FUNCTION)},
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


def validate_fail(capsys, continue_on_error, not_permitted, permitted):
    def validate_fail_output(stdout, stderr):
        assert stdout != "Success\n"
        assert "Usage of restricted datasets found:" in stderr
        for not_permitted_dataset_values in not_permitted:
            np_name, np_function, np_error_line = not_permitted_dataset_values
            assert np_name in stderr
            assert np_function in stderr
            assert np_error_line in stderr
        
        for permitted_dataset_values in permitted:
            p_name, p_function, p_error_line = permitted_dataset_values
            assert p_name not in stderr
            assert p_function not in stderr
            assert p_error_line not in stderr
        assert "4:" not in stderr
        assert "#b=" not in stderr
        assert "#y=" not in stderr
        assert "#z=" not in stderr
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


def validate_norepo(capsys, continue_on_error):
    if not continue_on_error:
        with pytest.raises(SystemExit):
            check.main(continue_on_error)
            stdout, stderr = capsys.readouterr()
            assert "git config" in stdout.lower()
            assert "Unable to find repository name" in stderr
    else:
        check.main(continue_on_error)
        stdout, stderr = capsys.readouterr()
        assert stderr == ""
        assert stdout == ""


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
    repo_path, capsys, monkeypatch, requests_mock, repo, protocol, dataset, continue_on_error
):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    # Mock the call to the permissions URL to return the contents of our test permissions file
    permissions_file = Path(__file__).parent / "fixtures" / "permissions" / "repository_permissions.yaml"
    requests_mock.get(check.PERMISSIONS_URL, text=permissions_file.read_text())   
    
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

    if not repo and dataset != Dataset.RESTRICTED:
        validate_norepo(capsys, continue_on_error)
    elif dataset == Dataset.RESTRICTED and repo != Repo.PERMITTED_ALL:
        icnarc = ("icnarc", "admitted_to_icu", "3")
        theraputics = ("therapeutics", "with_covid_therapeutics", "5")
        isaric = ("isaric", "with_an_isaric_record", "7")
        
        permitted_mapping = {
            "permitted": {
                Repo.PERMITTED_ICNARC: (icnarc,),
                Repo.PERMITTED_THERAPEUTICS: (theraputics,),
                Repo.PERMITTED_ISARIC: (isaric,),
                Repo.PERMITTED_MULTIPLE: (icnarc,),
                Repo.UNKNOWN: (),
                Repo.UNPERMITTED: (),
                None: (),
            },
            "not_permitted": {
                Repo.PERMITTED_ICNARC: (theraputics, isaric),
                Repo.PERMITTED_THERAPEUTICS: (icnarc, isaric),
                Repo.PERMITTED_ISARIC: (icnarc, theraputics),
                Repo.PERMITTED_MULTIPLE: (theraputics, isaric),
                Repo.UNKNOWN: (icnarc, theraputics, isaric),
                Repo.UNPERMITTED: (icnarc, theraputics, isaric),
                None: (icnarc, theraputics, isaric),
            }
        }
        validate_fail(
            capsys, 
            continue_on_error, 
            not_permitted=permitted_mapping["not_permitted"][repo],
            permitted=permitted_mapping["permitted"][repo]
        )
    else:
        validate_pass(capsys, continue_on_error)


def test_repository_permissions_yaml():
    try:
        permissions = check.get_datasource_permissions(check.PERMISSIONS_URL)
    except RequestException as e:
        # This test should always pass on main, but if we've renamed the file
        # on the branch, it will fail before it's merged
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if branch != "main" and "Error 404" in str(e):
            pytest.xfail("Permissions file does not exist on main yet") 

    assert permissions, "empty permissions file"
    assert type(permissions) == CommentedMap, "invalid permissions file"
    for k, v in permissions.items():
        assert len(v.keys()) == 1, f"multiple keys specified for {k}"
        assert "allow" in v.keys(), f"allow key not present for {k}"
