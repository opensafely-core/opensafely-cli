import pathlib

from opensafely import execute
from tests.conftest import run_main


def test_execute_main(run, no_user):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "--init",
            "--label=opensafely",
            "-it",
            f"--volume={pathlib.Path.cwd()}://workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ]
    )
    assert run_main(execute, "databuilder:v1 foo bar baz") == 0
