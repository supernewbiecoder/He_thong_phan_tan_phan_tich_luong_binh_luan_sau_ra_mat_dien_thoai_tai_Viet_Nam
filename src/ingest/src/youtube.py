import logging
import random
import time
import requests
from .quota import QuotaExceeded


log = logging.getLogger("youtube")


class CommentsDisabled(Exception):
    pass


class YouTubeError(Exception):
    """Lỗi từ phía YouTube/mạng, không phải lỗi hạn mức."""


class TransientError(YouTubeError):
    """Lỗi tạm thời (mạng, 429, 5xx) vẫn còn sau khi đã thử lại nhiều lần."""


class ApiError(YouTubeError):
    """API trả lỗi không thể thử lại (ví dụ playlistNotFound, forbidden)."""


class YouTube:
    BASE = "https://www.googleapis.com/youtube/v3"
    RETRIES = 5

    def __init__(self, api_key, ledger):
        if not api_key:
            raise SystemExit("Thiếu YOUTUBE_API_KEY trong file .env")
        self.key, self.ledger, self.s = api_key, ledger, requests.Session()

    @staticmethod
    def _reason(r):
        try:
            return r.json()["error"]["errors"][0]["reason"]
        except Exception:
            return ""

    def _call(self, method, endpoint, **params):
        self.ledger.charge(method)
        params["key"] = self.key
        last = ""
        for attempt in range(self.RETRIES):
            wait = min(60, 3 * 2 ** attempt) + random.random()
            try:
                r = self.s.get(f"{self.BASE}/{endpoint}", params=params, timeout=(10, 30))
            except requests.RequestException as e:
                last = f"lỗi mạng {type(e).__name__}: {str(e)[:150]}"
                log.warning("%s lần %d/%d: %s", endpoint, attempt + 1, self.RETRIES, last)
                time.sleep(wait)
                continue
            if r.status_code == 200:
                time.sleep(0.1)
                return r.json()
            reason = self._reason(r)
            if r.status_code == 403 and reason in ("quotaExceeded", "dailyLimitExceeded"):
                self.ledger.mark_exhausted()
                raise QuotaExceeded(reason)
            if reason in ("commentsDisabled", "videoNotFound"):
                raise CommentsDisabled(reason)
            if r.status_code in (429, 500, 502, 503, 504) or reason in ("rateLimitExceeded", "userRateLimitExceeded"):
                last = f"HTTP {r.status_code} {reason}"
                log.warning("%s lần %d/%d: %s", endpoint, attempt + 1, self.RETRIES, last)
                time.sleep(wait)
                continue
            raise ApiError(f"{endpoint}: HTTP {r.status_code} {reason}: {r.text[:300]}")
        raise TransientError(f"{endpoint}: thất bại sau {self.RETRIES} lần thử, lỗi cuối: {last}")

    def channel(self, handle=None, channel_id=None):
        p = {"part": "snippet,contentDetails"}
        p.update({"forHandle": handle} if handle else {"id": channel_id})
        items = self._call("channels.list", "channels", **p).get("items", [])
        return items[0] if items else None

    def uploads(self, playlist_id):
        token = None
        while True:
            d = self._call("playlistItems.list", "playlistItems", part="snippet,contentDetails",
                           playlistId=playlist_id, maxResults=50, pageToken=token)
            yield from d.get("items", [])
            token = d.get("nextPageToken")
            if not token:
                return

    def videos(self, ids):
        return self._call("videos.list", "videos", part="snippet,statistics", id=",".join(ids)).get("items", [])

    def comment_threads(self, video_id, token=None):
        # textFormat=plainText: API key không đọc được textOriginal, dùng textDisplay dạng thuần
        return self._call("commentThreads.list", "commentThreads", part="snippet,replies",
                          videoId=video_id, maxResults=100, order="time",
                          textFormat="plainText", pageToken=token)

    def all_replies(self, parent_id):
        out, token = [], None
        while True:
            d = self._call("comments.list", "comments", part="snippet", parentId=parent_id,
                           maxResults=100, textFormat="plainText", pageToken=token)
            out += d.get("items", [])
            token = d.get("nextPageToken")
            if not token:
                return out

    def search_videos(self, **params):
        return self._call("search.list", "search", part="snippet", type="video", maxResults=50, **params)

    def search_channels(self, name):
        return self._call("search.list", "search", part="snippet", type="channel", q=name,
                          regionCode="VN", relevanceLanguage="vi", maxResults=3)

    def channels_info(self, ids):
        return self._call("channels.list", "channels", part="snippet,statistics",
                          id=",".join(ids)).get("items", [])
