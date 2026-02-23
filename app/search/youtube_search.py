from typing import List, Optional, Dict

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from app.config.settings import YOUTUBE_API_KEY
from app.search.models import VideoSource


class YouTubeSearcher:
    """
    Handles YouTube video search using YouTube Data API v3.
    """

    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def search(self, queries: List[str], max_results: int = 5) -> List[VideoSource]:
        all_videos = []

        for query in queries:
            videos = self._search_single_query(query, max_results)
            all_videos.extend(videos)

        return all_videos

    def _search_single_query(self, query: str, max_results: int) -> List[VideoSource]:

        request = self.youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            regionCode="IN",
            relevanceLanguage="en"
        )

        response = request.execute()

        videos = []

        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]

            video = VideoSource(
                video_id=video_id,
                title=title,
                channel=channel,
                url=f"https://www.youtube.com/watch?v={video_id}"
            )

            videos.append(video)

        return videos


class TranscriptFetcher:
    """
    Fetches transcript for YouTube videos.
    Stores both plain full text and timestamped segments.
    Skips videos without transcript.
    """

    def __init__(self):
        self.ytt_api = YouTubeTranscriptApi()

    def fetch(self, videos: List[VideoSource]) -> List[VideoSource]:

        updated_videos = []

        for video in videos:
            result = self._get_transcript(video.video_id, video.url)

            if result:
                video.transcript = result["full_text"]
                video.transcript_segments = result["segments"]
                updated_videos.append(video)

        return updated_videos

    def _get_transcript(self, video_id: str, video_url: str) -> Optional[Dict]:
        """
        Returns a dict with:
          - full_text: plain joined transcript string (same as before)
          - segments: list of dicts with text, start, timestamp, url
        Returns None if transcript unavailable or too short.
        """
        try:
            fetched_transcript = self.ytt_api.fetch(
                video_id,
                languages=[
                    'en', 'en-IN', 'en-US',
                    'hi', 'bn', 'te', 'mr', 'ta',
                    'ur', 'gu', 'kn', 'ml', 'pa', 'or', 'as'
                ]
            )

            segments = []
            full_text_parts = []

            for snippet in fetched_transcript:
                text = snippet.text.strip()

                if not text:
                    continue

                start_seconds = int(snippet.start)                    # e.g. 74
                timestamp = self._seconds_to_timestamp(start_seconds) # e.g. "1:14"
                deep_link = f"{video_url}&t={start_seconds}"          # e.g. "https://youtube.com/watch?v=XYZ&t=74"

                segments.append({
                    "text": text,
                    "start": start_seconds,
                    "timestamp": timestamp,
                    "url": deep_link
                })

                full_text_parts.append(text)

            full_text = " ".join(full_text_parts)

            # Skip extremely small transcripts (like music / junk)
            if len(full_text) < 200:
                return None

            return {
                "full_text": full_text,
                "segments": segments
            }

        except Exception as e:
            print(f"[Transcript Error] {video_id}: {e}")
            return None

    @staticmethod
    def _seconds_to_timestamp(seconds: int) -> str:
        """
        Converts seconds to human readable timestamp.
        Examples:
          74  → "1:14"
          3661 → "1:01:01"
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"