from typing import List, Tuple

from app.search.google_search import GoogleSearcher
from app.search.youtube_search import YouTubeSearcher, TranscriptFetcher
from app.search.filters import SearchFilter
from app.search.models import ArticleSource, VideoSource


class SearchOrchestrator:
    """
    Coordinates Google search, YouTube search,
    deduplication, and transcript fetching.
    """

    def __init__(self):
        self.google_searcher = GoogleSearcher()
        self.youtube_searcher = YouTubeSearcher()
        self.transcript_fetcher = TranscriptFetcher()

    def run(self, queries: List[str]) -> Tuple[List[ArticleSource], List[VideoSource]]:

        print("\n===== STARTING SEARCH ORCHESTRATION =====\n")

        # ----------------------------------
        # STEP 1 — GOOGLE SEARCH
        # ----------------------------------
        print("Running Google Search...")
        articles = self.google_searcher.search(queries)
        print(f"Google returned {len(articles)} raw articles")

        # ----------------------------------
        # STEP 2 — ARTICLE DEDUP
        # ----------------------------------
        articles = SearchFilter.dedup_articles(articles)
        print(f"After deduplication: {len(articles)} unique articles")

        # ----------------------------------
        # STEP 3 — YOUTUBE SEARCH
        # ----------------------------------
        # print("\nRunning YouTube Search...")
        # videos = self.youtube_searcher.search(queries)
        # print(f"YouTube returned {len(videos)} raw videos")

        videos = []
        print("YouTube search skipped for now.")
        
        # ----------------------------------
        # STEP 4 — VIDEO DEDUP
        # ----------------------------------
        videos = SearchFilter.dedup_videos(videos)
        print(f"After deduplication: {len(videos)} unique videos")

        # ----------------------------------
        # STEP 5 — TRANSCRIPT FETCH
        # ----------------------------------
        print("\nFetching transcripts...")
        videos = self.transcript_fetcher.fetch(videos)
        print(f"Videos with transcript: {len(videos)}")

        print("\n===== SEARCH ORCHESTRATION COMPLETE =====\n")

        return articles, videos