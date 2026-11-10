"""Search public YouTube videos with Google's official API; follow bounded pagination."""

import argparse
from pathlib import Path

from googleapiclient.discovery import build

from examples.common import bounded_int, cli, json_output, required_key


def search_videos(youtube, query: str, limit: int = 10) -> list[dict]:
    videos = []
    seen = set()
    page_token = None
    # A fixed page budget prevents empty/duplicate pages from making an unbounded loop.
    for _ in range((limit + 49) // 50):
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(50, limit - len(videos)),
        }
        if page_token:
            params["pageToken"] = page_token
        response = youtube.search().list(**params).execute(num_retries=0)
        for item in response.get("items", []):
            identifier = item["id"]["videoId"]
            if identifier not in seen:
                seen.add(identifier)
                videos.append(item)
        page_token = response.get("nextPageToken")
        if not page_token or len(videos) >= limit:
            break
    return videos[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search phrase, e.g. 'python tutorial'")
    parser.add_argument("--limit", type=bounded_int(1, 500), default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("YOUTUBE_API_KEY")
    with json_output(args.output) as write:
        with build("youtube", "v3", developerKey=key, cache_discovery=False) as youtube:
            write({"items": search_videos(youtube, args.query, args.limit)})


if __name__ == "__main__":
    cli(main)
