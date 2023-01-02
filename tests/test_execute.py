import pathlib
from unittest import mock

from opensafely import execute


@mock.patch("opensafely.execute.os")
def test_execute_main(mock_os, run):
    mock_os.getuid.return_value = 12345
    mock_os.getgid.return_value = 67890
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--user",
            "12345:67890",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ],
        winpty=True,
    )
    execute.main("databuilder:v1", ["foo", "bar", "baz"])


@mock.patch("opensafely.execute.os")
def test_execute_main_on_windows(mock_os, run):
    mock_os.getuid.side_effect = AttributeError()
    mock_os.getgid.side_effect = AttributeError()
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            "-it",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ],
        winpty=True,
    )
    execute.main("databuilder:v1", ["foo", "bar", "baz"])
