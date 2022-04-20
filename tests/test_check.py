from collections import Counter
import itertools
import os
import subprocess
import textwrap
from enum import Enum
from pathlib import Path

import pytest
from requests_mock import mocker
from opensafely._vendor.ruamel.yaml import YAML

from opensafely import check
from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml.comments import CommentedMap
from opensafely._vendor.requests.exceptions import RequestException

# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


def flatten_list(nested_list):
    return sum([sublist for sublist in nested_list], [])


class Protocol(Enum):
    HTTPS = 1
    SSH = 2
    ENVIRON = 3


UNRESTRICTED_FUNCTION = "with_these_medications"


@pytest.fixture
def repo_path(tmp_path):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(prev_dir)


def get_permissions_fixture_data():
    permissions_file = (
        Path(__file__).parent
        / "fixtures"
        / "permissions"
        / "repository_permissions.yaml"
    )
    permissions_text = permissions_file.read_text()
    permissions_dict = YAML().load(permissions_text)
    return permissions_text, permissions_dict


def all_test_repos():
    _, permissions = get_permissions_fixture_data()
    unknown_repo = "opensafely/dummy"
    assert unknown_repo not in permissions
    return [*permissions, unknown_repo, None]


def format_function_call(func):
    return (
        f"patients.{func}("
        "between=['2021-01-01','2022-02-02'], "
        "find_first_match_in_period=True, "
        "returning='binary_flag')"
    )


def write_study_def(path, include_restricted):
    filename_part = "restricted" if include_restricted else "unrestricted"
    all_restricted_functions = flatten_list(check.RESTRICTED_DATASETS.values())

    for a in [1, 2]:
        # generate the filename; we make 2 versions to test that all study defs are checked
        filepath = path / f"study_definition_{filename_part}_{a}.py"

        # Build the function calls for the test's study definition.  We name each variable with
        # the function name itself, to make checking the outputs easier

        # if we're included restricted functions, create a function call for each one
        # these will cause check fails depending on the test repo's permissions
        if include_restricted:
            restricted = [
                f"{name}_name={format_function_call(name)},"
                for name in all_restricted_functions
            ]
        else:
            restricted = []
        restricted_lines = "\n".join(restricted)
        # create a commented-out function call for each restricted function
        # include these in all test study defs; always allowed
        restricted_commented_lines = "\n".join(
            [
                f"#{name}_commented={format_function_call(name)},"
                for name in all_restricted_functions
            ]
        )
        # create a function call an unrestricted function;
        # include in all test study defs; this is always allowed
        unrestricted = (
            f"{UNRESTRICTED_FUNCTION}={format_function_call(UNRESTRICTED_FUNCTION)},"
        )

        filepath.write_text(
            textwrap.dedent(
                f"""
                from cohortextractor import StudyDefinition, patients

                study = StudyDefinition (
                {restricted_lines}
                {restricted_commented_lines}
                {unrestricted}
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


def validate_fail(capsys, continue_on_error, permissions):
    def validate_fail_output(stdout, stderr):
        assert stdout != "Success\n"
        assert "Usage of restricted datasets found:" in stderr

        for dataset_name, function_list in check.RESTRICTED_DATASETS.items():
            for function_name in function_list:
                # commented out functions are never in error output, even if restricted
                assert f"#{function_name}_commented" not in stderr
            if dataset_name in permissions:
                assert dataset_name not in stderr
                assert f"{function_name}_name" not in stderr
            else:
                assert dataset_name in stderr, permissions
                assert f"{function_name}_name" in stderr

        # unrestricted function is never in error output
        assert UNRESTRICTED_FUNCTION not in stderr
        # Both study definition files are reported
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


def test_permissions_fixture_data_complete():
    """
    This test is just to test the permissions test fixture, to ensure:
    1) that we've included all the restricted datasets
    2) that at least one test repo has access to all restricted datasets
    """
    _, permissions_dict = get_permissions_fixture_data()

    restricted_datasets = set(check.RESTRICTED_DATASETS.keys())

    all_allowed_repo = None
    # find repo with all restricted datasets
    for repo, allowed_dict in permissions_dict.items():
        allowed = set(allowed_dict.get("allow", []))
        if not (restricted_datasets - allowed):
            all_allowed_repo = repo
            break

    assert (
        all_allowed_repo is not None
    ), """
        No repo found with access to all restricted datasets.  
        If you added a new restricted dataset, make sure 
        tests/fixtures/permissions/repository-permissions.yaml has been updated.
        """

    flattened_permitted_datasets = flatten_list(
        [
            dataset_permissions["allow"]
            for dataset_permissions in permissions_dict.values()
        ]
    )
    permitted_dataset_counts = Counter(flattened_permitted_datasets)

    for dataset in restricted_datasets:
        assert (
            permitted_dataset_counts[dataset] > 1
        ), f"No part-restricted repo found for restricted dataset {dataset}"


@pytest.mark.parametrize(
    "repo, protocol, include_restricted, continue_on_error",
    itertools.chain(
        itertools.product(
            all_test_repos(), list(Protocol), [True, False], [True, False]
        ),
        itertools.product([None], [None], [True, False], [True, False]),
    ),
)
def test_check(
    repo_path,
    capsys,
    monkeypatch,
    requests_mock,
    repo,
    protocol,
    include_restricted,
    continue_on_error,
):
    if "GITHUB_REPOSITORY" in os.environ:
        monkeypatch.delenv("GITHUB_REPOSITORY")

    # Mock the call to the permissions URL to return the contents of our test permissions file
    permissions_text, permissions_dict = get_permissions_fixture_data()
    requests_mock.get(check.PERMISSIONS_URL, text=permissions_text)

    write_study_def(repo_path, include_restricted)

    if repo:
        if protocol == Protocol.ENVIRON:
            monkeypatch.setenv("GITHUB_REPOSITORY", repo)
        else:
            if protocol == Protocol.SSH:
                url = f"git@github.com:{repo}.git"
            elif protocol == Protocol.HTTPS:
                url = f"https://github.com/{repo}"
            else:
                url = ""
            git_init(url)

    repo_permissions = permissions_dict.get(repo, {}).get("allow", [])
    # are the restricted datasets all in repo's permitted dataset?
    # Some repos in the test fixtures list "ons", which is an allowed dataset;
    # ignore any datasets listed in the repo's permissions that are not restricted
    all_allowed = not (set(check.RESTRICTED_DATASETS.keys()) - set(repo_permissions))

    if not repo and not include_restricted:
        validate_norepo(capsys, continue_on_error)
    elif include_restricted and not all_allowed:
        validate_fail(
            capsys, continue_on_error, permissions_dict.get(repo, {}).get("allow", [])
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
