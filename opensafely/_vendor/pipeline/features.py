from __future__ import annotations

from types import SimpleNamespace


# The versions of `project.yaml` where each feature applies to
# Tuple of (version where the feature was introduced, version after which the feature is deprecated)
FEATURE_FLAGS_BY_VERSION = {
    "UNIQUE_OUTPUT_PATH": (2, None),
    "EXPECTATIONS_POPULATION": (3, 3),
    "REMOVE_SUPPORT_FOR_COHORT_EXTRACTOR": (4, None),
}

LATEST_VERSION = max([v[0] for v in FEATURE_FLAGS_BY_VERSION.values()])


def get_feature_flags_for_version(version: float) -> SimpleNamespace:
    if version > LATEST_VERSION:
        raise ValueError(f"The latest version is v{LATEST_VERSION}, but got v{version}")
    feat = SimpleNamespace()

    for k, v in FEATURE_FLAGS_BY_VERSION.items():
        # is this feature turned on the requested version?
        if v[1] is None:
            value = v[0] <= version
        else:
            value = v[0] <= version <= v[1]

        setattr(feat, k, value)

    return feat
