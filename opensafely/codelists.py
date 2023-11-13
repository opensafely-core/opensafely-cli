import dataclasses
import datetime
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from opensafely._vendor import requests


OPENCODELISTS_BASE_URL = "https://www.opencodelists.org"
DESCRIPTION = f"Commands for interacting with {OPENCODELISTS_BASE_URL}"

CODELISTS_DIR = "codelists"
CODELISTS_FILE = "codelists.txt"
MANIFEST_FILE = "codelists.json"


def add_arguments(parser):
    def show_help(**kwargs):
        parser.print_help()
        parser.exit()

    # Show help by default if no command supplied
    parser.set_defaults(function=show_help)
    subparsers = parser.add_subparsers(
        title="available commands", description="", metavar="COMMAND"
    )

    parser_update = subparsers.add_parser(
        "update",
        help=(
            f"Update codelists, using specification at "
            f"{CODELISTS_DIR}/{CODELISTS_FILE}"
        ),
    )
    parser_update.set_defaults(function=update)

    parser_check = subparsers.add_parser(
        "check",
        help=(
            "Check that codelists on disk match the specification at "
            f"{CODELISTS_DIR}/{CODELISTS_FILE} and are up-to-date with "
            "upstream versions"
        ),
    )

    parser_check_upstream = subparsers.add_parser(
        "check-upstream",
        help=("Check codelists are up to date with upstream versions"),
    )
    parser_check_upstream.set_defaults(function=check_upstream)

    parser_check.set_defaults(function=check)


# Just here for consistency so we can always reference `<module>.main()` in the
# primary entrypoint. The behaviour usually implemented by `main()` is handled
# by the default `show_help` above
def main():
    pass


def update(codelists_dir=None):
    if not codelists_dir:
        codelists_dir = Path.cwd() / CODELISTS_DIR
    codelists = parse_codelist_file(codelists_dir)
    old_files = set(codelists_dir.glob("*.csv"))
    new_files = set()
    manifest = {"files": {}}
    for codelist in codelists:
        print(f"Fetching {codelist.id}")
        try:
            response = requests.get(codelist.download_url)
            response.raise_for_status()
        except Exception as e:
            exit_with_error(
                f"Error downloading codelist: {e}\n\n"
                f"Check that you can access the codelist at:\n{codelist.url}"
            )
        codelist.filename.write_bytes(response.content)
        new_files.add(codelist.filename)
        key = str(codelist.filename.relative_to(codelists_dir))
        manifest["files"][key] = {
            "id": codelist.id,
            "url": codelist.url,
            "downloaded_at": f"{datetime.datetime.utcnow()}Z",
            "sha": hash_bytes(response.content),
        }
    manifest_file = codelists_dir / MANIFEST_FILE
    preserve_download_dates(manifest, manifest_file)
    manifest_file.write_text(json.dumps(manifest, indent=2))
    for file in old_files - new_files:
        print(f"Deleting {file.name}")
        file.unlink()
    return True


def get_codelists_dir(codelists_dir=None):
    codelists_dir = codelists_dir or Path.cwd() / CODELISTS_DIR
    if not codelists_dir.exists():
        print(f"No '{CODELISTS_DIR}' directory present so nothing to check")
        return
    return codelists_dir


def check_upstream(codelists_dir=None):
    """
    Check currently downloaded codelists against current OpenCodelists data.
    This runs after the local checks in `check()`, but can also run as a standalone
    command.
    """
    codelists_dir = get_codelists_dir(codelists_dir)
    if codelists_dir is None:
        return True
    codelists_file = codelists_dir / CODELISTS_FILE
    if not codelists_file.exists():
        exit_with_error(f"No file found at '{codelists_file}'")
    manifest_file = codelists_dir / MANIFEST_FILE
    if not manifest_file.exists():
        exit_with_prompt(f"No file found at '{manifest_file}'.")
    post_data = {
        "codelists": codelists_file.read_text(),
        "manifest": manifest_file.read_text(),
    }
    url = f"{OPENCODELISTS_BASE_URL}/api/v1/check/"
    response = requests.post(url, post_data).json()
    status = response["status"]

    if status == "error":
        # The OpenCodelists check endpoint returns an error in the response data if it
        # encounters an invalid user, organisation or codelist in the codelists.txt file, or
        # if any codelists in codelists.csv don't match the expected pattern. These should all
        # be fixable by `opensafely codelists update`.
        if "error" in response["data"]:
            error_message = (
                f"Error checking upstream codelists: {response['data']['error']}\n"
            )
        elif response["data"]["added"] or response["data"]["removed"]:
            error_message = (
                "Codelists have been added or removed\n\n"
                "For details, run:\n\n  opensafely codelists check\n"
            )
        else:
            changed = "\n  ".join(response["data"]["changed"])
            error_message = (
                f"Some codelists are out of date\nCodelists affected:\n  {changed}\n"
            )

        # If we're running in CI, we don't want to fail the entire action due to out of
        # date upstream codelists, as users may have valid reasons for not wanting to update
        # them  (i.e. if they have already run jobs that use the backend database). In this
        # case, just print the error message instead of exiting.
        if not os.environ.get("GITHUB_WORKFLOW"):
            exit_with_prompt(error_message)
        print(error_message)
    else:
        print("Codelists OK")
    return True


def check():
    codelists_dir = get_codelists_dir()
    if codelists_dir is None:
        return True

    codelists = parse_codelist_file(codelists_dir)
    manifest_file = codelists_dir / MANIFEST_FILE
    if not manifest_file.exists():
        # This is here so that switching to use this test in Github Actions
        # doesn't cause existing repos which previously passed to start
        # failing. It works by creating a temporary manifest file and then
        # checking against that. Functionally, this is the same as the old test
        # which would check against the OpenCodelists website every time.
        if os.environ.get("GITHUB_WORKFLOW"):
            print(
                "==> WARNING\n"
                "    Using temporary workaround for Github Actions tests.\n"
                "    You should run: opensafely codelists update\n"
            )
            manifest = make_temporary_manifest(codelists_dir)
        else:
            exit_with_prompt(f"No file found at '{CODELISTS_DIR}/{MANIFEST_FILE}'.")
    else:
        try:
            manifest = json.loads(manifest_file.read_text())
        except json.decoder.JSONDecodeError:
            exit_with_prompt(
                f"'{CODELISTS_DIR}/{MANIFEST_FILE}' is invalid.\n"
                "Note that this file is automatically generated and should not be manually edited.\n"
            )
    all_ids = {codelist.id for codelist in codelists}
    ids_in_manifest = {f["id"] for f in manifest["files"].values()}
    if all_ids != ids_in_manifest:
        diff = format_diff(all_ids, ids_in_manifest)
        exit_with_prompt(
            f"It looks like '{CODELISTS_FILE}' has been edited but "
            f"'update' hasn't been run.\n{diff}\n"
        )
    all_csvs = set(f.name for f in codelists_dir.glob("*.csv"))
    csvs_in_manifest = set(manifest["files"].keys())
    if all_csvs != csvs_in_manifest:
        diff = format_diff(all_csvs, csvs_in_manifest)
        exit_with_prompt(
            f"It looks like CSV files have been added or deleted in the "
            f"'{CODELISTS_DIR}' folder.\n{diff}\n"
        )
    modified = []
    for filename, details in manifest["files"].items():
        csv_file = codelists_dir / filename
        sha = hash_bytes(csv_file.read_bytes())
        if sha != details["sha"]:
            modified.append(f"  {CODELISTS_DIR}/{filename}")
    if modified:
        exit_with_prompt(
            "A CSV file seems to have been modified since it was downloaded:\n"
            "{}\n".format("\n".join(modified))
        )

    try:
        check_upstream(codelists_dir)
    except requests.exceptions.ConnectionError:
        print(
            f"Local codelists OK; could not contact {OPENCODELISTS_BASE_URL} for upstream check,"
            "try again later"
        )
    return True


def make_temporary_manifest(codelists_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        contents = codelists_dir.joinpath(CODELISTS_FILE).read_bytes()
        tmpdir.joinpath(CODELISTS_FILE).write_bytes(contents)
        update(codelists_dir=tmpdir)
        manifest = json.loads(tmpdir.joinpath(MANIFEST_FILE).read_text())
    return manifest


@dataclasses.dataclass
class Codelist:
    id: str  # noqa: A003
    url: str
    download_url: str
    filename: Path


def parse_codelist_file(codelists_dir):
    if not codelists_dir.exists() or not codelists_dir.is_dir():
        exit_with_error(f"No '{CODELISTS_DIR}' folder found")
    codelists_file = codelists_dir / CODELISTS_FILE
    if not codelists_file.exists():
        exit_with_error(f"No file found at '{CODELISTS_DIR}/{CODELISTS_FILE}'")
    codelists = []
    codelist_versions = {}
    for line in codelists_file.read_text().splitlines():
        line = line.strip().rstrip("/")
        if not line or line.startswith("#"):
            continue
        tokens = line.split("/")
        if len(tokens) not in [3, 4]:
            exit_with_error(
                f"{line} does not match [project]/[codelist]/[version] "
                "or user/[username]/[codelist]/[version]"
            )
        line_without_version = "/".join(tokens[:-1])
        existing_version = codelist_versions.get(line_without_version)
        line_version = tokens[-1]
        if existing_version == line_version:
            exit_with_error(f"{line} is a duplicate of a previous line")
        if existing_version is not None:
            exit_with_error(
                f"{line} conflicts with a different version of the same codelist: {existing_version}"
            )
        codelist_versions[line_without_version] = line_version

        url = f"{OPENCODELISTS_BASE_URL}/codelist/{line}/"
        filename = "-".join(tokens[:-1]) + ".csv"
        codelists.append(
            Codelist(
                id=line,
                url=url,
                download_url=f"{url}download.csv",
                filename=codelists_dir / filename,
            )
        )
    return codelists


def preserve_download_dates(manifest, old_manifest_file):
    """
    If file contents are unchanged then we copy the original download date from
    the existing manifest. This makes the update process idempotent and
    prevents unnecessary diff noise.
    """
    if not old_manifest_file.exists():
        return
    old_manifest = json.loads(old_manifest_file.read_text())
    for filename, details in manifest["files"].items():
        old_details = old_manifest["files"].get(filename)
        if old_details and old_details["sha"] == details["sha"]:
            details["downloaded_at"] = old_details["downloaded_at"]


def hash_bytes(content):
    # Normalize line-endings. Windows in general, and git on Windows in
    # particular, is prone to messing about with these
    content = b"\n".join(content.splitlines())
    return hashlib.sha1(content).hexdigest()


def format_diff(set_a, set_b):
    return "\n".join(
        [
            f"  {'  added' if element in set_a else 'removed'}: {element}"
            for element in set_a.symmetric_difference(set_b)
        ]
    )


def exit_with_prompt(message):
    exit_with_error(
        f"{message}\n"
        f"To fix these errors run the command below and commit the changes:\n\n"
        f"  opensafely codelists update\n"
    )


def exit_with_error(message):
    print(message)
    sys.exit(1)
