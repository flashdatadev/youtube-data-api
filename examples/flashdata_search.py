"""Search YouTube using the FlashData Python SDK and save the full response."""

import argparse
from pathlib import Path

from flashdata import FlashData

from examples.common import bounded_int, cli, json_output, required_key, result_payloads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=bounded_int(1, 20), default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = required_key("FLASHDATA_API_KEY")
    with json_output(args.output) as write:
        with FlashData(api_key=key) as client:
            response = client.youtube.search(args.query, max_results=args.limit)
            write(response)
            result_payloads(response)


if __name__ == "__main__":
    cli(main)
