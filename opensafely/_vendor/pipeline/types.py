"""
Custom types to type check the raw input data

When loading data from YAML we get dictionaries which pydantic attempts to
validate.  Some of our validation is done via custom methods using the raw
dictionary data.
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, TypedDict


RawOutputs = Dict[str, Dict[str, str]]


class RawAction(TypedDict):
    config: dict[Any, Any] | None
    run: str
    needs: list[str] | None
    outputs: RawOutputs
    dummy_data_file: pathlib.Path | None


class RawExpectations(TypedDict):
    population_size: str | int | None


class RawPipeline(TypedDict):
    version: str | float | int
    expectations: RawExpectations
    actions: dict[str, RawAction]
