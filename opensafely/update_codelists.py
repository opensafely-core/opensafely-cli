from pathlib import Path

from opensafely._vendor import requests


DESCRIPTION = "Update codelists, using specification at codelists/codelists.txt"


def add_arguments(parser):
    # This command doesn't yet take any arguments
    pass


def main():
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
        codelist_file.write_text(response.text)
        new_files.add(codelist_file)
    for file in old_files - new_files:
        print(f"Deleting {file.name}")
        file.unlink()
