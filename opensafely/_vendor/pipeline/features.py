from __future__ import annotations

from types import SimpleNamespace


# The version of `project.yaml` where each feature was introduced
FEATURE_FLAGS_BY_VERSION = {
    "UNIQUE_OUTPUT_PATH": 2,
    "EXPECTATIONS_POPULATION": 3,
}


LATEST_VERSION = max(FEATURE_FLAGS_BY_VERSION.values())


def get_feature_flags_for_version(version: float) -> SimpleNamespace:
    feat = SimpleNamespace()

    for k, v in FEATURE_FLAGS_BY_VERSION.items():
        value = v <= version  # is this feature turned on the requested version?

        setattr(feat, k, value)

    return feat
