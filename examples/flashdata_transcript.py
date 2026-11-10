"""Retrieve existing YouTube caption text and timestamps with FlashData."""

import argparse
from pathlib import Path

from flashdata import FlashData

from examples.common import cli, json_output, required_key, result_payloads, video_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_id", type=video_id)
    parser.add_argument("--language", default="en")
    parser.add_argument("--manual-captions", action="store_true", help="Request uploader captions")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("FLASHDATA_API_KEY")
    with json_output(args.output) as write:
        with FlashData(api_key=key) as client:
            response = client.youtube.transcript(
                args.video_id, language=args.language, auto=not args.manual_captions
            )
            write(response)
            return 0 if result_payloads(response) else 2


if __name__ == "__main__":
    cli(main)
