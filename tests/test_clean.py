import argparse
from dataclasses import dataclass

from opensafely import clean


def test_clean_parser():
    parser = argparse.ArgumentParser()
    clean.add_arguments(parser)
    assert parser.parse_args([]).verbose is False
    assert parser.parse_args(["--verbose"]).verbose is True


@dataclass
class Call:
    expected: list
    return_value: list


def test_main(run):
    run.expect(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--format={{ .ID }}",
            "--filter",
            clean.label_filter,
        ],
        stdout="os-job-1",
    )

    run.expect(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--format={{ .ID }}",
            "--filter",
            clean.busybox_filter,
        ],
        stdout="os-volume-manager-1",
    ),
    # these two will typically return the same results as the first two
    run.expect(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--format={{ .ID }}",
            "--filter",
            clean.name_filter,
        ],
        stdout="os-job-1",
    ),
    run.expect(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--format={{ .ID }}",
            "--filter",
            clean.volume_filter,
        ],
        stdout="os-volume-manager-1",
    ),
    # remove containers
    run.expect(["docker", "rm", "--force", "os-job-1", "os-volume-manager-1"])

    # list volumes
    run.expect(
        [
            "docker",
            "volume",
            "ls",
            "--format={{ .Name }}",
            "--filter",
            clean.volume_filter,
        ],
        stdout="os-volume-1",
    ),
    # remove volumes
    run.expect(["docker", "volume", "rm", "--force", "os-volume-1"])
    # prunemove containers
    run.expect(["docker", "image", "prune", "--force", "--filter", clean.label_filter])

    clean.main()
