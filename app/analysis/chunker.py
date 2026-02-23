from typing import List
from app.search.models import ArticleSource, VideoSource
from app.analysis.models import Chunk
import hashlib

class Chunker:
    """
    Splits ArticleSource and VideoSource content into
    overlapping chunks with full metadata attached.

    Chunk size: ~400 words
    Overlap: ~50 words (so no sentence is lost at boundaries)
    """

    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def chunk_all(
        self,
        articles: List[ArticleSource],
        videos: List[VideoSource]
    ) -> List[Chunk]:
        """
        Chunks all articles and videos and returns a combined flat list of Chunks.
        """
        all_chunks = []

        for article in articles:
            chunks = self._chunk_article(article)
            all_chunks.extend(chunks)
            print(f"[Chunker] Article '{article.title}' → {len(chunks)} chunks")

        for video in videos:
            chunks = self._chunk_video(video)
            all_chunks.extend(chunks)
            print(f"[Chunker] Video '{video.title}' → {len(chunks)} chunks")

        print(f"[Chunker] Total chunks: {len(all_chunks)}")
        return all_chunks

    # =========================
    # ARTICLE CHUNKING
    # =========================
    def _chunk_article(self, article: ArticleSource) -> List[Chunk]:
        """
        Splits article.content into overlapping word-based chunks.
        Each chunk gets the article URL as its deep link.
        """
        if not article.content:
            return []

        words = article.content.split()
        raw_chunks = self._split_into_windows(words)
        chunks = []

        for i, chunk_words in enumerate(raw_chunks):
            chunk_text = " ".join(chunk_words)
            url_hash = hashlib.md5(article.url.encode()).hexdigest()[:8]
            chunk_id = f"{url_hash}_{i}"

            chunk = Chunk(
                text=chunk_text,
                source_name=article.title,
                source_type="article",
                url=article.url,
                chunk_id=chunk_id,
                video_id=None,
                timestamp=None,
                start_seconds=None
            )
            chunks.append(chunk)

        return chunks

    # =========================
    # VIDEO CHUNKING
    # =========================
    def _chunk_video(self, video: VideoSource) -> List[Chunk]:
        """
        Splits video transcript into overlapping chunks.
        Uses transcript_segments to attach the correct timestamp
        to each chunk based on where in the video it starts.
        """
        if not video.transcript:
            return []

        # If we have segments with timestamps, use them
        # Otherwise fall back to plain text chunking
        if video.transcript_segments:
            return self._chunk_video_with_timestamps(video)
        else:
            return self._chunk_video_plain(video)

    def _chunk_video_with_timestamps(self, video: VideoSource) -> List[Chunk]:
        """
        Builds chunks from transcript_segments so each chunk
        knows exactly which timestamp it starts at.
        """
        segments = video.transcript_segments
        chunks = []
        i = 0
        chunk_index = 0

        while i < len(segments):
            # Accumulate segments until we hit chunk_size words
            chunk_segments = []
            word_count = 0

            j = i
            while j < len(segments) and word_count < self.chunk_size:
                chunk_segments.append(segments[j])
                word_count += len(segments[j]["text"].split())
                j += 1

            if not chunk_segments:
                break

            chunk_text = " ".join(seg["text"] for seg in chunk_segments)

            # Timestamp and URL come from the FIRST segment of this chunk
            first_seg = chunk_segments[0]
            start_seconds = first_seg["start"]
            timestamp = first_seg["timestamp"]
            deep_link = f"https://www.youtube.com/watch?v={video.video_id}&t={start_seconds}"

            chunk_id = f"{video.video_id}_{chunk_index}"

            chunk = Chunk(
                text=chunk_text,
                source_name=f"{video.channel} — {video.title}",
                source_type="youtube",
                url=deep_link,
                chunk_id=chunk_id,
                video_id=video.video_id,
                timestamp=timestamp,
                start_seconds=start_seconds
            )

            chunks.append(chunk)

            # Move back by overlap amount for next chunk
            # Calculate how many segments to backtrack for overlap
            overlap_words = 0
            backtrack = j - 1
            while backtrack > i and overlap_words < self.overlap:
                overlap_words += len(segments[backtrack]["text"].split())
                backtrack -= 1

            i = max(backtrack, i + 1)  # always advance at least 1 to avoid infinite loop
            chunk_index += 1

        return chunks

    def _chunk_video_plain(self, video: VideoSource) -> List[Chunk]:
        """
        Fallback: chunk plain transcript text without timestamps.
        Used when transcript_segments is empty.
        """
        words = video.transcript.split()
        raw_chunks = self._split_into_windows(words)
        chunks = []

        for i, chunk_words in enumerate(raw_chunks):
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{video.video_id}_{i}"

            chunk = Chunk(
                text=chunk_text,
                source_name=f"{video.channel} — {video.title}",
                source_type="youtube",
                url=video.url,
                chunk_id=chunk_id,
                video_id=video.video_id,
                timestamp=None,
                start_seconds=None
            )
            chunks.append(chunk)

        return chunks

    # =========================
    # HELPER — SLIDING WINDOW
    # =========================
    def _split_into_windows(self, words: List[str]) -> List[List[str]]:
        """
        Splits a word list into overlapping windows.
        Each window is chunk_size words, stepping by (chunk_size - overlap).
        """
        step = self.chunk_size - self.overlap
        windows = []

        start = 0
        while start < len(words):
            window = words[start: start + self.chunk_size]
            windows.append(window)
            start += step

        return windows