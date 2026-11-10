import csv
import json
from unittest.mock import MagicMock

import pytest
from flashdata.errors import RequestTimeoutError

from examples.search_to_dataset import DemoYouTube, run_dataset

CONFIG = {"query": "python tutorial", "limit": 3, "language": "en", "auto": True, "demo": True}


def test_demo_exports_and_completed_resume_has_no_requests(tmp_path):
    output = tmp_path / "demo.jsonl"
    assert run_dataset(DemoYouTube(), config=CONFIG, output=output) == 0
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    assert all(row["status"] == "complete" and row["provider"] == "synthetic_demo" for row in rows)
    with output.with_suffix(".csv").open(encoding="utf-8", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 3
    client = MagicMock()
    assert run_dataset(client, config=CONFIG, output=output, resume=True) == 0
    assert client.mock_calls == []


def test_duplicate_search_ids_do_not_repeat_metadata_requests(tmp_path):
    client = DemoYouTube()
    matches = client.data["search"]["results"][0]["results"]
    matches[1] = matches[0].copy()
    client.metadata = MagicMock(wraps=client.metadata)
    assert run_dataset(client, config=CONFIG, output=tmp_path / "videos.jsonl") == 0
    assert client.metadata.call_count == 2


def test_missing_transcript_preserves_metadata_and_returns_partial(tmp_path):
    client = DemoYouTube()
    client.data["transcripts"]["demoVid0001"] = {"status": "done", "results": []}
    output = tmp_path / "partial.jsonl"
    assert run_dataset(client, config=CONFIG, output=output) == 2
    first = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert first["status"] == "partial"
    assert first["metadata"]["videoId"] == "demoVid0001"
    assert first["errors"]["transcript"] == "requested_caption_track_unavailable"


def test_timeout_stops_and_resume_never_resubmits_uncertain_request(tmp_path):
    client = DemoYouTube()
    client.transcript = MagicMock(side_effect=RequestTimeoutError("timeout"))
    output = tmp_path / "interrupted.jsonl"
    with pytest.raises(RequestTimeoutError):
        run_dataset(client, config=CONFIG, output=output)
    state = json.loads(output.with_suffix(".state.json").read_text(encoding="utf-8"))
    assert state["videos"]["demoVid0001"]["transcript"]["status"] == "unknown"
    assert state["videos"]["demoVid0001"]["metadata"]["status"] == "done"
    recovering = MagicMock()
    with pytest.raises(ValueError, match="unknown outcome"):
        run_dataset(recovering, config=CONFIG, output=output, resume=True)
    assert recovering.mock_calls == []
    assert json.loads(output.read_text(encoding="utf-8").splitlines()[0])["metadata"] is not None


def test_resume_pending_stages_without_repeating_completed_search(tmp_path):
    output = tmp_path / "pending.jsonl"
    run_dataset(DemoYouTube(), config=CONFIG, output=output)
    state_path = output.with_suffix(".state.json")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["videos"]["demoVid0003"]["transcript"] = {"status": "pending"}
    state_path.write_text(json.dumps(state), encoding="utf-8")
    client = DemoYouTube()
    client.search = MagicMock(side_effect=AssertionError("Search must not repeat"))
    client.metadata = MagicMock(side_effect=AssertionError("Metadata must not repeat"))
    client.transcript = MagicMock(wraps=client.transcript)
    assert run_dataset(client, config=CONFIG, output=output, resume=True) == 0
    client.transcript.assert_called_once_with("demoVid0003", language="en", auto=True)


def test_existing_output_config_change_and_active_lock_are_rejected(tmp_path):
    output = tmp_path / "demo.jsonl"
    run_dataset(DemoYouTube(), config=CONFIG, output=output)
    with pytest.raises(ValueError, match="already exists"):
        run_dataset(DemoYouTube(), config=CONFIG, output=output)
    with pytest.raises(ValueError, match="options differ"):
        run_dataset(DemoYouTube(), config={**CONFIG, "language": "fr"}, output=output, resume=True)
    lock = output.with_suffix(".state.json.lock")
    lock.write_text("pid=example", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_dataset(DemoYouTube(), config=CONFIG, output=output, resume=True)
    assert lock.exists()
