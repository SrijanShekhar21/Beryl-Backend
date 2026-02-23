import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.search.models import ArticleSource, VideoSource
from app.analysis.chunker import Chunker

# Fake article
article = ArticleSource(
    title="Best phones under 30000",
    url="https://gsmarena.com/test",
    domain="gsmarena.com",
    content="Samsung Galaxy A55 is a great phone. " * 200  # fake long content
)

# Fake video with segments
video = VideoSource(
    video_id="TEST123",
    title="Top 5 phones under 30k",
    channel="TechBurner",
    url="https://youtube.com/watch?v=TEST123",
    transcript="the camera is great " * 200,
    transcript_segments=[
        {"text": "the camera is great on this phone", "start": 10, "timestamp": "0:10", "url": "https://youtube.com/watch?v=TEST123&t=10"},
        {"text": "samsung galaxy a55 is the best", "start": 20, "timestamp": "0:20", "url": "https://youtube.com/watch?v=TEST123&t=20"},
    ] * 50
)

chunker = Chunker()
chunks = chunker.chunk_all([article], [video])

print(f"Total chunks: {len(chunks)}")
print(f"\nFirst article chunk:")
print(f"  text[:100]: {chunks[0].text[:100]}")
print(f"  source_type: {chunks[0].source_type}")
print(f"  url: {chunks[0].url}")

# Find first youtube chunk
yt_chunks = [c for c in chunks if c.source_type == "youtube"]
print(f"\nFirst youtube chunk:")
print(f"  text[:100]: {yt_chunks[0].text[:100]}")
print(f"  timestamp: {yt_chunks[0].timestamp}")
print(f"  url: {yt_chunks[0].url}")