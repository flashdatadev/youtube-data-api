# Dataset exports and recovery

## Small topic-based collections

`examples.search_to_dataset` accepts a query and a limit of 1–20 videos. It uses one FlashData search request, deduplicates valid video IDs, then retrieves metadata and an existing caption track for each video.

```bash
python -m examples.search_to_dataset --query "machine learning tutorial" --limit 5 --output output/ml.jsonl
```

The output contains a JSONL record per selected ID. Metadata retains the provider's field names. Captions retain timestamped segments. The CSV is a flat view with `video_id`, `source_url`, `query`, `provider`, `status`, `title`, `language`, `transcript`, and `errors`.

Each record is `complete`, `partial` (metadata exists but another part is missing), or `failed`. Check this field before using the data downstream. Exit code **0** means all selected rows are complete, **2** means partial/empty results, and **1** means a request, state, or file error. Interrupting with Ctrl+C exits with **130**.

## Checkpoints

For `output/ml.jsonl`, state is stored in `output/ml.state.json`. The file contains run options, request stage statuses, and the responses already received. It does not contain your API key. Export files are regenerated from this state using atomic file replacement.

Resume with the same query, limit, language, caption type, demo mode, and output path:

```bash
python -m examples.search_to_dataset --query "machine learning tutorial" --limit 5 --output output/ml.jsonl --resume
```

- `done`: result saved; no repeated request on resume.
- `failed`: a known failure saved; not automatically retried.
- `pending`: request has not started.
- `in_flight` / `unknown`: the request may have reached the service, but its result was not saved. Automatic resume stops here.

For an unknown outcome, inspect FlashData's console job history. Preserve the original checkpoint and exports. Start a new run only after you have decided whether another request is needed; a new run can consume credits again. This example does not claim exactly-once delivery across network failures.

A `.state.json.lock` file prevents concurrent writers. Normal exits remove it. After a force-killed process, verify that the old process has stopped before removing its stale lock. Do not remove a lock while a run is active.

The JSONL and CSV are replaced separately. If interrupted between exports, resume rebuilds both from the same checkpoint without repeating completed requests. The raw state is the recovery source.

## Bulk job recovery

`examples.bulk_export` accepts a UTF-8 file with one 11-character video ID per line. It validates the file before submitting. Remove duplicates in your source list if you do not want repeated inputs; this example streams validation without holding a large file in memory.

For each new run, the script reserves a new output file and a `.job.json` record. It saves the job ID immediately after creation, before uploading the file and starting work. Signed upload URLs are not saved in the record.

If waiting or exporting fails after the job has started:

1. Keep the original output, even if incomplete.
2. Read `bulk_id` from its `.job.json` record.
3. Use `--bulk-id` and a **fresh** output file to wait for and export that same job.

```bash
python -m examples.bulk_export --bulk-id YOUR_BULK_JOB_ID --output output/recovered.jsonl
```

The recovery command does not create, upload, start, or resubmit work. A local timeout does not cancel the server job. Paused, failed, or cancelled jobs stop with an error rather than producing a misleading success message.

If a record says `created` or `uploaded`, inspect the job before continuing: it may need an upload or start operation. An empty `{}` record means creation did not return a saved ID; check the console before creating another job. Recovery with `--bulk-id` reports an `awaiting_upload` job rather than waiting indefinitely for work that has not started.

Result exports preserve all returned rows, including item failures. The program exits with code 2 when the completed job's counts report failed or invalid inputs. Download results promptly: FlashData bulk result files have a retention window; check the job's expiry and current [bulk documentation](https://flashdata.dev/docs).

## Sample data

`sample-data/demo.jsonl` and `sample-data/demo.csv` are generated from the synthetic fixture in `examples/fixtures/demo.json`. They illustrate the export schema, not live YouTube data. `sample-data/video-ids.txt` contains public example IDs for real API calls; it does not promise available captions.
