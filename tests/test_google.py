from unittest.mock import MagicMock

from examples.google_playlist import playlist_videos
from examples.google_search import search_videos
from examples.google_video_metadata import video_metadata


def test_search_follows_tokens_deduplicates_and_bounds_requests():
    youtube = MagicMock()
    resource = youtube.search.return_value
    first = [{"id": {"videoId": f"video{i:06d}"}} for i in range(50)]
    resource.list.return_value.execute.side_effect = [
        {"items": first, "nextPageToken": "page-2"},
        {"items": [first[0], {"id": {"videoId": "video000050"}}], "nextPageToken": "page-3"},
    ]
    rows = search_videos(youtube, "python", 52)
    assert len(rows) == 51
    assert resource.list.call_count == 2
    assert resource.list.call_args.kwargs["pageToken"] == "page-2"
    assert resource.list.call_args.kwargs["maxResults"] == 2
    assert resource.list.call_args_list[0].kwargs["type"] == "video"
    resource.list.return_value.execute.assert_called_with(num_retries=0)


def test_search_stops_when_no_next_page():
    youtube = MagicMock()
    youtube.search.return_value.list.return_value.execute.return_value = {"items": []}
    assert search_videos(youtube, "nothing", 100) == []
    assert youtube.search.return_value.list.call_count == 1


def test_metadata_batches_50_ids_and_reports_missing_ids():
    youtube = MagicMock()
    ids = [f"video{i:06d}" for i in range(51)]
    youtube.videos.return_value.list.return_value.execute.side_effect = [
        {"items": [{"id": identifier} for identifier in ids[:49]]},
        {"items": [{"id": ids[50]}]},
    ]
    response = video_metadata(youtube, ids + [ids[0]])
    assert response["missing_video_ids"] == [ids[49]]
    assert len(response["items"]) == 50
    calls = youtube.videos.return_value.list.call_args_list
    assert len(calls) == 2
    assert len(calls[0].kwargs["id"].split(",")) == 50
    assert calls[1].kwargs["id"] == ids[50]


def test_playlist_follows_token_and_stops_at_limit():
    youtube = MagicMock()
    resource = youtube.playlistItems.return_value
    resource.list.return_value.execute.side_effect = [
        {"items": [{"id": str(i)} for i in range(50)], "nextPageToken": "second"},
        {"items": [{"id": "last"}], "nextPageToken": "unused"},
    ]
    assert len(playlist_videos(youtube, "PLexample", 51)) == 51
    assert resource.list.call_count == 2
    assert resource.list.call_args.kwargs["pageToken"] == "second"
    assert resource.list.call_args.kwargs["maxResults"] == 1
