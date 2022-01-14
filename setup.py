import os

from setuptools import find_namespace_packages, setup


with open(os.path.join("opensafely", "VERSION")) as f:
    version = f.read().strip()

setup(
    name="opensafely",
    version=version,
    packages=find_namespace_packages(exclude=["tests"]),
    include_package_data=True,
    url="https://github.com/opensafely-core/opensafely-cli",
    description="Command line tool for running OpenSAFELY studies locally.",
    license="GPLv3",
    author="OpenSAFELY",
    author_email="tech@opensafely.org",
    python_requires=">=3.8",
    entry_points={"console_scripts": ["opensafely=opensafely:main"]},
    classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"],
    project_urls={
        "Homepage": "https://opensafely.org",
        "Documentation": "https://docs.opensafely.org",
    },
)
