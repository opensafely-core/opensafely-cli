import sys
import textwrap
from pathlib import Path

import pytest

from opensafely import info


project_fixture_path = Path(__file__).parent / "fixtures" / "projects"


@pytest.mark.skipif(sys.platform != "linux", reason="Only runs on Linux")
def test_info(capsys):
    assert info.main()
    out, err = capsys.readouterr()
    assert "opensafely version:" in out
    assert "docker version:" in out
    assert "docker memory:" in out
    assert "docker cpu:" in out


def test_list_project_images(capsys):
    assert info.main(list_project_images=project_fixture_path / "project.yaml")
    out, err = capsys.readouterr()
    assert err == ""
    assert out == textwrap.dedent(
        """
       cohortextractor:v1
       jupyter:v1
       python:v1
    """.lstrip(
            "\n"
        )
    )
