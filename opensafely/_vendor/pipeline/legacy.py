from __future__ import annotations

from .main import load_pipeline


def get_all_output_patterns_from_project_file(project_file: str) -> list[str]:
    config = load_pipeline(project_file)
    all_patterns = set()
    for action in config.actions.values():
        for patterns in action.outputs.dict(exclude_unset=True).values():
            all_patterns.update(patterns.values())
    return list(all_patterns)
