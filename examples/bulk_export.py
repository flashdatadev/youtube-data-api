"""Submit a file of video IDs to FlashData bulk jobs, or export an existing job."""

import argparse
import json
import os
import sys
from pathlib import Path

from flashdata import FlashData

from examples.common import VIDEO_ID, atomic_json, bounded_int, cli, required_key


def validate_input(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not VIDEO_ID.fullmatch(line.strip()):
                raise ValueError(f"Invalid video ID on line {line_number}; use one ID per line.")
            count += 1
    if not count:
        raise ValueError("The input file is empty.")
    return count


def bulk_export(
    client,
    *,
    output: Path,
    input_path: Path | None = None,
    source: str = "youtube_metadata",
    language: str = "en",
    auto: bool = True,
    bulk_id: str | None = None,
    timeout: int = 3600,
) -> int:
    if input_path:
        validate_input(input_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    record = Path(str(output) + ".job.json")
    # An empty reserved record also blocks an accidental second submission after a crash.
    if output.exists() or record.exists():
        raise ValueError(
            "Choose a fresh output path; existing output and job records are preserved."
        )
    with record.open("x", encoding="utf-8") as stream:
        stream.write("{}\n")
        stream.flush()
        os.fsync(stream.fileno())
    with output.open("x", encoding="utf-8") as stream:
        if bulk_id is None:
            if input_path is None:
                raise ValueError("Supply --input or --bulk-id.")
            options = (
                {"include_formats": False}
                if source == "youtube_metadata"
                else {
                    "language": language,
                    "auto": auto,
                }
            )
            receipt = client.bulk.create({"source": source, "options": options})
            bulk_id = receipt["job"]["id"]
            atomic_json(record, {"bulk_id": bulk_id, "phase": "created", "source": source})
            print(f"Saved bulk ID {bulk_id} to {record}", file=sys.stderr, flush=True)
            client.bulk.upload_file(receipt, input_path)
            atomic_json(record, {"bulk_id": bulk_id, "phase": "uploaded", "source": source})
            client.bulk.start(bulk_id)
        else:
            atomic_json(record, {"bulk_id": bulk_id, "phase": "existing_job"})
            job = client.bulk.get(bulk_id)
            if job["status"] == "awaiting_upload":
                raise ValueError(
                    "This job has not started. Check its upload/start state in FlashData; "
                    "--bulk-id only waits for and exports an existing job."
                )
        atomic_json(record, {"bulk_id": bulk_id, "phase": "waiting"})
        completed = client.bulk.wait(bulk_id, timeout=timeout, poll_interval=5)
        for row in client.bulk.rows(bulk_id):
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
        counts = completed.get("counts", {})
        atomic_json(record, {"bulk_id": bulk_id, "phase": "exported", "counts": counts})
    print(f"Exported bulk job {bulk_id} to {output}")
    return 2 if counts.get("failed", 0) or counts.get("invalid", 0) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--input", type=Path, help="UTF-8 file, one video ID per line")
    origin.add_argument("--bulk-id", help="Export an existing job without submitting another")
    parser.add_argument(
        "--source", choices=["youtube_metadata", "youtube_transcript"], default="youtube_metadata"
    )
    parser.add_argument("--language", default="en", help="Transcript jobs only")
    parser.add_argument("--manual-captions", action="store_true", help="Transcript jobs only")
    parser.add_argument("--timeout", type=bounded_int(1, 86400), default=3600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with FlashData(api_key=required_key("FLASHDATA_API_KEY")) as client:
        return bulk_export(
            client,
            output=args.output,
            input_path=args.input,
            bulk_id=args.bulk_id,
            source=args.source,
            language=args.language,
            auto=not args.manual_captions,
            timeout=args.timeout,
        )


if __name__ == "__main__":
    cli(main)
