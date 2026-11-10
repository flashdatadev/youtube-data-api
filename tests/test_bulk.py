import json
from unittest.mock import MagicMock

import pytest
from flashdata.errors import PollingTimeoutError

from examples.bulk_export import bulk_export


def bulk_client():
    client = MagicMock()
    client.bulk.create.return_value = {"job": {"id": "bulk_fixture"}, "upload": {"secret": "url"}}
    client.bulk.wait.return_value = {"status": "completed", "counts": {"failed": 0, "invalid": 0}}
    client.bulk.rows.return_value = iter([{"status": "done", "video_id": "jNQXAC9IVRw"}])
    return client


def test_job_id_is_durable_before_upload_and_signed_urls_are_not_saved(tmp_path):
    client = bulk_client()
    input_path = tmp_path / "ids.txt"
    input_path.write_text("jNQXAC9IVRw\n", encoding="utf-8")
    output = tmp_path / "rows.jsonl"
    record = tmp_path / "rows.jsonl.job.json"

    def verify_record(*args):
        saved = json.loads(record.read_text())
        assert saved["bulk_id"] == "bulk_fixture"
        assert saved["phase"] == "created"
        assert "secret" not in record.read_text()

    client.bulk.upload_file.side_effect = verify_record
    assert bulk_export(client, input_path=input_path, output=output) == 0
    client.bulk.start.assert_called_once_with("bulk_fixture")
    assert json.loads(output.read_text())["video_id"] == "jNQXAC9IVRw"


def test_existing_bulk_job_is_never_recreated(tmp_path):
    client = bulk_client()
    client.bulk.get.return_value = {"status": "running"}
    assert bulk_export(client, output=tmp_path / "recovery.jsonl", bulk_id="bulk_fixture") == 0
    client.bulk.create.assert_not_called()
    client.bulk.upload_file.assert_not_called()
    client.bulk.start.assert_not_called()


def test_partial_bulk_keeps_rows_and_returns_nonzero(tmp_path):
    client = bulk_client()
    client.bulk.get.return_value = {"status": "completed"}
    client.bulk.wait.return_value["counts"]["failed"] = 1
    client.bulk.rows.return_value = iter([{"status": "done"}, {"status": "failed"}])
    output = tmp_path / "partial.jsonl"
    assert bulk_export(client, output=output, bulk_id="bulk_fixture") == 2
    assert len(output.read_text().splitlines()) == 2


def test_poll_timeout_preserves_job_id(tmp_path):
    client = bulk_client()
    client.bulk.get.return_value = {"status": "running"}
    client.bulk.wait.side_effect = PollingTimeoutError("bulk_fixture")
    output = tmp_path / "timeout.jsonl"
    with pytest.raises(PollingTimeoutError):
        bulk_export(client, output=output, bulk_id="bulk_fixture")
    record = json.loads((tmp_path / "timeout.jsonl.job.json").read_text())
    assert record["bulk_id"] == "bulk_fixture"


def test_invalid_input_and_existing_outputs_do_not_submit(tmp_path):
    client = bulk_client()
    bad = tmp_path / "bad.txt"
    bad.write_text("https://youtube.com/watch?v=jNQXAC9IVRw\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid video ID"):
        bulk_export(client, input_path=bad, output=tmp_path / "out.jsonl")
    client.bulk.create.assert_not_called()
    output = tmp_path / "already.jsonl"
    output.write_text("keep this", encoding="utf-8")
    with pytest.raises(ValueError, match="fresh output"):
        bulk_export(client, bulk_id="bulk_fixture", output=output)
    assert output.read_text() == "keep this"
