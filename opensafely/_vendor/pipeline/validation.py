from __future__ import annotations

import fnmatch
import posixpath
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

from .constants import LEVEL4_FILE_TYPES
from .exceptions import InvalidPatternError, ValidationError
from .outputs import get_output_dirs


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


def validate_action_config(action_id: str, action_config: Any) -> None:
    # Verifies the required arguments for Action.build are present
    validate_type(action_config, dict, f"Configuration for action {action_id}")
    for key in ["run", "outputs"]:
        if key not in action_config:
            raise ValidationError(
                f"Action {action_id} must contain a configuration for '{key}'"
            )


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


def validate_ehrql_outputs(action_id: str, action: Action) -> None:
    """
    Check ehrQL's output config is valid for this command

    We can't validate outputs in the Action or Outputs models because we need
    to look up other fields (eg run).
    """
    if action.outputs.moderately_sensitive or action.outputs.minimally_sensitive:
        raise ValidationError(
            f"`{action_id}` action uses `generate-dataset` and so all outputs must "
            f"be labelled `highly_sensitive`"
        )

    output_spec = get_output_spec_from_args(action.run.parts)
    if not output_spec:
        raise ValidationError(
            f"`{action_id}` action does not provide an `--output` argument specifying "
            f"where the results of `generate-dataset` should be stored"
        )

    output_patterns = (action.outputs.highly_sensitive or {}).values()
    if not output_patterns_match_spec(output_spec, list(output_patterns)):
        raise ValidationError("--output in run command and outputs must match")


def get_output_spec_from_args(args: list[str]) -> str | None:
    for switch, value in zip(args, args[1:] + [""]):
        if switch == "--output":
            return value
        if switch.startswith("--output="):
            # Need to support 3.8 so no `removeprefix`
            return switch[len("--output=") :]
    return None


def output_patterns_match_spec(spec: str, patterns: list[str]) -> bool:
    directory, extension = split_directory_and_extension(PurePosixPath(spec))
    if extension:
        glob_pattern = f"{directory}/*{extension}"
        return all(fnmatch.fnmatch(pattern, glob_pattern) for pattern in patterns)
    else:
        return spec in patterns


# Borrowed directly from ehrQL:
# https://github.com/opensafely-core/ehrql/blob/e511dca176d0/ehrql/file_formats/main.py#L153-L166
def split_directory_and_extension(filename: PurePath) -> tuple[PurePath, str]:
    name, separator, extension = filename.name.rpartition(":")
    if not separator:
        return filename, ""
    elif not name:
        return filename.parent, f".{extension}"
    else:
        return filename.with_name(name), f".{extension}"
