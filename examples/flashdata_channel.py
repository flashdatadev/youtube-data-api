"""Retrieve a YouTube channel and a bounded set of its videos with FlashData."""

import argparse
from pathlib import Path

from flashdata import FlashData

from examples.common import bounded_int, cli, json_output, required_key, result_payloads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handle", help="For example @GoogleDevelopers")
    parser.add_argument("--limit", type=bounded_int(1, 100), default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("FLASHDATA_API_KEY")
    with json_output(args.output) as write:
        with FlashData(api_key=key) as client:
            response = client.youtube.channel(args.handle, video_limit=args.limit)
            write(response)
            return 0 if result_payloads(response) else 2


if __name__ == "__main__":
    cli(main)
