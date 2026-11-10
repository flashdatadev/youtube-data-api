"""Get video titles, duration, channel IDs, and statistics with the YouTube Data API v3."""

import argparse
from pathlib import Path

from googleapiclient.discovery import build

from examples.common import cli, json_output, required_key, video_id


def video_metadata(youtube, ids: list[str]) -> dict:
    ids = list(dict.fromkeys(ids))
    items = []
    for offset in range(0, len(ids), 50):
        response = (
            youtube.videos()
            .list(part="snippet,contentDetails,statistics", id=",".join(ids[offset : offset + 50]))
            .execute(num_retries=0)
        )
        items.extend(response.get("items", []))
    returned = {item["id"] for item in items}
    return {"items": items, "missing_video_ids": [item for item in ids if item not in returned]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_ids", nargs="+", type=video_id)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("YOUTUBE_API_KEY")
    with json_output(args.output) as write:
        with build("youtube", "v3", developerKey=key, cache_discovery=False) as youtube:
            result = video_metadata(youtube, args.video_ids)
            write(result)
            return 2 if result["missing_video_ids"] else 0


if __name__ == "__main__":
    cli(main)
