#!/usr/bin/python3
import json
import re
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

DESCRIPTION = "Parse and output cohortextractor-stats logs as JSONL"
TIMESTAMP_PREFIX_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{9}Z")
COMPLETED_PREFIX_REGEX = re.compile(r"^Completed successfully")
KEY_VALUE_REGEX = re.compile(r"(?<=\s)([^\s=]+)=(.*?)(?=(?:\s[^\s=]+=|$))")
ACTION_SUMMARY_REGEX = re.compile(
        r"^(state|docker_image_id|job_id|run_by_user|created_at|completed_at):\s(.*)"
)


def add_arguments(parser):
    parser.add_argument(
        "--project-dir",
        help="Project directory (default: current directory)",
        type=Path,
        default=".",
    )
    parser.add_argument(
        "--project-name",
        help="Project name (default: project-dir)",
        type=str,
    )
    parser.add_argument(
        "--output-file",
        help="Output json filename (default: log_stats.json)",
        type=Path,
        default="log_stats.json",
    )
    return parser


def _timestamp_for_honeytail(timestamp, ts_format):
    honeytail_ts_format = "%Y-%m-%dT%H:%M:%S.000000000Z"
    dt = datetime.strptime(timestamp, ts_format)
    return dt.strftime(honeytail_ts_format)


def parse_log(project_name, current_action, job_id, current_log):
    current_log_timestamp = TIMESTAMP_PREFIX_REGEX.match(current_log).group()
    current_log = re.sub(r"\s*\n\s*", " ", current_log).strip()
    log_params = dict(KEY_VALUE_REGEX.findall(current_log))
    return {
        "timestamp": current_log_timestamp,
        "project": project_name,
        "job_id": job_id,
        "action": current_action,
        **log_params,
    }


def parse_stats_logs(raw_logs, project_name, current_action, job_id):
    for log in raw_logs:
        yield parse_log(project_name, current_action, job_id, log)


def format_summary_stats(project_name, current_action, summary_stats):
    start_time = summary_stats.get("created_at")
    end_time = summary_stats.get("completed_at")
    ts_format = "%Y-%m-%dT%H:%M:%SZ"
    start_dt = datetime.strptime(start_time, ts_format)

    if start_time and end_time:
        elapsed = datetime.strptime(end_time, ts_format) - start_dt
        summary_stats["elapsed_time_secs"] = elapsed.seconds
        summary_stats["elapsed_time"] = str(elapsed)
    return {
        "timestamp": _timestamp_for_honeytail(start_time, ts_format),
        "project": project_name,
        "action": current_action,
        **{k: v for k, v in summary_stats.items()},
    }


def main(project_dir, output_file, project_name=None):
    log_dir = project_dir / "metadata"
    project_name = project_name or project_dir.resolve().name

    log_files = list(log_dir.glob("*.log"))

    # Find the number of actions (equivalent to the number of log files)
    action_count = len(log_files)
    stats_logs = []
    summary_stats_logs = []

    for filep in log_files:
        current_action = filep.stem
        # Include the total number of actions run alongside this one in each action summary
        summary_stats = {"total_actions_in_job_request": action_count}
        raw_logs = []
        current_log = None
        for line in filep.open().readlines():
            # Logs in the log file can span multiple lines;
            # check if this line is the beginning of a new log or the action summary
            if TIMESTAMP_PREFIX_REGEX.match(line) or COMPLETED_PREFIX_REGEX.match(line):
                # If there's a current log, we're finished with it now, parse it add to the stats dict
                if current_log is not None:
                    raw_logs.append(current_log)
                # Now reset the current log, to the current line if it's a cohort-extractor log
                if "cohortextractor-stats" in line:
                    current_log = line
                else:
                    # This is a standard log, set the current_log to None
                    current_log = None
            elif ACTION_SUMMARY_REGEX.match(line):
                # Check for the summary stats lines
                summary_stats.update(dict(ACTION_SUMMARY_REGEX.findall(line)))
            elif current_log is not None:
                # this isn't a log start, and the previous log start was a stats one, so it
                # must be a continuation
                current_log += line
        # Add the final log, if there is one
        if current_log is not None:
            raw_logs.append(current_log)

        # format the raw logs and add to the main list
        stats_logs.extend(
            parse_stats_logs(
                raw_logs, project_name, current_action, summary_stats["job_id"]
            )
        )

        # Format and add the summary stats
        summary_stats_logs.append(
            format_summary_stats(project_name, current_action, summary_stats)
        )

    with (log_dir / output_file).open("w") as outpath:
        for log in [*summary_stats_logs, *stats_logs]:
            json.dump(log, outpath)
            outpath.write("\n")
    print(f"Log stats written to {log_dir / output_file}")


def run():
    parser = ArgumentParser(description=DESCRIPTION)
    parser = add_arguments(parser)
    args = parser.parse_args()
    main(
        project_dir=args.project_dir / "metadata",
        output_file=args.output_file,
        project_name=args.project_name,
    )


if __name__ == "__main__":
    run()
