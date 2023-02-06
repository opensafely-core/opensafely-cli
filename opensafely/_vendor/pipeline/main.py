from __future__ import annotations

from pathlib import Path

from opensafely._vendor import pydantic

from .exceptions import ProjectValidationError, YAMLError
from .loading import parse_yaml_file
from .models import Pipeline


def load_pipeline(pipeline_config: str | Path, filename: str | None = None) -> Pipeline:
    """
    Main entrypoint for function for parsing pipeline configs

    The given pipeline_config should be the contents of a config file to be
    parsed and validated.

    The optional filename will add filenames to validation errors of YAML
    configs, which is useful in user facing contexts.
    """
    # parse
    try:
        parsed_data = parse_yaml_file(pipeline_config, filename=filename)
    except YAMLError as e:
        raise ProjectValidationError(*e.args)

    # validate
    try:
        return Pipeline(**parsed_data)
    except pydantic.ValidationError as exc:
        raise ProjectValidationError(
            f"Invalid project: {filename or ''}\n{exc}"
        ) from exc
