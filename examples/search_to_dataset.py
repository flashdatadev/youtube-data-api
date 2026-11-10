"""Search, deduplicate, collect metadata/transcripts, and export a resumable dataset."""

import argparse
import csv
import io
import json
import os
import sys
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

from flashdata import FlashData

from examples.common import (
    VIDEO_ID,
    atomic_json,
    atomic_text,
    bounded_int,
    cli,
    definitely_rejected,
    required_key,
    result_payloads,
    safe_error,
)


class DemoYouTube:
    """Offline responses with invented videos, never a fallback for failed live requests."""

    def __init__(self):
        fixture = files("examples").joinpath("fixtures/demo.json")
        self.data = json.loads(fixture.read_text(encoding="utf-8"))

    def search(self, query, *, max_results):
        response = self.data["search"]
        response["results"][0]["results"] = response["results"][0]["results"][:max_results]
        return response

    def metadata(self, video_id, **kwargs):
        return self.data["metadata"][video_id]

    def transcript(self, video_id, **kwargs):
        return self.data["transcripts"][video_id]


@contextmanager
def checkpoint_lock(checkpoint: Path):
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    lock = checkpoint.with_suffix(checkpoint.suffix + ".lock")
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def collect_stage(state: dict, stage: dict, checkpoint: Path, operation):
    """Record intent before calling a metered API; unknown results are never auto-retried."""
    if stage["status"] in {"done", "failed"}:
        return
    if stage["status"] != "pending":
        raise ValueError(
            "A previous request has an unknown outcome. Check FlashData job history before "
            "submitting again; this checkpoint will not automatically repeat it."
        )
    stage["status"] = "in_flight"
    atomic_json(checkpoint, state)
    try:
        response = operation()
    except Exception as exc:
        stage["status"] = "failed" if definitely_rejected(exc) else "unknown"
        stage["error"] = safe_error(exc)
        atomic_json(checkpoint, state)
        raise
    stage["response"] = response
    stage["status"] = "done" if response.get("status") == "done" else "failed"
    if stage["status"] == "failed":
        stage["error"] = "query_not_done"
    atomic_json(checkpoint, state)


def search_ids(response: dict, limit: int) -> list[str]:
    ids = []
    for payload in result_payloads(response):
        for item in payload.get("results", []):
            identifier = item.get("videoId")
            if (
                isinstance(identifier, str)
                and VIDEO_ID.fullmatch(identifier)
                and identifier not in ids
            ):
                ids.append(identifier)
    return ids[:limit]


def dataset_rows(state: dict) -> list[dict]:
    rows = []
    for identifier, entry in state["videos"].items():
        metadata = entry["metadata"].get("response", {}).get("results", [])
        tracks = entry["transcript"].get("response", {}).get("results", [])
        valid_metadata = [m for m in metadata if isinstance(m, dict) and not m.get("error")]
        valid_tracks = [
            t for t in tracks if isinstance(t, dict) and not t.get("error") and t.get("fullText")
        ]
        errors = {
            name: stage.get("error", stage["status"])
            for name, stage in entry.items()
            if stage["status"] != "done"
        }
        if not valid_metadata:
            errors.setdefault("metadata", "metadata_unavailable")
        if not valid_tracks:
            errors.setdefault("transcript", "requested_caption_track_unavailable")
        rows.append(
            {
                "video_id": identifier,
                "source_url": f"https://www.youtube.com/watch?v={identifier}",
                "query": state["config"]["query"],
                "provider": "synthetic_demo" if state["config"]["demo"] else "flashdata",
                "status": "complete" if not errors else "partial" if valid_metadata else "failed",
                "metadata": valid_metadata[0] if valid_metadata else None,
                "transcripts": valid_tracks,
                "errors": errors,
            }
        )
    return rows


def export_dataset(state: dict, output: Path, csv_path: Path):
    rows = dataset_rows(state)
    atomic_text(output, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "video_id",
            "source_url",
            "query",
            "provider",
            "status",
            "title",
            "language",
            "transcript",
            "errors",
        ],
    )
    writer.writeheader()
    for row in rows:
        track = next(iter(row["transcripts"]), {})
        writer.writerow(
            {
                **{
                    key: row[key]
                    for key in ("video_id", "source_url", "query", "provider", "status")
                },
                "title": (row["metadata"] or {}).get("title", ""),
                "language": track.get("languageCode", ""),
                "transcript": track.get("fullText", ""),
                "errors": json.dumps(row["errors"], ensure_ascii=False),
            }
        )
    atomic_text(csv_path, buffer.getvalue())


def run_dataset(youtube, *, config: dict, output: Path, resume: bool = False) -> int:
    output = output.resolve()
    if output.suffix.lower() != ".jsonl":
        raise ValueError("Dataset output must end with .jsonl.")
    checkpoint = output.with_suffix(".state.json")
    csv_path = output.with_suffix(".csv")
    with checkpoint_lock(checkpoint):
        if resume:
            state = json.loads(checkpoint.read_text(encoding="utf-8"))
            if state.get("version") != 1 or state.get("config") != config:
                raise ValueError("Checkpoint options differ. Resume using the original options.")
        else:
            if any(path.exists() for path in (output, csv_path, checkpoint)):
                raise ValueError(
                    "Output already exists. Use --resume or choose a fresh output path."
                )
            state = {"version": 1, "config": config, "search": {"status": "pending"}, "videos": {}}
            atomic_json(checkpoint, state)
        try:
            collect_stage(
                state,
                state["search"],
                checkpoint,
                lambda: youtube.search(config["query"], max_results=config["limit"]),
            )
            if state["search"]["status"] != "done":
                raise ValueError("Search failed. Inspect the saved checkpoint before a new run.")
            for identifier in search_ids(state["search"]["response"], config["limit"]):
                state["videos"].setdefault(
                    identifier,
                    {
                        "metadata": {"status": "pending"},
                        "transcript": {"status": "pending"},
                    },
                )
            atomic_json(checkpoint, state)
            for identifier, entry in state["videos"].items():
                collect_stage(
                    state,
                    entry["metadata"],
                    checkpoint,
                    lambda identifier=identifier: youtube.metadata(
                        identifier, include_formats=False
                    ),
                )
                collect_stage(
                    state,
                    entry["transcript"],
                    checkpoint,
                    lambda identifier=identifier: youtube.transcript(
                        identifier, language=config["language"], auto=config["auto"]
                    ),
                )
                export_dataset(state, output, csv_path)
        finally:
            # Preserve completed metadata even when a caption request or later video fails.
            export_dataset(state, output, csv_path)
        rows = dataset_rows(state)
        complete = sum(row["status"] == "complete" for row in rows)
        print(f"Exported {len(rows)} videos ({complete} complete) to {output} and {csv_path}")
        return 0 if rows and complete == len(rows) else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="python tutorial")
    parser.add_argument("--limit", type=bounded_int(1, 20), default=3)
    parser.add_argument("--language", default="en")
    parser.add_argument("--manual-captions", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("output/videos.jsonl"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--demo", action="store_true", help="Synthetic offline fixtures; no API calls"
    )
    args = parser.parse_args()
    config = {
        "query": args.query,
        "limit": args.limit,
        "language": args.language,
        "auto": not args.manual_captions,
        "demo": args.demo,
    }
    if args.demo:
        if args.language != "en" or args.manual_captions:
            parser.error("The demo fixture only contains automatic English captions.")
        print("Offline demo: invented videos and captions, no network requests.", file=sys.stderr)
        return run_dataset(DemoYouTube(), config=config, output=args.output, resume=args.resume)
    with FlashData(api_key=required_key("FLASHDATA_API_KEY")) as client:
        return run_dataset(client.youtube, config=config, output=args.output, resume=args.resume)


if __name__ == "__main__":
    cli(main)
