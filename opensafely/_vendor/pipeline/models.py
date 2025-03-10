from __future__ import annotations

import pathlib
import re
import shlex
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .constants import RUN_ALL_COMMAND
from .exceptions import InvalidPatternError, ValidationError
from .features import LATEST_VERSION, get_feature_flags_for_version
from .validation import (
    validate_action_config,
    validate_cohortextractor_outputs,
    validate_ehrql_outputs,
    validate_glob_pattern,
    validate_no_kwargs,
    validate_not_cohort_extractor_action,
    validate_type,
)


# orderd by most common, going forwards
DB_COMMANDS = {
    "ehrql": ("generate-dataset", "generate-measures"),
    "sqlrunner": "*",  # all commands are valid
    "cohortextractor": ("generate_cohort", "generate_codelist_report"),
    "databuilder": ("generate-dataset",),
}


def is_database_action(args: list[str]) -> bool:
    """
    By default actions do not have database access, but certain trusted actions require it
    """
    image = args[0]
    image = image.split(":")[0]
    db_commands = DB_COMMANDS.get(image)
    if db_commands is None:
        return False

    if db_commands == "*":
        return True

    # no command specified
    if len(args) == 1:
        return False

    # 1st arg is command
    return args[1] in db_commands


@dataclass(frozen=True)
class Expectations:
    population_size: int

    @classmethod
    def build(
        cls,
        population_size: Any = None,
        **kwargs: Any,
    ) -> Expectations:
        validate_no_kwargs(kwargs, "project `expectations` section")
        try:
            population_size = int(population_size)
        except (TypeError, ValueError):
            raise ValidationError(
                "Project expectations population size must be a number",
            )
        return cls(population_size)


@dataclass(frozen=True)
class Outputs:
    highly_sensitive: dict[str, str] | None
    moderately_sensitive: dict[str, str] | None
    minimally_sensitive: dict[str, str] | None

    @classmethod
    def build(
        cls,
        action_id: str,
        highly_sensitive: Any = None,
        moderately_sensitive: Any = None,
        minimally_sensitive: Any = None,
        **kwargs: Any,
    ) -> Outputs:
        if (
            highly_sensitive is None
            and moderately_sensitive is None
            and minimally_sensitive is None
        ):
            raise ValidationError(
                f"must specify at least one output of: {', '.join(['highly_sensitive', 'moderately_sensitive', 'minimally_sensitive'])}"
            )

        validate_no_kwargs(kwargs, f"`outputs` section for action {action_id}")

        cls.validate_output_filenames_are_valid(
            action_id, "highly_sensitive", highly_sensitive
        )
        cls.validate_output_filenames_are_valid(
            action_id, "moderately_sensitive", moderately_sensitive
        )
        cls.validate_output_filenames_are_valid(
            action_id, "minimally_sensitive", minimally_sensitive
        )

        return cls(highly_sensitive, moderately_sensitive, minimally_sensitive)

    def __len__(self) -> int:
        return len(self.dict())

    def dict(self) -> dict[str, dict[str, str]]:
        d = {
            k: getattr(self, k)
            for k in [
                "highly_sensitive",
                "moderately_sensitive",
                "minimally_sensitive",
            ]
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def validate_output_filenames_are_valid(
        cls, action_id: str, privacy_level: str, output: Any
    ) -> None:
        if output is None:
            return
        validate_type(output, dict, f"`{privacy_level}` section for action {action_id}")
        for output_id, filename in output.items():
            validate_type(filename, str, f"`{output_id}` output for action {action_id}")
            try:
                validate_glob_pattern(filename, privacy_level)
            except InvalidPatternError as e:
                raise ValidationError(f"Output path {filename} is invalid: {e}")


@dataclass(frozen=True)
class Command:
    raw: str

    @property
    def args(self) -> str:
        return " ".join(self.parts[1:])

    @property
    def name(self) -> str:
        # parts[0] with version split off
        return self.parts[0].split(":")[0]

    @property
    def parts(self) -> list[str]:
        return shlex.split(self.raw)

    @property
    def version(self) -> str:
        # parts[0] with name split off
        return self.parts[0].split(":")[1]


@dataclass(frozen=True)
class Action:
    action_id: str
    outputs: Outputs
    run: Command
    needs: list[str]
    config: dict[Any, Any] | None
    dummy_data_file: pathlib.Path | None

    @classmethod
    def build(
        cls,
        action_id: str,
        outputs: Any,
        run: Any,
        needs: Any = None,
        config: Any = None,
        dummy_data_file: Any = None,
        **kwargs: Any,
    ) -> Action:
        validate_no_kwargs(kwargs, f"action {action_id}")
        validate_type(outputs, dict, f"`outputs` section for action {action_id}")
        validate_type(run, str, f"`run` section for action {action_id}")
        validate_type(
            needs, list, f"`needs` section for action {action_id}", optional=True
        )
        validate_type(
            config, dict, f"`config` section for action {action_id}", optional=True
        )
        validate_type(
            dummy_data_file,
            str,
            f"`dummy_data_file` section for action {action_id}",
            optional=True,
        )

        outputs = Outputs.build(action_id=action_id, **outputs)
        run = cls.parse_run_string(action_id, run)
        needs = needs or []
        for n in needs:
            if " " in n:
                raise ValidationError(
                    f"`needs` actions should be separated with commas, but {action_id} needs `{n}`"
                )
        action = cls(action_id, outputs, run, needs, config, dummy_data_file)

        if re.match(r"cohortextractor:\S+ generate_cohort", run.raw):
            validate_cohortextractor_outputs(action_id, action)
        if re.match(r"(ehrql|databuilder):\S+ generate[-_]dataset", run.raw):
            validate_ehrql_outputs(action_id, action)

        return action

    # Valid image versions. `dev` is for local testing
    # Note: at some point, we probably want to disallow latest.
    VERSION_REGEX = re.compile(r"^((v[\d.]+)|dev|latest)$")

    @classmethod
    def parse_run_string(cls, action_id: str, run: str) -> Command:
        if run == "":
            raise ValidationError(
                f"run must have a value, {action_id} has an empty run key"
            )

        parts = shlex.split(run)

        name, _, version = parts[0].partition(":")

        vmatch = cls.VERSION_REGEX.match(version)
        if not vmatch:
            raise ValidationError(
                f"Action command {name} must have a version specified in the form :vN (e.g. {name}:v2)",
            )

        return Command(raw=run)

    @property
    def is_database_action(self) -> bool:
        return is_database_action(self.run.parts)


@dataclass(frozen=True)
class Pipeline:
    version: float
    actions: dict[str, Action]
    expectations: Expectations | None

    @classmethod
    def build(
        cls,
        version: Any = None,
        actions: Any = None,
        expectations: Any = None,
        **kwargs: Any,
    ) -> Pipeline:
        validate_no_kwargs(kwargs, "project")
        if version is None:
            raise ValidationError(
                f"Project file must have a `version` attribute specifying which "
                f"version of the project configuration format it uses (current "
                f"latest version is {LATEST_VERSION})"
            )

        try:
            version = float(version)
        except (TypeError, ValueError):
            raise ValidationError(
                f"`version` must be a number between 1 and {LATEST_VERSION}"
            )
        feat = get_feature_flags_for_version(version)

        validate_type(actions, dict, "Project `actions` section")

        _actions = dict()
        for action_id, action_config in actions.items():
            validate_action_config(action_id, action_config)
            _actions[action_id] = Action.build(action_id, **action_config)
        actions = _actions

        if feat.REMOVE_SUPPORT_FOR_COHORT_EXTRACTOR:
            for config in actions.values():
                validate_not_cohort_extractor_action(config)

        seen: dict[Command, list[str]] = defaultdict(list)
        for name, config in actions.items():
            run = config.run
            if run in seen:
                raise ValidationError(
                    f"Action {name} has the same 'run' command as other actions: {' ,'.join(seen[run])}"
                )
            seen[run].append(name)

        if feat.UNIQUE_OUTPUT_PATH:
            # find duplicate paths defined in the outputs section
            seen_files = []
            for config in actions.values():
                for output in config.outputs.dict().values():
                    for filename in output.values():
                        if filename in seen_files:
                            raise ValidationError(
                                f"Output path {filename} is not unique"
                            )

                        seen_files.append(filename)

        for a in actions.values():
            for n in a.needs:
                if n not in actions:
                    raise ValidationError(
                        f"Action `{a.action_id}` references an unknown action in its `needs` list: {n}"
                    )

        if feat.REMOVE_SUPPORT_FOR_COHORT_EXTRACTOR:
            if expectations is not None:
                raise ValidationError(
                    "Project includes `expectations` section, which is not supported in this version"
                )
        elif feat.EXPECTATIONS_POPULATION:
            if expectations is None:
                raise ValidationError("Project must include `expectations` section")
        else:
            expectations = {"population_size": 1000}

        if expectations is not None:
            validate_type(expectations, dict, "Project `expectations` section")
            if "population_size" not in expectations:
                raise ValidationError(
                    "Project `expectations` section must include `population_size` section",
                )
            expectations = Expectations.build(**expectations)

        return cls(version, actions, expectations)

    @property
    def all_actions(self) -> list[str]:
        """
        Get all actions for this Pipeline instance

        We ignore any manually defined run_all action (in later project
        versions this will be an error). We use a list comprehension rather
        than set operators as previously so we preserve the original order.
        """
        return [action for action in self.actions.keys() if action != RUN_ALL_COMMAND]

    @property
    def action_images(self) -> set[str]:
        """
        Get all unique action images/version used in this project.

        This is useful for tooling to know which image version to support.
        """
        images = set()
        for action in self.actions.values():
            # for hysterical raisins, :latest is actually mapped to v1, not v2 or later.
            # We hope to fix this at some point
            version = "v1" if action.run.version == "latest" else action.run.version
            images.add(f"{action.run.name}:{version}")

        return images
