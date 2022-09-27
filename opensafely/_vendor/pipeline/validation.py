from __future__ import annotations

import posixpath
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING

from .exceptions import InvalidPatternError
from .outputs import get_first_output_file, get_output_dirs


if TYPE_CHECKING:  # pragma: no cover
    from .models import Action


def assert_valid_glob_pattern(pattern: str) -> None:
    """
    These patterns get converted into regular expressions and matched
    with a `find` command so there shouldn't be any possibility of a path
    traversal attack anyway. But it's still good to ensure that they are
    well-formed.
    """
    # Only POSIX slashes please
    if "\\" in pattern:
        raise InvalidPatternError("contains back slashes (use forward slashes only)")

    # These aren't unsafe, but they won't behave as expected so we shouldn't let
    # people use them
    for expr in ("**", "?", "["):
        if expr in pattern:
            raise InvalidPatternError(
                f"contains '{expr}' (only the * wildcard character is supported)"
            )

    if pattern.endswith("/"):
        raise InvalidPatternError(
            "looks like a directory (only files should be specified)"
        )

    # Check that the path is in normal form
    if posixpath.normpath(pattern) != pattern:
        raise InvalidPatternError(
            "is not in standard form (contains double slashes or '..' elements)"
        )

    # This is the directory we use for storing metadata about action runs and
    # we don't want outputs getting mixed up in it.
    if pattern == "metadata" or pattern.startswith("metadata/"):
        raise InvalidPatternError("should not include the metadata directory")

    # Windows has a different notion of absolute paths (e.g c:/foo) so we check
    # for both platforms
    if PurePosixPath(pattern).is_absolute() or PureWindowsPath(pattern).is_absolute():
        raise InvalidPatternError("is an absolute path")


def validate_cohortextractor_outputs(action_id: str, action: Action) -> None:
    """
    Check cohortextractor's output config is valid for this command

    We can't validate outputs in the Action or Outputs models because we need
    to look up other fields (eg run).
    """
    # ensure we only have output level defined.
    num_output_levels = len(action.outputs)
    if num_output_levels != 1:
        raise ValueError(
            "A `generate_cohort` action must have exactly one output; "
            f"{action_id} had {num_output_levels}"
        )

    output_dirs = get_output_dirs(action.outputs)
    if len(output_dirs) == 1:
        return

    # If we detect multiple output directories but the command explicitly
    # specifies an output directory then we assume the user knows what
    # they're doing and don't attempt to modify the output directory or
    # throw an error
    flag = "--output-dir"
    has_output_dir = any(
        arg == flag or arg.startswith(f"{flag}=") for arg in action.run.parts
    )
    if not has_output_dir:
        raise ValueError(
            f"generate_cohort command should produce output in only one "
            f"directory, found {len(output_dirs)}:\n"
            + "\n".join([f" - {d}/" for d in output_dirs])
        )


def validate_databuilder_outputs(action_id: str, action: Action) -> None:
    """
    Check databuilder's output config is valid for this command

    We can't validate outputs in the Action or Outputs models because we need
    to look up other fields (eg run).
    """
    # TODO: should this be checking output _paths_ instead of levels?
    num_output_levels = len(action.outputs)
    if num_output_levels != 1:
        raise ValueError(
            "A `generate-dataset` action must have exactly one output; "
            f"{action_id} had {num_output_levels}"
        )

    first_output_file = get_first_output_file(action.outputs)
    if first_output_file not in action.run.raw:
        raise ValueError("--output in run command and outputs must match")
