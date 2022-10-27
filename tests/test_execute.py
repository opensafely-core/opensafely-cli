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
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "--user",
            "12345:67890",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ]
    )
    execute.main("databuilder:v1", ["foo", "bar", "baz"], container_user_is_enabled=False)


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
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ]
    )
    execute.main("databuilder:v1", ["foo", "bar", "baz"], container_user_is_enabled=False)


@mock.patch("opensafely.execute.os")
def test_execute_main_without_user(mock_os, run):
    run.expect(["docker", "info"])
    run.expect(
        [
            "docker",
            "run",
            "--rm",
            f"--volume={pathlib.Path.cwd()}:/workspace",
            "ghcr.io/opensafely-core/databuilder:v1",
            "foo",
            "bar",
            "baz",
        ]
   )
    execute.main("databuilder:v1", ["foo", "bar", "baz"], container_user_is_enabled=True)
