# Contributing

Keep examples small, runnable, and Python-only. A useful addition solves a concrete YouTube data task and documents its provider, credentials, output, and request limits.

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
python -m examples.search_to_dataset --demo --output output/contributor-demo.jsonl
```

For a new example:

1. Add an importable module under `examples/` with `argparse` and a `--help` command that needs no credentials.
2. Reuse the provider's maintained client instead of adding another HTTP SDK.
3. Document the command in the README and make any live request costs clear.
4. Preserve partial results and bound pagination or job polling.
5. Add tests with fixtures or mocked transports. CI must not use real API keys or paid API calls.

Report issues at [GitHub Issues](https://github.com/flashdatadev/youtube-data-api/issues). Include the Python version and sanitized steps to reproduce. Contact [support@flashdata.dev](mailto:support@flashdata.dev) for account-specific questions.
