import pathlib
import re
import shlex
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, TypedDict

from opensafely._vendor.pydantic import BaseModel, root_validator, validator

from .constants import RUN_ALL_COMMAND
from .exceptions import InvalidPatternError
from .features import LATEST_VERSION, get_feature_flags_for_version
from .types import RawOutputs, RawPipeline
from .validation import (
    assert_valid_glob_pattern,
    validate_cohortextractor_outputs,
    validate_databuilder_outputs,
)


cohortextractor_pat = re.compile(r"cohortextractor:\S+ generate_cohort")
databuilder_pat = re.compile(r"databuilder:\S+ generate[-_]dataset")


class Expectations(BaseModel):
    population_size: int

    @validator("population_size", pre=True)
    def validate_population_size(cls, population_size: str) -> int:
        try:
            return int(population_size)
        except (TypeError, ValueError):
            raise ValueError(
                "Project expectations population size must be a number",
            )


class Outputs(BaseModel):
    highly_sensitive: Optional[Dict[str, str]]
    moderately_sensitive: Optional[Dict[str, str]]
    minimally_sensitive: Optional[Dict[str, str]]

    def __len__(self) -> int:
        return len(self.dict(exclude_unset=True))

    @root_validator()
    def at_least_one_output(cls, outputs: Dict[str, str]) -> Dict[str, str]:
        if not any(outputs.values()):
            raise ValueError(
                f"must specify at least one output of: {', '.join(outputs)}"
            )

        return outputs

    @root_validator(pre=True)
    def validate_output_filenames_are_valid(cls, outputs: RawOutputs) -> RawOutputs:
        # we use pre=True here so that we only get the outputs specified in the
        # input data.  With Optional[…] wrapped fields pydantic will set None
        # for us and that just makes the logic a little fiddler with no
        # benefit.
        for privacy_level, output in outputs.items():
            for output_id, filename in output.items():
                try:
                    assert_valid_glob_pattern(filename)
                except InvalidPatternError as e:
                    raise ValueError(f"Output path {filename} is not permitted: {e}")

        return outputs


class Command(BaseModel):
    raw: str  # original string

    class Config:
        # this makes Command hashable, which for some reason due to the
        # Action.parse_run_string works, pydantic requires.
        frozen = True

    @property
    def args(self) -> str:
        return " ".join(self.parts[1:])

    @property
    def name(self) -> str:
        # parts[0] with version split off
        return self.parts[0].split(":")[0]

    @property
    def parts(self) -> List[str]:
        return shlex.split(self.raw)

    @property
    def version(self) -> str:
        # parts[0] with name split off
        return self.parts[0].split(":")[1]


class Action(BaseModel):
    config: Optional[Dict[Any, Any]] = None
    run: Command
    needs: List[str] = []
    outputs: Outputs
    dummy_data_file: Optional[pathlib.Path]

    @validator("run", pre=True)
    def parse_run_string(cls, run: str) -> Command:
        parts = shlex.split(run)

        name, _, version = parts[0].partition(":")
        if not version:
            raise ValueError(
                f"{name} must have a version specified (e.g. {name}:0.5.2)",
            )

        return Command(raw=run)


class PartiallyValidatedPipeline(TypedDict):
    """
    A custom type to type-check the values in "post" root validators

    A root_validator with pre=False (or no kwargs) runs after the values have
    been ingested already, and the `values` arg is a dictionary of model types.

    Note: This is defined here so we don't have to deal with forward reference
    types.
    """

    version: float
    expectations: Expectations
    actions: Dict[str, Action]


class Pipeline(BaseModel):
    version: float
    expectations: Expectations
    actions: Dict[str, Action]

    @property
    def all_actions(self) -> List[str]:
        """
        Get all actions for this Pipeline instance

        We ignore any manually defined run_all action (in later project
        versions this will be an error). We use a list comprehension rather
        than set operators as previously so we preserve the original order.
        """
        return [action for action in self.actions.keys() if action != RUN_ALL_COMMAND]

    @root_validator()
    def validate_actions(
        cls, values: PartiallyValidatedPipeline
    ) -> PartiallyValidatedPipeline:
        # TODO: move to Action when we move name onto it
        validators = {
            cohortextractor_pat: validate_cohortextractor_outputs,
            databuilder_pat: validate_databuilder_outputs,
        }
        for action_id, config in values.get("actions", {}).items():
            for cmd, validator_func in validators.items():
                if cmd.match(config.run.raw):
                    validator_func(action_id, config)

        return values

    @root_validator(pre=True)
    def validate_expectations_per_version(cls, values: RawPipeline) -> RawPipeline:
        """Ensure the expectations key exists for version 3 onwards"""
        try:
            version = float(values["version"])
        except (KeyError, TypeError, ValueError):
            # this is handled in the validate_version_exists and
            # validate_version_value validators
            return values

        feat = get_feature_flags_for_version(version)

        if not feat.EXPECTATIONS_POPULATION:
            # set the default here because pydantic doesn't seem to set it
            # otherwise
            values["expectations"] = {"population_size": 1000}
            return values

        if "expectations" not in values:
            raise ValueError("Project must include `expectations` section")

        if "population_size" not in values["expectations"]:
            raise ValueError(
                "Project `expectations` section must include `population_size` section",
            )

        return values

    @root_validator()
    def validate_outputs_per_version(
        cls, values: PartiallyValidatedPipeline
    ) -> PartiallyValidatedPipeline:
        """
        Ensure outputs are unique for version 2 onwards

        We validate this on Pipeline so we can get the version
        """

        # we're not using pre=True in the validator so we can rely on the
        # version and action keys being the correct type but we have to handle
        # them not existing
        if not (version := values.get("version")):
            return values  # handle missing version

        if (actions := values.get("actions")) is None:
            return values  # hand no actions

        feat = get_feature_flags_for_version(version)
        if not feat.UNIQUE_OUTPUT_PATH:
            return values

        # find duplicate paths defined in the outputs section
        seen_files = []
        for config in actions.values():
            for output in config.outputs.dict(exclude_unset=True).values():
                for filename in output.values():
                    if filename in seen_files:
                        raise ValueError(f"Output path {filename} is not unique")

                    seen_files.append(filename)

        return values

    @root_validator(pre=True)
    def validate_actions_run(cls, values: RawPipeline) -> RawPipeline:
        # TODO: move to Action when we move name onto it
        for action_id, config in values.get("actions", {}).items():
            if config["run"] == "":
                # key is present but empty
                raise ValueError(
                    f"run must have a value, {action_id} has an empty run key"
                )

        return values

    @validator("actions")
    def validate_unique_commands(cls, actions: Dict[str, Action]) -> Dict[str, Action]:
        seen: Dict[Command, List[str]] = defaultdict(list)
        for name, config in actions.items():
            run = config.run
            if run in seen:
                raise ValueError(
                    f"Action {name} has the same 'run' command as other actions: {' ,'.join(seen[run])}"
                )
            seen[run].append(name)

        return actions

    @validator("actions")
    def validate_needs_are_comma_delimited(
        cls, actions: Dict[str, Action]
    ) -> Dict[str, Action]:
        space_delimited = {}
        for name, action in actions.items():
            # find needs definitions with spaces in them
            incorrect = [dep for dep in action.needs if " " in dep]
            if incorrect:
                space_delimited[name] = incorrect

        if not space_delimited:
            return actions

        def iter_incorrect_needs(
            space_delimited: Dict[str, List[str]]
        ) -> Iterable[str]:
            for name, needs in space_delimited.items():
                yield f"Action: {name}"
                for need in needs:
                    yield f" - {need}"

        msg = [
            "`needs` actions should be separated with commas. The following actions need fixing:",
            *iter_incorrect_needs(space_delimited),
        ]

        raise ValueError("\n".join(msg))

    @validator("actions")
    def validate_needs_exist(cls, actions: Dict[str, Action]) -> Dict[str, Action]:
        missing = {}
        for name, action in actions.items():
            unknown_needs = set(action.needs) - set(actions)
            if unknown_needs:
                missing[name] = unknown_needs

        if not missing:
            return actions

        def iter_missing_needs(missing: Dict[str, Set[str]]) -> Iterable[str]:
            for name, needs in missing.items():
                yield f"Action: {name}"
                for need in needs:
                    yield f" - {need}"

        msg = [
            "One or more actions is referencing unknown actions in its needs list:",
            *iter_missing_needs(missing),
        ]
        raise ValueError("\n".join(msg))

    @root_validator(pre=True)
    def validate_version_exists(cls, values: RawPipeline) -> RawPipeline:
        """
        Ensure the version key exists.

        This is a re-implementation of pydantic's field validation so we can
        get a custom error message.  This can be removed when we add a wrapper
        around the models to generate more UI friendly error messages.
        """
        if "version" in values:
            return values

        raise ValueError(
            f"Project file must have a `version` attribute specifying which "
            f"version of the project configuration format it uses (current "
            f"latest version is {LATEST_VERSION})"
        )

    @validator("version", pre=True)
    def validate_version_value(cls, value: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"`version` must be a number between 1 and {LATEST_VERSION}"
            )
