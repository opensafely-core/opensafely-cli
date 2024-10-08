from __future__ import annotations

import posixpath
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

from .constants import LEVEL4_FILE_TYPES
from .exceptions import InvalidPatternError, ValidationError
from .outputs import get_first_output_file, get_output_dirs


if TYPE_CHECKING:  # pragma: no cover
    from .models import Action


def validate_type(val: Any, exp_type: type, loc: str, optional: bool = False) -> None:
    type_lookup: dict[type, str] = {
        str: "string",
        dict: "dictionary of key/value pairs",
        list: "list",
    }
    if optional and val is None:
        return
    if not isinstance(val, exp_type):
        raise ValidationError(f"{loc} must be a {type_lookup[exp_type]}")


def validate_no_kwargs(kwargs: dict[str, Any], loc: str) -> None:
    if kwargs:
        raise ValidationError(f"Unexpected parameters ({', '.join(kwargs)}) in {loc}")


def validate_glob_pattern(pattern: str, privacy_level: str) -> None:
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

    path = Path(pattern)

    if path.suffix == "" or path.suffix.endswith("*"):
        raise InvalidPatternError(
            "output paths must have a file type extension at the end"
        )

    if privacy_level == "moderately_sensitive":
        if path.suffix not in LEVEL4_FILE_TYPES:
            raise InvalidPatternError(
                f"{path} is not an allowed file type for moderately_sensitive outputs"
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


def validate_not_cohort_extractor_action(action: Action) -> None:
    if action.run.parts[0].startswith("cohortextractor"):
        raise ValidationError(
            f"Action {action.action_id} uses cohortextractor actions, which are not supported in this version."
        )


def validate_cohortextractor_outputs(action_id: str, action: Action) -> None:
    """
    Check cohortextractor's output config is valid for this command

    We can't validate outputs in the Action or Outputs models because we need
    to look up other fields (eg run).
    """
    # ensure we only have output level defined.
    num_output_levels = len(action.outputs)
    if num_output_levels != 1:
        raise ValidationError(
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
        raise ValidationError(
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
        raise ValidationError(
            "A `generate-dataset` action must have exactly one output; "
            f"{action_id} had {num_output_levels}"
        )

    first_output_file = get_first_output_file(action.outputs)
    if first_output_file not in action.run.raw:
        raise ValidationError("--output in run command and outputs must match")
