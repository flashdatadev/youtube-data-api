import importlib
import json
import sys

import httpx
import pytest
from flashdata import FlashData


@pytest.mark.parametrize(
    ("module", "arguments", "expected"),
    [
        (
            "flashdata_search",
            ["python tutorial", "--limit", "3"],
            {"source": "youtube_search", "query": "python tutorial", "params": {"max_results": 3}},
        ),
        (
            "flashdata_metadata",
            ["jNQXAC9IVRw"],
            {
                "source": "youtube_metadata",
                "video_id": "jNQXAC9IVRw",
                "params": {"include_formats": False},
            },
        ),
        (
            "flashdata_channel",
            ["@GoogleDevelopers", "--limit", "5"],
            {
                "source": "youtube_channel",
                "handle": "@GoogleDevelopers",
                "params": {"video_limit": 5},
            },
        ),
        (
            "flashdata_transcript",
            ["jNQXAC9IVRw", "--language", "en", "--manual-captions"],
            {
                "source": "youtube_transcript",
                "video_id": "jNQXAC9IVRw",
                "params": {"language": "en", "auto": False},
            },
        ),
    ],
)
def test_examples_use_real_sdk_request_contract(monkeypatch, tmp_path, module, arguments, expected):
    requests = []

    def handler(request):
        assert request.url.host == "data.flashdata.dev"
        assert request.url.path == "/v1/queries/realtime"
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "status": "done",
                "source": expected["source"],
                "results": [{"title": "Fixture"}],
            },
        )

    example = importlib.import_module("examples." + module)
    monkeypatch.setenv("FLASHDATA_API_KEY", "test-key-not-live")
    monkeypatch.setattr(
        example,
        "FlashData",
        lambda **kw: FlashData(
            **kw,
            transport=httpx.MockTransport(handler),
            trust_env=False,
        ),
    )
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", [module, *arguments, "--output", str(output)])
    assert example.main() in (None, 0)
    assert requests == [expected]
    assert json.loads(output.read_text())["results"][0]["title"] == "Fixture"
