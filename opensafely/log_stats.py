#!/usr/bin/python3
import json
import re
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

DESCRIPTION = "Parse cohortextractor-stats logs as json"
PREFIX_REGEX = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{9}Z"
KEY_VALUE_REGEX = r"(?<=\s)([^\s=]+)=(.*?)(?=(?:\s[^\s=]+=|$))"
ACTION_SUMMARY_REGEX = (
    r"^(state|docker_image_id|job_id|run_by_user|created_at|completed_at):\s(.*)"
)


def add_arguments(parser):
    parser.add_argument(
        "--project-dir",
        help="Project directory (default: current directory)",
        type=Path,
        default=".",
    )
    return parser


def add_parsed_log(stats_dict, current_action, current_log):
    current_log_timestamp = re.match(PREFIX_REGEX, current_log).group()
    current_log = re.sub(r"\s*\n\s*", " ", current_log)
    log_params = dict(re.findall(KEY_VALUE_REGEX, current_log))
    stats_dict[current_action].append(
        {"timestamp": current_log_timestamp, **log_params}
    )


def add_action_stats(stats_dict, current_action, action_stats):
    start_time = action_stats.get("created_at")
    end_time = action_stats.get("completed_at")
    ts_format = "%Y-%m-%dT%H:%M:%SZ"
    if start_time and end_time:
        elapsed = datetime.strptime(end_time, ts_format) - datetime.strptime(
            start_time, ts_format
        )
        action_stats["elapsed_time_secs"] = elapsed.seconds
        action_stats["elapsed_time"] = str(elapsed)
    stats_dict[current_action].insert(0, action_stats)


def main(project_dir):
    # Log the number of actions first
    stats = {"project": {"number_of_actions": 0}}

    log_dir = project_dir / "metadata"

    for filep in (log_dir).glob("*.log"):
        current_action = filep.stem
        stats[current_action] = []
        action_stats = {}
        current_log = None
        for line in filep.open().readlines():
            # Logs in the log file can span multiple lines;
            # check if this line is the beginning of a new log
            if re.match(PREFIX_REGEX, line):
                # If there's a current log, we're finished with it now, parse it add to the stats dict
                if current_log is not None:
                    add_parsed_log(stats, current_action, current_log)
                # Now reset the current log, to the current line if it's a cohort-extractor log
                if "cohortextractor-stats" in line:
                    current_log = line
                else:
                    # This is a standard log, set the current_log to None
                    current_log = None
            elif re.match(ACTION_SUMMARY_REGEX, line):
                # Check for the summary stats lines
                action_stats.update(dict(re.findall(ACTION_SUMMARY_REGEX, line)))
            elif current_log is not None:
                # this isn't a log start, and the previous log start was a stats one, so it
                # must be a continuation
                current_log += line
        # Parse the final log, if there is one
        if current_log is not None:
            add_parsed_log(stats, current_action, current_log)
        add_action_stats(stats, current_action, action_stats)
        stats["project"]["number_of_actions"] += 1

    with (log_dir / "log_stats.json").open("w") as outpath:
        json.dump(stats, outpath, indent=2)
        print(f"Log stats written to {log_dir / 'log_stats.json'}")


def run():
    parser = ArgumentParser(description=DESCRIPTION)
    parser = add_arguments(parser)
    args = parser.parse_args()
    main(project_dir=args.project_dir / "metadata")


if __name__ == "__main__":
    run()
