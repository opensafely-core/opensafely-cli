import glob
import os
import re
import subprocess
import sys

from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml import YAML

DESCRIPTION = "Check the opensafely project for correctness"

RESTRICTED_DATASETS = {"icnarc": ["admitted_to_icu"]}

PERMISSIONS_URL = "https://raw.githubusercontent.com/opensafely-core/opensafely-cli/main/repository_permisisons.yaml"


def add_arguments(parser):
    pass


def main(continue_on_error=False):
    permissions_url = os.environ.get("OPENSAFELY_PERMISSIONS_URL") or PERMISSIONS_URL
    repo_name = get_repository_name()
    permissions = get_datasource_permissions(permissions_url)
    allowed_datasets = get_allowed_datasets(repo_name, permissions)
    datasets_to_check = {
        k: v for k, v in RESTRICTED_DATASETS.items() if k not in allowed_datasets
    }
    files_to_check = glob.glob("**/*.py", recursive=True)

    found_datasets = {
        dataset: check_dataset(functions, files_to_check)
        for dataset, functions in datasets_to_check.items()
        if check_dataset(functions, files_to_check)
    }

    if found_datasets:
        violations = "\n".join(format_violations(found_datasets))
        if not continue_on_error:
            sys.exit(violations)
        print("*** WARNING ***\n")
        print(violations)
    else:
        if not continue_on_error:
            print("Success")


def format_violations(found_datasets):
    yield "Usage of restricted datasets found:\n"
    for d, functions in found_datasets.items():
        yield f"{d}: https://docs.opensafely.org/study-def-variables/#{d}"
        for fn, files in functions.items():
            yield f"- {fn}"
            for f, lines in files.items():
                yield f"  - {f}:"
                for ln, line in lines.items():
                    yield f"    line {ln}: {line}"


def check_dataset(functions, files_to_check):
    found_functions = {}
    for function in functions:
        regex = re.compile(rf"\.{function}\(")
        found_files = {}
        for f in files_to_check:
            matches = check_file(f, regex)
            if matches:
                found_files[f] = matches
        if found_files:
            found_functions[function] = found_files
    return found_functions


def check_file(filename, regex):
    found_lines = {}
    with open(filename, "r", encoding="utf8", errors="ignore") as f:
        for ln, line in enumerate(f, start=1):
            if line.lstrip().startswith("#"):
                continue
            if regex.search(line):
                found_lines[ln] = line
    return found_lines


def get_datasource_permissions(permissions_url):
    resp = requests.get(permissions_url)
    if resp.status_code != 200:
        raise requests.RequestException(
            f"Error {resp.status_code} getting {permissions_url}"
        )
    yaml = YAML()
    permissions = yaml.load(resp.text)
    return permissions


def get_repository_name():
    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]
    else:

        url = subprocess.run(
            args=["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
        ).stdout
        return (
            url.replace("https://github.com/", "")
            .replace("git@github.com:", "")
            .replace(".git", "")
            .strip()
        )


def get_allowed_datasets(respository_name, permissions):
    if not respository_name or respository_name not in permissions:
        return []
    return permissions[respository_name]["allow"]
