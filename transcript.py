"""유튜브 영상에서 콘티 재료(자막 또는 제목+댓글)를 뽑아온다."""

import os
import re

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"유튜브 링크에서 video_id를 못 찾았어요: {url}")


def fetch_transcript(video_id: str) -> str | None:
    """자막(자동 생성 포함)을 시도. 없으면 None."""
    try:
        api = YouTubeTranscriptApi()
        segments = api.fetch(video_id, languages=["ko", "en"])
        return " ".join(s.text for s in segments)
    except Exception:
        return None


def fetch_title_and_comments(video_id: str, max_comments: int = 10) -> tuple[str, list[str]]:
    """자막이 없을 때 대체용: 제목 + 상위 댓글."""
    youtube = build("youtube", "v3", developerKey=os.environ["YOUTUBE_API_KEY"])

    video_resp = youtube.videos().list(id=video_id, part="snippet").execute()
    items = video_resp.get("items", [])
    title = items[0]["snippet"]["title"] if items else "(제목을 못 가져왔어요)"

    comments = []
    try:
        resp = youtube.commentThreads().list(
            videoId=video_id,
            part="snippet",
            order="relevance",
            maxResults=max_comments,
            textFormat="plainText",
        ).execute()
        for item in resp.get("items", []):
            comments.append(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
    except Exception:
        pass

    return title, comments


def get_source_material(url: str) -> dict:
    """콘티 생성에 쓸 원재료를 모은다. 자막 우선, 없으면 제목+댓글로 대체."""
    video_id = extract_video_id(url)
    title, comments = fetch_title_and_comments(video_id)
    transcript = fetch_transcript(video_id)

    return {
        "video_id": video_id,
        "title": title,
        "transcript": transcript,
        "comments": comments,
        "used_fallback": transcript is None,
    }
