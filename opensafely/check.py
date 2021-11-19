from opensafely._vendor import requests
from opensafely._vendor.ruamel.yaml import YAML
from os import environ, popen, walk, path
import re


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
    }

    if found_datasets:
        print_violations(found_datasets)
        exit(1)
    else:
        print("Success")
        exit(0)


def print_violations(found_datasets):
    print('Usage of restricted datasets found:')
    for d,files in found_datasets.items():
        print(f'{d}:')
        for f,lines in files.items():
            print(f'\t {f} :')
            for ln, line in lines:
                print(f"\t\t line {ln}: {line}")


def check_dataset(functions, files_to_check):
    found_functions = {}
    for function in functions:
        regex = re.compile(f"\.{function}\(")
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
            if regex.match(line):
                found_lines[ln] = line
    return found_lines


def get_local_py_files():
    out_files = []
    for root, dirs, files in walk(".", topdown=False):
        for name in files:
            out_files.append(path.join(root, name))
        for name in dirs:
            out_files.append(path.join(root, name))
    return [r for r in out_files if r.endswith(".py")]


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
    if "GITHUB_REPOSITORY" in environ:
        return environ["GITHUB_REPOSITORY"]
    else:
        s = popen("git config --get remote.origin.url")
        url = s.read()
        if url.startswith("https://github.com/"):
            return url.replace("https://github.com/", "")
        if url.startswith("git@github.com:"):
            return url.replace("git@github.com:", "").replace(".git", "")
        return None


def get_allowed_datasets(respository_name, permissions):
    if respository_name not in permissions:
        return []
    return permissions[respository_name]["allow"]

