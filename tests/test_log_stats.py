import json
import shutil
from pathlib import Path

import pytest

from opensafely import log_stats


@pytest.fixture
def project_path(tmp_path):
    fixture_path = Path(__file__).parent / "fixtures" / "metadata"
    shutil.copytree(fixture_path, tmp_path / "metadata")
    yield tmp_path


def test_log_stats(project_path):
    log_stats.main(project_path)
    stats_output_path = project_path / "metadata" / "log_stats.json"
    assert stats_output_path.exists()

    stats_json = json.load(stats_output_path.open())
    assert sorted(stats_json.keys()) == ["action1", "action2", "project"]

    assert stats_json["project"]["number_of_actions"] == 2
    assert len(stats_json["action1"]) == 9
    assert len(stats_json["action2"]) == 10
    for action in ["action1", "action2"]:
        # First item in each action log list is the summary
        assert list(stats_json[action][0].keys()) == [
            "state",
            "docker_image_id",
            "job_id",
            "run_by_user",
            "created_at",
            "completed_at",
            "elapsed_time_secs",
            "elapsed_time",
        ]
        # elapsed time is calculated from created/completed time and reported in
        # seconds and human-readable H:M:S
        assert stats_json[action][0]["elapsed_time_secs"] == 16
        assert stats_json[action][0]["elapsed_time"] == "0:00:16"
