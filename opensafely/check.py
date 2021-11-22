from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml import YAML
import os
import re
import glob
import subprocess

DESCRIPTION = "Check the opensafely project for correctness"

RESTRICTED_DATASETS = {"ICNARC": ["admitted_to_icu"]}

# todo: dummy location and data
PERMISSIONS_URL = "https://raw.githubusercontent.com/Jongmassey/research_repository_permissions/main/repository_permissions.yaml"


def add_arguments(parser):
    pass


def main():
    repo_name = get_repository_name()
    permissions = get_datasource_permissions(PERMISSIONS_URL)
    allowed_datasets = get_allowed_datasets(repo_name, permissions)
    datasets_to_check = {
        k: v
        for k, v in RESTRICTED_DATASETS.items()
        if k not in allowed_datasets
    }
    files_to_check = get_local_py_files()

    found_datasets = {
        dataset: check_dataset(functions, files_to_check)
        for dataset, functions in datasets_to_check.items()
        if check_dataset(functions, files_to_check)
    }

    if found_datasets:
        exit(print_violations(found_datasets))
    else:
        print("Success")


def print_violations(found_datasets):
    print("Usage of restricted datasets found:")
    for d, files in found_datasets.items():
        print(f"{d}:")
        for f, lines in files.items():
            print(f"\t {f} :")
            for ln, line in lines:
                print(f"\t\t line {ln}: {line}")


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
    with open(filename, "r") as f:
        for ln, line in enumerate(f.readlines(), start=1):
            if regex.search(line):
                found_lines[ln] = line
    return found_lines


def get_local_py_files():
    return glob.glob("**/*.py",recursive=True)


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
            args=["git", "config", "--get","remote.origin.url"],
            capture_output=True,
            text=True,
        ).stdout
        return (
            url.replace("https://github.com/", "")
            .replace("git@github.com:","")
            .replace(".git", "")
            .strip()
        )


def get_allowed_datasets(respository_name, permissions):
    if not respository_name or respository_name not in permissions:
        return []
    return permissions[respository_name]["allow"]
