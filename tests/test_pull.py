import argparse

import pytest

from opensafely import pull


def tag(image):
    return f"{pull.REGISTRY}/{image}:latest"


def test_default_no_local_images(run, capsys):

    run.expect(["docker", "image", "ls", "--format={{.Repository}}"], stdout=b"")

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.strip() == "No OpenSAFELY docker images found to update."


def test_default_no_local_images_force(run, capsys):

    run.expect(["docker", "image", "ls", "--format={{.Repository}}"], stdout=b"")
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "pull", tag("python")])
    run.expect(["docker", "pull", tag("jupyter")])
    run.expect(["docker", "pull", tag("stata-mp")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="all", force=True)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Updating OpenSAFELY python image",
        "Updating OpenSAFELY jupyter image",
        "Updating OpenSAFELY stata-mp image",
        "Cleaning up old images",
    ]


def test_default_with_local_images(run, capsys):

    run.expect(
        ["docker", "image", "ls", "--format={{.Repository}}"],
        stdout=b"ghcr.io/opensafely-core/r",
    )
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Cleaning up old images",
    ]


def test_specific_image(run, capsys):

    run.expect(["docker", "image", "ls", "--format={{.Repository}}"], stdout=b"")
    run.expect(["docker", "pull", tag("r")])
    run.expect(["docker", "image", "prune", "--force"])

    pull.main(image="r", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r image",
        "Cleaning up old images",
    ]


def test_remove_deprecated_images(run):
    local_images = set(
        [
            "docker.opensafely.org/r",
            "ghcr.io/opensafely/r",
            "ghcr.io/opensafely-core/r",
        ]
    )

    run.expect(["docker", "image", "rm", "docker.opensafely.org/r"])
    run.expect(["docker", "image", "rm", "ghcr.io/opensafely/r"])

    pull.remove_deprecated_images(local_images)


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], argparse.Namespace(image="all", force=False)),
        (["--force"], argparse.Namespace(image="all", force=True)),
        (["r"], argparse.Namespace(image="r", force=False)),
        (["r", "--force"], argparse.Namespace(image="r", force=True)),
        (["invalid"], SystemExit()),
    ],
)
def test_pull_parser_valid(argv, expected, capsys):
    parser = argparse.ArgumentParser()
    pull.add_arguments(parser)
    if isinstance(expected, SystemExit):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
    else:
        assert parser.parse_args(argv) == expected
