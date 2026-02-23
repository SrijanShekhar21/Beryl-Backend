from typing import List
from urllib.parse import urlparse, urlunparse

from app.search.models import ArticleSource, VideoSource


class SearchFilter:
    """
    Handles deduplication and basic filtering of search results.
    """

    # =========================
    # ARTICLE DEDUPLICATION
    # =========================
    @staticmethod
    def dedup_articles(articles: List[ArticleSource]) -> List[ArticleSource]:
        """
        Removes duplicate articles based on normalized URL.
        """
        seen_urls = set()
        unique_articles = []

        for article in articles:
            normalized_url = SearchFilter._normalize_url(article.url)

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                article.url = normalized_url  # store clean version
                unique_articles.append(article)

        return unique_articles

    # =========================
    # VIDEO DEDUPLICATION
    # =========================
    @staticmethod
    def dedup_videos(videos: List[VideoSource]) -> List[VideoSource]:
        """
        Removes duplicate videos based on video_id.
        """
        seen_ids = set()
        unique_videos = []

        for video in videos:
            if video.video_id not in seen_ids:
                seen_ids.add(video.video_id)
                unique_videos.append(video)

        return unique_videos

    # =========================
    # URL NORMALIZATION
    # =========================
    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Removes query parameters and fragments from URL.
        Example:
        https://site.com/page?ref=abc&utm=123 → https://site.com/page
        """
        parsed = urlparse(url)

        # Remove query and fragment
        cleaned = parsed._replace(query="", fragment="")

        return urlunparse(cleaned)