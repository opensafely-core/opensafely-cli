import gzip
import os
from pathlib import Path
import subprocess

import pytest

from opensafely import unzip


def write_gzip(path, content="test content"):
    with gzip.open(path, "w") as f:
        f.write(content.encode("utf8"))


def test_unzip_file(tmp_path):
    f = tmp_path / "test.csv.gz"
    write_gzip(f)
    unzip.main(str(f))
    assert f.with_suffix("").read_text() == "test content"


def test_unzip_dir(tmp_path):
    f1 = tmp_path / "test.csv.gz"
    f2 = tmp_path / "test.dta.gz"
    write_gzip(f1, "csv")
    write_gzip(f2, "dta")
    unzip.main(str(tmp_path))
    assert f1.with_suffix("").read_text() == "csv"
    assert f2.with_suffix("").read_text() == "dta"


def test_unzip_not_exists(tmp_path):
    with pytest.raises(SystemExit):
        unzip.main(str(tmp_path / "nope"))
