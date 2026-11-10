# YouTube Data API Toolkit

[![Python examples](https://github.com/flashdatadev/youtube-data-api/actions/workflows/ci.yml/badge.svg)](https://github.com/flashdatadev/youtube-data-api/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Practical Python examples for the YouTube Data API: search videos, retrieve metadata and channel information, collect available transcripts, and export datasets to JSONL and CSV.**


Start with Google's official YouTube Data API v3 for public video data, or use FlashData for transcript and bulk collection workflows. Every example is a runnable Python module with command-line help. An offline demo lets you generate your first dataset without an API key.

Maintained by [FlashData](https://flashdata.dev/products/youtube-data?utm_source=github&utm_medium=readme&utm_campaign=youtube-data-api). This is an independent toolkit, not an official Google SDK. The FlashData examples use the existing [FlashData Python SDK](https://github.com/flashdatadev/flashdata-python).

[Quick start](#quick-start) · [Examples](#python-examples) · [Dataset workflow](#search-to-dataset-workflow) · [Authentication](docs/authentication.md) · [Troubleshooting](docs/troubleshooting.md)

## What you can build

- A video search tool that returns titles, IDs, channels, and source URLs.
- A channel catalog using channel details and a paginated uploads playlist.
- A transcript collection with caption text, languages, and timestamps.
- A research or retrieval dataset with one record per video and explicit missing-data status.
- A bulk metadata or transcript export from an existing file of YouTube video IDs.

## Choose the API for your task

| Task | Google YouTube Data API v3 examples | FlashData examples |
| --- | --- | --- |
| Authentication | Google Cloud API key | FlashData API key |
| Video search | Search results with bounded pagination | Search up to 20 results per example run |
| Video metadata | Titles, descriptions, duration, statistics; up to 50 IDs per call | Structured metadata for a video ID |
| Channel data | Handle or channel ID, statistics, uploads playlist ID | Handle, channel details, bounded video list |
| Playlist pagination | Included | Not included in this toolkit |
| Existing transcripts | Not provided by these Google API-key examples | Caption text, language, and timestamped segments |
| Bulk export | Metadata example batches Google requests | Managed bulk jobs from a file of video IDs |
| Credentials needed for offline demo | None | None |

These are different APIs with different credentials and response formats. You only need a key for the provider you choose. Google's caption download endpoint requires OAuth and permission to edit the video; a public-data API key does not give access to arbitrary video transcripts. See [Google's caption download reference](https://developers.google.com/youtube/data/reference/rest/v3/captions/download).

## Quick start

Requires **Python 3.10 or newer**. Run these commands from a terminal:

```bash
git clone https://github.com/flashdatadev/youtube-data-api.git
cd youtube-data-api
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install the examples and run the offline dataset demo:

```bash
python -m pip install -e .
python -m examples.search_to_dataset --demo --output output/demo.jsonl
```

The demo writes:

```text
output/demo.jsonl       One structured record per video
output/demo.csv         A flat table of titles, captions, and source URLs
output/demo.state.json  A checkpoint for resuming this run
```

The three demo videos and their captions are **synthetic fixtures**. The demo makes no network requests and spends no credits. Browse the committed [JSONL](sample-data/demo.jsonl) and [CSV](sample-data/demo.csv) outputs before running it.

To rerun into the same files, keep the original options and add `--resume`. Completed stages are loaded from the checkpoint:

```bash
python -m examples.search_to_dataset --demo --output output/demo.jsonl --resume
```

## Get a YouTube Data API key

For the Google examples, enable **YouTube Data API v3** in your Google Cloud project, create an API key, and set `YOUTUBE_API_KEY` in your shell. See the [authentication walkthrough](docs/authentication.md) and [Google's getting-started guide](https://developers.google.com/youtube/v3/getting-started).

For the FlashData examples, create an account at [flashdata.dev](https://flashdata.dev/?utm_source=github&utm_medium=readme&utm_campaign=youtube-data-api), get your key from the console, and set `FLASHDATA_API_KEY`.

```bash
# macOS / Linux — set the key for the examples you want to run
export YOUTUBE_API_KEY="your-google-api-key"
export FLASHDATA_API_KEY="your-flashdata-api-key"
```

```powershell
# Windows PowerShell
$env:YOUTUBE_API_KEY = "your-google-api-key"
$env:FLASHDATA_API_KEY = "your-flashdata-api-key"
```

The examples read environment variables. `.env.example` is a reference, not an automatically loaded configuration file. Google calls consume your project's quota; live FlashData calls consume account credits. Start with the small limits below.

## Python examples

Run from the repository root after installation. Use `--help` with any module to see its arguments. Basic examples print JSON by default; `--output` saves to a **new** file and refuses to overwrite an existing one.

| Example | Command | Output |
| --- | --- | --- |
| Google video search | `python -m examples.google_search "python tutorial" --limit 5` | Video IDs and snippets |
| Google video metadata | `python -m examples.google_video_metadata jNQXAC9IVRw` | Metadata, statistics, missing IDs |
| Google channel lookup | `python -m examples.google_channel --handle @GoogleDevelopers` | Channel details and uploads playlist ID |
| Google playlist pagination | `python -m examples.google_playlist YOUR_PLAYLIST_ID --limit 100` | Playlist items across bounded pages |
| FlashData video search | `python -m examples.flashdata_search "python tutorial" --limit 5` | Full search response |
| FlashData video metadata | `python -m examples.flashdata_metadata jNQXAC9IVRw` | Full metadata response |
| FlashData channel lookup | `python -m examples.flashdata_channel @GoogleDevelopers --limit 10` | Channel details and video list |
| FlashData transcript | `python -m examples.flashdata_transcript VIDEO_ID --language en` | Available caption text and timestamps |

Replace `YOUR_PLAYLIST_ID` and `VIDEO_ID` with actual IDs. A video ID is the 11-character value in a YouTube watch URL's `v` parameter. Caption availability depends on the chosen video and language; see [transcripts](docs/transcripts.md).

### Search YouTube videos in Python

The official API example uses Google's maintained Python client:

```python
import os
from googleapiclient.discovery import build

with build(
    "youtube",
    "v3",
    developerKey=os.environ["YOUTUBE_API_KEY"],
    cache_discovery=False,
) as youtube:
    response = (
        youtube.search()
        .list(
            part="snippet",
            q="python tutorial",
            type="video",
            maxResults=5,
        )
        .execute(num_retries=0)
    )
    for item in response.get("items", []):
        print(item["id"]["videoId"], item["snippet"]["title"])
```

The runnable [search example](examples/google_search.py) adds command-line arguments, a result limit, deduplication, and `nextPageToken` handling. To collect video statistics or duration, pass the returned IDs to [the metadata example](examples/google_video_metadata.py); those fields are not part of search snippets.

### Get video metadata with FlashData

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.environ["FLASHDATA_API_KEY"]) as client:
    response = client.youtube.metadata("jNQXAC9IVRw", include_formats=False)
    for video in response.get("results", []):
        print(video.get("videoId"), video.get("title"))
```

Use [the runnable metadata example](examples/flashdata_metadata.py) for status checking and JSON output. For transcripts, [the transcript example](examples/flashdata_transcript.py) calls `client.youtube.transcript()` and preserves the full response, including caption segments.

## Search-to-dataset workflow

Go from a topic to a small dataset in one command:

```bash
python -m examples.search_to_dataset --query "python tutorial" --limit 3 --language en --output output/python-tutorials.jsonl
```

```text
Search YouTube
    ↓
Deduplicate video IDs
    ↓
Retrieve each video's metadata
    ↓
Retrieve available captions
    ↓
Export JSONL + CSV + checkpoint
```

This workflow uses **FlashData**. It makes one search request and up to two requests per selected video. `--limit` defaults to 3 and is capped at 20. It selects automatic English captions by default; use `--manual-captions` for uploader-provided tracks.

Each JSONL record contains:

| Field | Meaning |
| --- | --- |
| `video_id`, `source_url` | Video identifier and original YouTube URL |
| `query`, `provider` | Collection context; demo rows identify themselves as synthetic |
| `status` | `complete`, `partial`, or `failed` |
| `metadata` | Structured video metadata, or `null` when unavailable |
| `transcripts` | Available caption tracks, including full text and timed segments |
| `errors` | Missing data or failed-stage details, rather than silently dropped videos |

Resume with the **same query, limit, language, and output**:

```bash
python -m examples.search_to_dataset --query "python tutorial" --limit 3 --language en --output output/python-tutorials.jsonl --resume
```

Successful stages are not requested again. If an interrupted request has an unknown outcome, the script stops for inspection rather than automatically submitting it again. Completed metadata is still exported when transcripts are unavailable. See [dataset checkpoints and recovery](docs/datasets.md).

## Bulk YouTube metadata and transcript exports

Already have video IDs? Use [bulk_export.py](examples/bulk_export.py) to upload a UTF-8 file containing one ID per line:

```bash
python -m examples.bulk_export --input sample-data/video-ids.txt --source youtube_metadata --output output/bulk-metadata.jsonl
python -m examples.bulk_export --input sample-data/video-ids.txt --source youtube_transcript --language en --output output/bulk-transcripts.jsonl
```

The example saves the bulk job ID **before uploading or starting work**. If polling or export is interrupted, recover the ID from `output/bulk-metadata.jsonl.job.json` and export the existing job to a fresh file:

```bash
python -m examples.bulk_export --bulk-id YOUR_BULK_JOB_ID --output output/bulk-recovered.jsonl
```

Recovery does not create a new job. Result rows, including failed items, are preserved in the export. A partial job returns a nonzero exit code. See [bulk recovery details](docs/datasets.md#bulk-job-recovery).

## Common questions

**Is this Google's official YouTube Data API SDK?**

No. This repository contains examples maintained by FlashData. The Google examples use `google-api-python-client`; the FlashData examples use `flashdata`.

**Can I use the Google examples without a FlashData account?**

Yes. Only `YOUTUBE_API_KEY` is needed for those examples. The offline dataset demo needs neither key.

**Does the YouTube Data API download video files?**

These examples collect structured data. For media files and delivery to cloud storage, see [FlashData's YouTube Download API](https://flashdata.dev/products/youtube-download?utm_source=github&utm_medium=readme&utm_campaign=youtube-data-api).

**Can I collect every video from a channel?**

The Google channel example returns the uploads playlist ID. Pass it to the playlist example and choose an explicit limit. Search results are not a complete channel inventory. See [pagination and quotas](docs/pagination-and-quotas.md).

**Can I use these outputs in a retrieval or AI pipeline?**

The JSONL output retains video URLs, metadata, text, and caption timestamps for downstream indexing. For larger collection and delivery projects, see [YouTube Video Datasets](https://flashdata.dev/products/youtube-video-datasets?utm_source=github&utm_medium=readme&utm_campaign=youtube-data-api).

## Development and tests

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Tests use fixtures and mocked transports, including the installed FlashData SDK. They check pagination, request parameters, missing-data preservation, credential-safe errors, checkpoint recovery, and bulk job reuse. CI also runs the offline dataset demo. No live credentials are required by CI.

See [CONTRIBUTING.md](CONTRIBUTING.md) for adding examples or reporting an issue. Please include the command, Python version, and sanitized error, never API keys.

## Documentation and related projects

- [Authentication](docs/authentication.md)
- [Pagination and API quotas](docs/pagination-and-quotas.md)
- [YouTube transcripts and captions](docs/transcripts.md)
- [Dataset schema, checkpoints, and bulk exports](docs/datasets.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Google YouTube Data API documentation](https://developers.google.com/youtube/data)
- [FlashData API documentation](https://flashdata.dev/docs)
- [FlashData Python SDK](https://github.com/flashdatadev/flashdata-python)
- [FlashData CLI](https://github.com/flashdatadev/flashdata-cli)
- [FlashData agent skills](https://github.com/flashdatadev/flashdata-skills)

Code is available under the [MIT license](LICENSE).
