"""Paginate a public playlist, including a channel's uploads playlist."""

import argparse
from pathlib import Path

from googleapiclient.discovery import build

from examples.common import bounded_int, cli, json_output, required_key


def playlist_videos(youtube, playlist_id: str, limit: int) -> list[dict]:
    items = []
    token = None
    for _ in range((limit + 49) // 50):
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": min(50, limit - len(items)),
        }
        if token:
            params["pageToken"] = token
        response = youtube.playlistItems().list(**params).execute(num_retries=0)
        items.extend(response.get("items", []))
        token = response.get("nextPageToken")
        if not token or len(items) >= limit:
            break
    return items[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id")
    parser.add_argument("--limit", type=bounded_int(1, 5000), default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("YOUTUBE_API_KEY")
    with json_output(args.output) as write:
        with build("youtube", "v3", developerKey=key, cache_discovery=False) as youtube:
            write({"items": playlist_videos(youtube, args.playlist_id, args.limit)})


if __name__ == "__main__":
    cli(main)
