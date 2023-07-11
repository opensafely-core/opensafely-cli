import configparser
import glob
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from opensafely._vendor import requests
from opensafely._vendor.ruyaml import YAML


DESCRIPTION = "Check the opensafely project for correctness"


@dataclass(frozen=True)
class RestrictedDataset:
    name: str
    cohort_extractor_function_names: List[str]
    ehrql_table_names: List[str]


RESTRICTED_DATASETS = [
    RestrictedDataset(
        name="icnarc",
        cohort_extractor_function_names=[
            "admitted_to_icu",
        ],
        ehrql_table_names=[],
    ),
    RestrictedDataset(
        name="isaric",
        cohort_extractor_function_names=[
            "with_an_isaric_record",
        ],
        ehrql_table_names=["isaric_new"],
    ),
    RestrictedDataset(
        name="ons_cis",
        cohort_extractor_function_names=[
            "with_an_ons_cis_record",
        ],
        ehrql_table_names=["ons_cis_raw", "ons_cis"],
    ),
    RestrictedDataset(
        name="ukrr",
        cohort_extractor_function_names=[
            "with_record_in_ukrr",
        ],
        ehrql_table_names=[],
    ),
    RestrictedDataset(
        name="icnarc",
        cohort_extractor_function_names=[
            "admitted_to_icu",
        ],
        ehrql_table_names=[],
    ),
    RestrictedDataset(
        name="open_prompt",
        cohort_extractor_function_names=[],
        ehrql_table_names=["open_prompt"],
    ),
]

PERMISSIONS_URL = "https://raw.githubusercontent.com/opensafely-core/opensafely-cli/main/repository_permissions.yaml"


def add_arguments(parser):
    pass


def main(continue_on_error=False):
    permissions_url = os.environ.get("OPENSAFELY_PERMISSIONS_URL") or PERMISSIONS_URL
    repo_name = get_repository_name(continue_on_error)
    if not repo_name and not continue_on_error:
        sys.exit("Unable to find repository name")
    permissions = get_datasource_permissions(permissions_url)
    allowed_datasets = get_allowed_datasets(repo_name, permissions)

    files_to_check = glob.glob("**/*.py", recursive=True)

    datasets_to_check = [
        dataset
        for dataset in RESTRICTED_DATASETS
        if dataset.name not in allowed_datasets
    ]

    found_cohort_datasets = {
        dataset.name: dataset_check
        for dataset in datasets_to_check
        if (
            dataset_check := check_restricted_names(
                restricted_names=dataset.cohort_extractor_function_names,
                # Check for the use of `.function_name`.
                regex_template=r"\.{name}\(",
                files_to_check=files_to_check,
            )
        )
    }

    found_ehrql_datasets = {
        dataset.name: dataset_check
        for dataset in datasets_to_check
        if (
            dataset_check := check_restricted_names(
                restricted_names=dataset.ehrql_table_names,
                # Check for the use of `table_name.`
                regex_template=r"{name}\.",
                files_to_check=files_to_check,
            )
        )
    }

    violations = []

    if found_ehrql_datasets:
        violations.extend(list(format_ehrql_violations(found_ehrql_datasets)))

    if found_cohort_datasets:
        violations.extend(list(format_cohort_violations(found_cohort_datasets)))

    if violations:
        violations_text = "\n".join(violations)
        if not continue_on_error:
            sys.exit(violations_text)
        print("*** WARNING ***\n")
        print(violations_text)
    else:
        if not continue_on_error:
            print("Success")


def format_cohort_violations(found_datasets):
    yield "Usage of restricted datasets found:\n"
    for d, functions in found_datasets.items():
        yield f"{d}: https://docs.opensafely.org/study-def-variables/#{d}"
        for fn, files in functions.items():
            yield f"- {fn}"
            for f, lines in files.items():
                yield f"  - {f}:"
                for ln, line in lines.items():
                    yield f"    line {ln}: {line}"


def format_ehrql_violations(found_datasets):
    # Unlike for cohort-extractor,
    # there is no specific reference we can currently link to for restricted tables.
    # We may be able to add such a link in future,
    # which might make it more reasonable to unify this function
    # with the analogous function for cohort-extractor.
    yield "Usage of restricted tables found:\n"
    for d, tables in found_datasets.items():
        for table, files in tables.items():
            yield f"{table}"
            for f, lines in files.items():
                yield f"  - {f}:"
                for ln, line in lines.items():
                    yield f"    line {ln}: {line}"


def check_restricted_names(restricted_names, regex_template, files_to_check):
    found_names = {}
    for name in restricted_names:
        regex = re.compile(regex_template.format(name=name))
        found_files = {}
        for f in files_to_check:
            matches = check_file(f, regex)
            if matches:
                found_files[f] = matches
        if found_files:
            found_names[name] = found_files
    return found_names


def check_file(filename, regex):
    found_lines = {}
    with open(filename, encoding="utf8", errors="ignore") as f:
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


def get_repository_name(continue_on_error):
    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]
    else:
        git_config_path = Path(".git", "config")
        if not git_config_path.is_file():
            if not continue_on_error:
                print("Git config file not found")
            return
        config = configparser.ConfigParser()
        try:
            config.read(git_config_path)
        except Exception as e:
            if not continue_on_error:
                print(f"Unable to read git config.\n{str(e)}")
            return
        if 'remote "origin"' not in config.sections():
            if not continue_on_error:
                print("Remote 'origin' not defined in git config.")
            return
        url = config['remote "origin"']["url"]
        return (
            url.replace("https://github.com/", "")
            .replace("git@github.com:", "")
            .replace(".git", "")
            .strip()
        )


def get_allowed_datasets(repository_name, permissions):
    if not repository_name or repository_name not in permissions:
        return []
    return permissions[repository_name]["allow"]
