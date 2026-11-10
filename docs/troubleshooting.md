# Troubleshooting

| Symptom | What to check |
| --- | --- |
| `Set YOUTUBE_API_KEY first` | Set the variable in the same terminal running Python. Google examples do not use the FlashData key. |
| `Set FLASHDATA_API_KEY first` | Set your FlashData console key. The `.env.example` file is not loaded automatically. |
| Google `accessNotConfigured` | Enable YouTube Data API v3 in the key's Google Cloud project. |
| Google `keyInvalid` or HTTP 400 | Check the key and request parameters. |
| Google HTTP 403 | Check the reported reason: quota, API enablement, key restrictions, and access are different problems. |
| Google `quotaExceeded` / `dailyLimitExceeded` | Check your project's usage and current limits. Do not repeatedly retry a quota failure. |
| FlashData HTTP 401/403 | Check the key and account access. |
| FlashData HTTP 402 | Check available credits and billing in the console. |
| FlashData HTTP 429 | Check rate limits; wait before intentionally retrying. |
| FlashData timeout or connection error | Check job history before resubmitting a request that may have been accepted. |
| Empty transcript or partial dataset row | Check the requested language and automatic/manual caption choice. Some videos have no matching track. |
| Missing Google metadata IDs | The video may be unavailable or inaccessible. The example lists missing IDs explicitly. |
| Output already exists | Choose a fresh path, or use `--resume` for the dataset workflow. Bulk recovery requires a fresh export path. |
| Checkpoint options differ | Reuse the original query, limit, language, caption type, and demo mode. |
| Unknown request outcome | Inspect console history and preserve the checkpoint before deciding to submit new work. |
| A stale checkpoint lock remains | Confirm the old process stopped, then remove only its `.lock` file. |
| `No module named examples...` | Run from the cloned repository and install with `python -m pip install -e .`. |
| PowerShell activation is blocked | Use `.\.venv\Scripts\python.exe` instead of `python`; activation is optional. |

To inspect the arguments without making an API call:

```bash
python -m examples.search_to_dataset --help
python -m examples.bulk_export --help
```

The CLI error formatter omits API request URLs and response bodies, because Google error URLs can contain your API key. When reporting a bug, include your Python version, module name, sanitized command, status code, and reproducible steps. Do not paste API keys or signed URLs.
