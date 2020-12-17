from pathlib import Path

from opensafely._vendor import requests


DESCRIPTION = "Commands for interacting with https://codelists.opensafely.org/"


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
        help="Update codelists, using specification at codelists/codelists.txt",
    )
    parser_update.set_defaults(function=update)


# Just here for consistency so we can always reference `<module>.main()` in the
# primary entrypoint. The behaviour usually implemented by `main()` is handled
# by the default `show_help` above
def main():
    pass


def update():
    codelists_path = Path.cwd() / "codelists"
    old_files = set(codelists_path.glob("*.csv"))
    new_files = set()
    lines = codelists_path.joinpath("codelists.txt").read_text().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        print(f"Fetching {line}")
        project_id, codelist_id, version = line.split("/")
        url = (
            f"https://codelists.opensafely.org"
            f"/codelist/{project_id}/{codelist_id}/{version}/download.csv"
        )
        codelist_file = codelists_path / f"{project_id}-{codelist_id}.csv"

        response = requests.get(url)
        response.raise_for_status()
        codelist_file.write_bytes(response.content)
        new_files.add(codelist_file)
    for file in old_files - new_files:
        print(f"Deleting {file.name}")
        file.unlink()
