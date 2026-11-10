# Authentication

## Google YouTube Data API v3

1. Open [Google Cloud Console](https://console.cloud.google.com/) and choose or create a project.
2. Enable **YouTube Data API v3** in **APIs & Services → Library**.
3. Create an API key in **APIs & Services → Credentials**.
4. Restrict the key to YouTube Data API v3 and use application restrictions appropriate for where your script runs.
5. Set `YOUTUBE_API_KEY` in your terminal, then run `python -m examples.google_search "python tutorial" --limit 3`.

The Google examples in this repository read public resources. They do not implement OAuth or operations on a signed-in user's private data. Browser-referrer-restricted keys may not work in a server-side Python script. Check the API error and your key restrictions if a request is rejected.

Official references: [getting started](https://developers.google.com/youtube/v3/getting-started), [authentication](https://developers.google.com/youtube/v3/guides/authentication).

## FlashData

1. Create or sign in to your account at [flashdata.dev](https://flashdata.dev/).
2. Obtain an API key from the console and check your available credits.
3. Set `FLASHDATA_API_KEY` in your terminal.
4. Run `python -m examples.flashdata_search "python tutorial" --limit 3`.

The examples use the official FlashData Python SDK and its default service endpoints. A Google API key does not authenticate FlashData requests, and a FlashData key does not authenticate Google requests.

## Set an environment variable

macOS / Linux:

```bash
export YOUTUBE_API_KEY="your-google-api-key"
export FLASHDATA_API_KEY="your-flashdata-api-key"
```

Windows PowerShell:

```powershell
$env:YOUTUBE_API_KEY = "your-google-api-key"
$env:FLASHDATA_API_KEY = "your-flashdata-api-key"
```

Set only the key required for your chosen provider. Environment changes apply to the current shell and its child processes. Examples do not automatically load `.env` files. Keep real keys out of source code and version control.
