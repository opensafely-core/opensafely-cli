#!/usr/bin/python3
import json
import re
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime
from pathlib import Path


DESCRIPTION = "Parse and output cohortextractor-stats logs as JSONL"
TIMESTAMP_PREFIX_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{9}Z")
COMPLETED_PREFIX_REGEX = re.compile(r"^Completed successfully|outputs:")
KEY_VALUE_REGEX = re.compile(r"(?<=\s)([^\s=]+)=(.*?)(?=(?:\s[^\s=]+=|$))")
ACTION_SUMMARY_REGEX = re.compile(
    r"^(state|exit_code|docker_image_id|job_id|job_request_id|run_by_user|created_at|completed_at|local_run):\s(.*)"
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
        help="Output json filename (default: extracted_stats.json)",
        type=Path,
        default="extracted_stats.json",
    )
    return parser


def _timestamp_for_honeytail(ts_datetime):
    honeytail_ts_format = "%Y-%m-%dT%H:%M:%S.000000000Z"
    return ts_datetime.strftime(honeytail_ts_format)


def parse_log(project_name, current_action, job_id, job_request_id, current_log):
    current_log_timestamp = TIMESTAMP_PREFIX_REGEX.match(current_log).group()
    current_log = re.sub(r"\s*\n\s*", " ", current_log).strip()
    log_params = dict(KEY_VALUE_REGEX.findall(current_log))
    return {
        "timestamp": current_log_timestamp,
        "project": project_name,
        "job_id": job_id,
        "job_request_id": job_request_id,
        "action": current_action,
        **log_params,
    }


def parse_stats_logs(raw_logs, project_name, current_action, job_id, job_request_id):
    for log in raw_logs:
        yield parse_log(project_name, current_action, job_id, job_request_id, log)


def _parse_summary_datetime(datetime_string, ts_format):
    """
    Created/completed in the log summary may be a stingified int (unix time)
    or ISO-8061 UTC format
    Convert the string to a datetime object and return both the datetime object and
    its ISO-8061 UTC string
    """
    try:
        datetime_obj = datetime.fromtimestamp(int(datetime_string))
        return datetime_obj, datetime_obj.strftime(ts_format)
    except ValueError:
        return datetime.strptime(datetime_string, ts_format), datetime_string


def format_summary_stats(project_name, current_action, summary_stats):
    start_time = summary_stats.get("created_at")
    end_time = summary_stats.get("completed_at")

    iso_utc_format = "%Y-%m-%dT%H:%M:%SZ"

    start_dt, start_time_formatted = _parse_summary_datetime(start_time, iso_utc_format)
    summary_stats["created_at"] = start_time_formatted
    if start_time and end_time:
        end_dt, end_time_formatted = _parse_summary_datetime(end_time, iso_utc_format)
        elapsed = end_dt - start_dt
        # prefix summary elapsed time to make filtering easier
        summary_stats["action_elapsed_time_secs"] = elapsed.seconds
        summary_stats["action_elapsed_time"] = str(elapsed)
        summary_stats["completed_at"] = end_time_formatted

    return {
        # add the timestamp field in the format that honeytail requires
        "timestamp": _timestamp_for_honeytail(start_dt),
        "project": project_name,
        "action": current_action,
        **{k: v for k, v in summary_stats.items()},
    }


def add_action_counts_by_job_request(summary_stats_list):
    job_request_counts = Counter(
        [
            summary.get("job_request_id")
            for summary in summary_stats_list
            if "job_request_id" in summary
        ]
    )
    # Include the total number of actions run alongside this one in each action summary
    summary_stats_with_action_counts = []
    for summary in summary_stats_list:
        job_request_id = summary.get("job_request_id")
        action_count = job_request_counts[job_request_id] if job_request_id else 0
        summary_stats_with_action_counts.append(
            {**summary, "total_actions_in_job_request": action_count}
        )
    return summary_stats_with_action_counts


def main(project_dir, output_file, project_name=None):
    """
    Read all log files from the project's metadata folder and extract stats logs.

    Cohort-extractor actions log stats with the event "cohortextractor-stats",
    which is used to idenitfy stats logs, and any number of key-value pairs of
    stats data in the format key=value.  Logs can span multiple lines, and values in
    a key=value pair can contain spaces.

    In addition, each log file contains a section with overall job summary data, which
    is extracted into a single additional log, and other non-stats logs, which are ignored.

    Output is in JSONL format, one log per line.
    """
    log_dir = project_dir / "metadata"
    project_name = project_name or project_dir.resolve().name

    log_files = list(log_dir.glob("*.log"))

    stats_logs = []
    summary_stats_logs = []

    for filep in log_files:
        current_action = filep.stem
        summary_stats = {}
        raw_logs = []
        # logs in the log file can span multiple lines, and are a mixture of stats logs,
        # which we want to extract, and other logs, which we mostly don't care about.
        # `extracted_log` keeps track of the log that's being parsed as we interate over the log
        # file line-by-line, collecting the stats logs into the `raw_logs` list

        extracted_log = None
        for line in filep.open().readlines():
            # check if this line is the beginning of a new log or the beginning of the end-of-file
            # action summary
            if TIMESTAMP_PREFIX_REGEX.match(line) or COMPLETED_PREFIX_REGEX.match(line):
                # We're at the beginning of a new log
                # If we were in the process of extracting a log, we're finished with it now
                # Add it to the list of raw logs to be processed later
                # (extracted_log can be None if we're at the beginning of the file, or if
                # the previous line wasn't a stats log)
                if extracted_log is not None:
                    raw_logs.append(extracted_log)
                # Now reset the extracted_log...
                if "cohortextractor-stats" in line:
                    # ...to the current line if it's a stats log
                    extracted_log = line
                else:
                    # ...to None if it's a standard non-stats log
                    extracted_log = None
            elif ACTION_SUMMARY_REGEX.match(line):
                # Check for the summary stats lines
                summary_stats.update(dict(ACTION_SUMMARY_REGEX.findall(line)))
            elif extracted_log is not None:
                # this line isn't a log start, and we're in the process of extracting a log,
                # so it must be a continuation line. Append it to the log we're extracting.
                extracted_log += line
        # Add the final extracted log, if there is one
        if extracted_log is not None:
            raw_logs.append(extracted_log)

        # At the end of each processed file, we parse the raw logs into a dict
        # and add them to the full list that will be written to file
        if raw_logs:
            stats_logs.extend(
                parse_stats_logs(
                    raw_logs,
                    project_name,
                    current_action,
                    summary_stats.get("job_id"),
                    summary_stats.get("job_request_id"),
                )
            )

        # Format and add the summary stats
        # Check for job_id in case we encountered other, non-job logs in the metadata folder
        if summary_stats.get("job_id"):
            summary_stats_logs.append(
                format_summary_stats(project_name, current_action, summary_stats)
            )

    # Now that all log files are processed, find the action acounts by
    # job request
    summary_stats_logs = add_action_counts_by_job_request(summary_stats_logs)

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
