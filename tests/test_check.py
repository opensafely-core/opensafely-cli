import pytest
from requests_mock import mocker
from opensafely._vendor import requests
from opensafely import check
import os
import subprocess

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

PERMITTED_REPO = "opensafely/dummy_icnarc"
PERMITTED_MULTIPLE_REPO = "opensafely/dummy_icnarc_ons"
UNPERMITTED_REPO = "opensafely/dummy_ons"
NONEXISTENT_REPO = "opensafely/dummy"

PERMITTED_HTTPS_ORIGIN = f"https://github.com/{PERMITTED_REPO}"
PERMITTED_MULTIPLE_HTTPS_ORIGIN = (
    f"https://github.com/{PERMITTED_MULTIPLE_REPO}"
)
UNPERMITTED_HTTPS_ORIGIN = f"https://github.com/{UNPERMITTED_REPO}"
NONEXISTENT_HTTPS_ORIGIN = f"https://github.com/{NONEXISTENT_REPO}"

PERMITTED_SSH_ORIGIN = f"git@github.com:{PERMITTED_REPO}.git"
PERMITTED_MULTIPLE_SSH_ORIGIN = f"git@github.com:{PERMITTED_MULTIPLE_REPO}.git"
UNPERMITTED_SSH_ORIGIN = f"git@github.com:{UNPERMITTED_REPO}.git"
NONEXISTENT_SSH_ORIGIN = f"git@github.com:{NONEXISTENT_REPO}.git"


STUDY_DEF_HEADER = """from cohortextractor import (StudyDefinition, patients)
study = StudyDefinition ("""

def write_restricted_files(path):
    for a in [1, 2]:
        with open(
            os.path.join(str(path), f"study_definition_restricted_{a}.py"), "w"
        ) as f:
            f.write(f"{STUDY_DEF_HEADER}\n")
            f.write(f"a={RESTRICTED_FUNCTION_CALL},\n")
            f.write(f"#b={RESTRICTED_FUNCTION_CALL},\n")
            f.write(f"c={UNRESTRICTED_FUNCTION_CALL},\n")
            f.write(f"#d={UNRESTRICTED_FUNCTION_CALL},\n")
            f.write(")")


def write_unrestricted_files(path):
    for a in [1, 2]:
        with open(
            os.path.join(str(path), f"study_definition_unrestricted_{a}.py"),
            "w",
        ) as f:
            f.write(f"{STUDY_DEF_HEADER}\n")
            f.write(f"#a={RESTRICTED_FUNCTION_CALL}\n")
            f.write(f"b={UNRESTRICTED_FUNCTION_CALL}\n")
            f.write(f"#c={UNRESTRICTED_FUNCTION_CALL}\n")
            f.write(")")


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

def test_unrestricted_local_norepo(tmp_path,capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    validate_pass(capsys)
    os.chdir(prev_dir)

def test_restricted_local_norepo(tmp_path,capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    validate_fail(capsys)
    os.chdir(prev_dir)

def test_unrestricted_nonexistant_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(NONEXISTENT_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_nonexistant_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(NONEXISTENT_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_multiple_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(PERMITTED_MULTIPLE_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_multiple_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(PERMITTED_MULTIPLE_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_nonexistant_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(NONEXISTENT_HTTPS_ORIGIN)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_restricted_nonexistant_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(NONEXISTENT_SSH_ORIGIN)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_multiple_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(PERMITTED_MULTIPLE_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_multiple_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(PERMITTED_MULTIPLE_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(PERMITTED_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(PERMITTED_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(PERMITTED_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(PERMITTED_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_unpermitted_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(UNPERMITTED_HTTPS_ORIGIN)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_restricted_unpermitted_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    git_init(UNPERMITTED_SSH_ORIGIN)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_unrestricted_unpermitted_local_https(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(UNPERMITTED_HTTPS_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_unpermitted_local_ssh(tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    git_init(UNPERMITTED_SSH_ORIGIN)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_unpermitted_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", UNPERMITTED_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", PERMITTED_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", PERMITTED_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_unpermitted_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", UNPERMITTED_REPO)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_restricted_permitted_multiple_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", PERMITTED_MULTIPLE_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_unrestricted_permitted_multiple_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", PERMITTED_MULTIPLE_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)


def test_restricted_nonexistant_action(monkeypatch, tmp_path, capsys):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_restricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", NONEXISTENT_REPO)
    validate_fail(capsys)
    os.chdir(prev_dir)


def test_unrestricted_nonexistent_multiple_action(
    monkeypatch, tmp_path, capsys
):
    prev_dir = os.getcwd()
    os.chdir(tmp_path)
    write_unrestricted_files(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", NONEXISTENT_REPO)
    validate_pass(capsys)
    os.chdir(prev_dir)
