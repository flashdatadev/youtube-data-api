"""Resolve a YouTube channel handle and find its uploads playlist ID."""

import argparse
from pathlib import Path

from googleapiclient.discovery import build

from examples.common import cli, json_output, required_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--handle", help="For example @GoogleDevelopers")
    target.add_argument("--channel-id", help="A channel ID beginning with UC")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("YOUTUBE_API_KEY")
    params = {"forHandle": args.handle} if args.handle else {"id": args.channel_id}
    with json_output(args.output) as write:
        with build("youtube", "v3", developerKey=key, cache_discovery=False) as youtube:
            response = (
                youtube.channels()
                .list(part="snippet,statistics,contentDetails", **params)
                .execute(num_retries=0)
            )
            write(response)
            return 0 if response.get("items") else 2


if __name__ == "__main__":
    cli(main)
