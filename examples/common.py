"""Small CLI and file helpers shared by the examples; not a replacement SDK."""

import argparse
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from flashdata.errors import APIError, FlashDataError, ValidationError
from googleapiclient.errors import HttpError

VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")


def required_key(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Set {name} first. See docs/authentication.md.")
    return value


def bounded_int(minimum: int, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        number = int(value)
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"Expected {minimum}–{maximum}.")
        return number

    return parse


def video_id(value: str) -> str:
    if not VIDEO_ID.fullmatch(value):
        raise argparse.ArgumentTypeError("Use an 11-character YouTube video ID, not a URL.")
    return value


def safe_error(exc: Exception) -> str:
    """Do not print HttpError URIs, request headers, signed URLs, or response bodies."""
    if isinstance(exc, HttpError):
        reason = "request_failed"
        try:
            errors = json.loads(exc.content)["error"]["errors"]
            candidate = errors[0]["reason"]
            if re.fullmatch(r"[A-Za-z0-9_]{1,80}", candidate):
                reason = candidate
        except (ValueError, KeyError, TypeError, IndexError):
            pass
        return f"Google HTTP {exc.resp.status}: {reason}. See docs/troubleshooting.md."
    if isinstance(exc, APIError):
        return f"FlashData HTTP {exc.status_code}. See docs/troubleshooting.md."
    if isinstance(exc, FlashDataError):
        return f"FlashData {type(exc).__name__}. See docs/troubleshooting.md."
    if isinstance(exc, OSError):
        return f"File or network error ({type(exc).__name__}). Check paths and connectivity."
    return str(exc)


def cli(main: Callable[[], int | None]) -> None:
    try:
        code = main()
    except (FlashDataError, HttpError, ValueError, OSError) as exc:
        print(safe_error(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        print(
            "Interrupted. See the saved checkpoint or job record before restarting.",
            file=sys.stderr,
        )
        raise SystemExit(130) from None
    raise SystemExit(code or 0)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
        ) as stream:
            temp = Path(stream.name)
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def atomic_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def json_output(path: Path | None):
    """Reserve a fresh output before making requests; never overwrite an existing file."""
    if path is None:
        yield lambda value: print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        yield lambda value: stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def result_payloads(response: dict) -> list[dict]:
    if response.get("status") != "done":
        raise ValueError(
            "FlashData query did not finish successfully. Check the console job history."
        )
    payloads = response.get("results")
    if not isinstance(payloads, list) or any(not isinstance(p, dict) for p in payloads):
        raise ValueError("Unexpected FlashData response structure; no results were discarded.")
    return payloads


def definitely_rejected(exc: Exception) -> bool:
    return isinstance(exc, ValidationError) or (
        isinstance(exc, APIError) and 400 <= exc.status_code < 500 and exc.status_code != 408
    )
