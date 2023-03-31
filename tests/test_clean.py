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


def test_main(monkeypatch):
    # hard to test w/o docker, so test expected calls
    expected = [
        # list jobs with all filters
        Call(
            [
                "container",
                "ls",
                "--all",
                "--format={{ .ID }}",
                "--filter",
                clean.label_filter,
            ],
            ["os-job-1"],
        ),
        Call(
            [
                "container",
                "ls",
                "--all",
                "--format={{ .ID }}",
                "--filter",
                clean.busybox_filter,
            ],
            ["os-volume-1"],
        ),
        # these two will typically return the same results as the first two
        Call(
            [
                "container",
                "ls",
                "--all",
                "--format={{ .ID }}",
                "--filter",
                clean.name_filter,
            ],
            ["os-job-1"],
        ),
        Call(
            [
                "container",
                "ls",
                "--all",
                "--format={{ .ID }}",
                "--filter",
                clean.volume_filter,
            ],
            ["os-volume-1"],
        ),
        # remove containers
        Call(
            ["rm", "--force", "os-job-1", "os-volume-1"],
            [],
        ),
        # list volumes
        Call(
            ["volume", "ls", "--format={{ .Name }}", "--filter", clean.volume_filter],
            ["os-volume-1"],
        ),
        # remove volumes
        Call(
            ["volume", "rm", "--force", "os-volume-1"],
            [],
        ),
        # prunemove containers
        Call(
            ["image", "prune", "--force", "--filter", clean.label_filter],
            [],
        ),
    ]

    def mock_docker_output(cmd, verbose):
        next_call = expected.pop(0)
        assert cmd == next_call.expected
        return next_call.return_value

    monkeypatch.setattr(clean, "docker_output", mock_docker_output)

    clean.main()
