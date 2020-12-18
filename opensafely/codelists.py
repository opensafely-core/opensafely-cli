import dataclasses
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


@dataclasses.dataclass
class Codelist:
    id: str
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
    for line in codelists_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        project_id, codelist_id, version = line.split("/")
        url = (
            f"https://codelists.opensafely.org"
            f"/codelist/{project_id}/{codelist_id}/{version}/"
        )
        codelists.append(
            Codelist(
                id=line,
                url=url,
                download_url=f"{url}download.csv",
                filename=codelists_dir / f"{project_id}-{codelist_id}.csv",
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


def exit_with_error(message):
    print(message)
    sys.exit(1)
