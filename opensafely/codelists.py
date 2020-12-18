import datetime
import hashlib
import json
from pathlib import Path
import sys

from opensafely._vendor import requests


DESCRIPTION = "Commands for interacting with https://codelists.opensafely.org/"

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


# Just here for consistency so we can always reference `<module>.main()` in the
# primary entrypoint. The behaviour usually implemented by `main()` is handled
# by the default `show_help` above
def main():
    pass


def update():
    codelists_path = Path.cwd() / CODELISTS_DIR
    if not codelists_path.exists() or not codelists_path.is_dir():
        exit_with_error(f"No '{CODELISTS_DIR}' folder found")
    codelists_file = codelists_path / CODELISTS_FILE
    if not codelists_file.exists():
        exit_with_error(f"No file found at '{CODELISTS_DIR}/{CODELISTS_FILE}'")
    old_files = set(codelists_path.glob("*.csv"))
    new_files = set()
    lines = codelists_file.read_text().splitlines()
    manifest = {"files": {}}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        print(f"Fetching {line}")
        project_id, codelist_id, version = line.split("/")
        codelist_url = (
            f"https://codelists.opensafely.org"
            f"/codelist/{project_id}/{codelist_id}/{version}/"
        )
        download_url = f"{codelist_url}download.csv"
        codelist_file = codelists_path / f"{project_id}-{codelist_id}.csv"
        try:
            response = requests.get(download_url)
            response.raise_for_status()
        except Exception as e:
            exit_with_error(
                f"Error downloading codelist: {e}\n\n"
                f"Check that you can access the codelist at:\n{codelist_url}"
            )
        codelist_file.write_bytes(response.content)
        new_files.add(codelist_file)
        key = str(codelist_file.relative_to(codelists_path))
        manifest["files"][key] = {
            "url": codelist_url,
            "downloaded_at": f"{datetime.datetime.utcnow()}Z",
            "sha": hash_bytes(response.content),
        }
    manifest_file = codelists_path / MANIFEST_FILE
    preserve_download_dates(manifest, manifest_file)
    manifest_file.write_text(json.dumps(manifest, indent=2))
    for file in old_files - new_files:
        print(f"Deleting {file.name}")
        file.unlink()


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


def exit_with_error(message):
    print(message)
    sys.exit(1)
