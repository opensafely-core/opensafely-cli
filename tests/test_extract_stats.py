import json
import shutil
from pathlib import Path

import pytest

from opensafely import extract_stats


@pytest.fixture
def project_path(tmp_path):
    fixture_path = Path(__file__).parent / "fixtures" / "metadata"
    shutil.copytree(fixture_path, tmp_path / "metadata")
    yield tmp_path


def test_log_stats(project_path):
    extract_stats.main(project_path, "stats.json")
    stats_output_path = project_path / "metadata" / "stats.json"
    assert stats_output_path.exists()

    stats_json = [json.loads(line) for line in stats_output_path.open().readlines()]
    # sort logs by action, with summary log at th
    stats_json.sort(key=lambda x: (x["action"], x.get("state", "")))
    # action 1 and 2 are part of one job request
    # action 1 has 8 stats logs plus one summary log
    # action 2 has 9 stats logs plus one summary log
    # action 3 is a different job request
    # action 3 has 1 stats log plus one summary log

    assert len(stats_json) == 9 + 10 + 2
    summary_logs = [stats_json[8], stats_json[18], stats_json[-1]]
    action1_logs = stats_json[0:8]
    action2_logs = stats_json[10:18]
    action3_logs = stats_json[19:-1]

    for summary_log in summary_logs:
        # First item in each action log list is the summary
        assert list(summary_log.keys()) == [
            "timestamp",
            "project",
            "action",
            "state",
            "docker_image_id",
            "job_id",
            "job_request_id",
            "run_by_user",
            "created_at",
            "completed_at",
            "action_elapsed_time_secs",
            "action_elapsed_time",
            "total_actions_in_job_request",
        ]
        # elapsed time is calculated from created/completed time and reported in
        # seconds and human-readable H:M:S
        assert summary_log["action_elapsed_time_secs"] == 16
        assert summary_log["action_elapsed_time"] == "0:00:16"
    for summary_log in summary_logs[:1]:
        assert summary_log["total_actions_in_job_request"] == 2
        assert summary_log["job_request_id"] == "1234"
    assert summary_logs[2]["total_actions_in_job_request"] == 1
    assert summary_logs[2]["job_request_id"] == "5678"

    # all other logs have the job id, project etc added
    def _assert_keys(log):
        for key in ["job_id", "job_request_id", "timestamp", "project", "action"]:
            assert key in log

    for statslog in action1_logs:
        _assert_keys(statslog)
        assert statslog["job_id"] == "3e6blwbtbxgpm6ji"
        assert statslog["job_request_id"] == "1234"

    for statslog in action2_logs:
        _assert_keys(statslog)
        assert statslog["job_id"] == "yf5dm6ekrw7cv5vo"
        assert statslog["job_request_id"] == "1234"

    for statslog in action3_logs:
        _assert_keys(statslog)
        assert statslog["job_id"] == "123"
        assert statslog["job_request_id"] == "5678"
