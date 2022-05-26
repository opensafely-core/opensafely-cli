from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Iterator


if TYPE_CHECKING:  # pragma: no cover
    from .models import Outputs


def get_first_output_file(output_spec: Outputs) -> str:
    return next(iter_all_outputs(output_spec))


def get_output_dirs(output_spec: Outputs) -> list[PurePosixPath]:
    """
    Given the set of output files specified by an action, return a list of the
    unique directory names of those outputs
    """
    filenames = iter_all_outputs(output_spec)

    return list({PurePosixPath(filename).parent for filename in filenames})


def iter_all_outputs(output_spec: Outputs) -> Iterator[str]:
    for group in output_spec.dict(exclude_unset=True).values():
        yield from group.values()
