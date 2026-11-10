import importlib
import json
import sys

import httplib2
import pytest
from googleapiclient.errors import HttpError

from examples.common import json_output, safe_error

MODULES = [
    "google_search",
    "google_video_metadata",
    "google_channel",
    "google_playlist",
    "flashdata_search",
    "flashdata_metadata",
    "flashdata_channel",
    "flashdata_transcript",
    "search_to_dataset",
    "bulk_export",
]


@pytest.mark.parametrize("module", MODULES)
def test_all_help_commands_work_without_keys(module, monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("FLASHDATA_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", [module, "--help"])
    with pytest.raises(SystemExit) as result:
        importlib.import_module("examples." + module).main()
    assert result.value.code == 0


def test_google_error_does_not_leak_key_or_request_uri():
    error = HttpError(
        httplib2.Response({"status": "403"}),
        json.dumps({"error": {"errors": [{"reason": "quotaExceeded"}]}}).encode(),
        uri="https://www.googleapis.com/youtube/v3/search?key=DO_NOT_PRINT_THIS",
    )
    message = safe_error(error)
    assert "quotaExceeded" in message
    assert "DO_NOT_PRINT_THIS" not in message
    assert "googleapis.com" not in message


def test_output_refuses_existing_file_before_request(tmp_path):
    target = tmp_path / "keep.json"
    target.write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError), json_output(target):
        pytest.fail("The request body must not be entered")
    assert target.read_text() == "original"
