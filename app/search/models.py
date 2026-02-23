from dataclasses import dataclass, field
from typing import Optional, List, Dict


# =========================
# Article Source Model
# =========================
@dataclass
class ArticleSource:
    title: str
    url: str
    domain: str
    snippet: Optional[str] = None
    source_type: str = "article"
    content: Optional[str] = None


# =========================
# YouTube Video Source Model
# =========================
@dataclass
class VideoSource:
    video_id: str
    title: str
    channel: str
    url: str
    transcript: Optional[str] = None          # plain full text (existing, unchanged)
    transcript_segments: List[Dict] = field(default_factory=list)  # NEW: timestamped segments
    source_type: str = "youtube"

    # Each segment in transcript_segments looks like:
    # {
    #     "text": "the camera on this phone is genuinely shocking for the price",
    #     "start": 74.3,         # seconds from video start
    #     "timestamp": "1:14",   # human readable
    #     "url": "https://www.youtube.com/watch?v=VIDEO_ID&t=74"  # deep link
    # }