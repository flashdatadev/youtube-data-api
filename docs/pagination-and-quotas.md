# Pagination and quotas

## Search results are pages, not a complete inventory

Google's `search.list` returns up to 50 results per page. The search example uses `type="video"`, takes each `id.videoId`, deduplicates IDs, and follows `nextPageToken` within an explicit page budget.

```bash
python -m examples.google_search "python tutorial" --limit 75 --output output/search.json
```

This allows up to two requests. `--limit` is an upper bound, not a promise of that many results. Duplicate items, an exhausted page token, or fewer available matches can produce fewer rows. The example caps the budget even when a page is empty, preventing an unbounded loop.

For video duration and statistics, use `videos.list`. The metadata example deduplicates input IDs and requests at most 50 IDs per call. IDs missing from the response appear in `missing_video_ids`; they are not silently treated as successful lookups.

## Channel uploads

1. Run `python -m examples.google_channel --handle @GoogleDevelopers`.
2. Read `items[0].contentDetails.relatedPlaylists.uploads` from the response.
3. Run `python -m examples.google_playlist YOUR_UPLOADS_PLAYLIST_ID --limit 100`.

The playlist example preserves the returned items and follows `nextPageToken` within the requested limit. Its default is 50 items, and its maximum is 5,000 per invocation. For larger collections, adapt the example to persist page tokens and output incrementally.

## Quota and retry behavior

Read current usage and limits in your Google Cloud project. Different methods have different quota rules; do not estimate usage solely from HTTP request count. These examples deliberately avoid automatic request retries. After an error, inspect its cause before starting another run.

FlashData's basic search example accepts 1–20 results. It is not an implementation of Google's page-token API. The dataset workflow performs one search and at most two subsequent requests per unique selected ID. Large existing lists should use the bulk example.

References:

- [Google search.list](https://developers.google.com/youtube/data/reference/rest/v3/search/list)
- [Google videos.list](https://developers.google.com/youtube/data/reference/rest/v3/videos/list)
- [Google playlistItems.list](https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list)
- [Google quota guidance](https://developers.google.com/youtube/v3/determine_quota_cost)
- [FlashData YouTube search](https://flashdata.dev/docs/sources/youtube_search)
