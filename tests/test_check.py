from requests_mock import mocker
from opensafely._vendor import requests
from opensafely import check
from os import environ
# Because we're using a vendored version of requests we need to monkeypatch the
# requests_mock library so it references our vendored library instead
mocker.requests = requests
mocker._original_send = requests.Session.send


def test_check_with_env_allowed(requests_mock):
    requests_mock.get(
        check.PERMISSIONS_URL
    )
    environ["GITHUB_REPOSITORY"] = "opensafely/dummy_icnarc"
    check.main()

def test_check_with_env_disallowed(requests_mock):
    requests_mock.get(
        check.PERMISSIONS_URL
    )
    environ["GITHUB_REPOSITORY"] = "opensafely/dummy_ons"
    check.main()

def test_check_with_local_git_disallowed():
    pass

def test_check_with_local_git_allowed():
    pass