from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "package_type,ext", [("sdist", "tar.gz"), ("bdist_wheel", "whl")]
)
def test_packaging(package_type, ext, tmp_path):
    project_root = Path(__file__).parent.parent
    # This is pretty yucky. Ideally we'd stick all the build artefacts in a
    # temporary directory but I can't seem to persuade setuptools to do this
    shutil.rmtree(project_root / "dist", ignore_errors=True)
    shutil.rmtree(project_root / "build", ignore_errors=True)
    # Build the package
    subprocess.run(
        [sys.executable, "setup.py", "build", package_type],
        check=True,
        cwd=project_root,
    )
    # Install it in a temporary virtualenv
    subprocess.run([sys.executable, "-m", "venv", tmp_path])
    package = list(project_root.glob(f"dist/*.{ext}"))[0]
    subprocess.run([tmp_path / "bin/pip", "install", package])
    # Smoketest it by running `--help`. This is actually a more comprehensive
    # test than you might think as it involves importing everything and because
    # all the complexity in this project is in the vendoring and packaging,
    # issues tend to show up at import time.
    subprocess.run([tmp_path / "bin/opensafely", "run", "--help"])
