from dataclasses import dataclass, field
from typing import Optional, List, Dict


# =========================
# Chunk Model
# (Internal — used between chunker, embedder, analyzer)
# =========================
@dataclass
class Chunk:
    text: str                          # raw text of the chunk
    source_name: str                   # e.g. "TechBurner" or "GSMArena"
    source_type: str                   # "youtube" or "article"
    url: str                           # article URL or YouTube deep link with timestamp
    chunk_id: str                      # unique ID e.g. "techburner_0", "gsmarena_3"

    # YouTube only fields (None for articles)
    video_id: Optional[str] = None
    timestamp: Optional[str] = None    # human readable e.g. "1:14"
    start_seconds: Optional[int] = None


# =========================
# Evidence Model
# A single exact quote supporting a feature score
# =========================
@dataclass
class Evidence:
    quote: str                         # exact words from the source, not paraphrased
    source_name: str                   # e.g. "TechBurner" or "GSMArena"
    source_type: str                   # "youtube" or "article"
    url: str                           # clickable deep link (with timestamp for youtube)
    timestamp: Optional[str] = None    # e.g. "1:14" — only for youtube


# =========================
# Feature Score Model
# Score + supporting evidence for one feature of one product
# =========================
@dataclass
class FeatureScore:
    score: float                       # out of 10
    summary: str                       # one line summary of this feature e.g. "Excellent camera for the price"
    evidence: List[Evidence] = field(default_factory=list)  # list of exact quotes


# =========================
# Product Analysis Model
# Full analysis of one product
# =========================
@dataclass
class ProductAnalysis:
    name: str                          # e.g. "Samsung Galaxy A55"
    price: Optional[int] = None        # e.g. 28000
    overall_score: Optional[float] = None
    verdict: Optional[str] = None      # one line overall verdict
    features: Dict[str, FeatureScore] = field(default_factory=dict)
    # features keys will be standardized: "camera", "battery", "display", "performance", "value_for_money"


# =========================
# Final Output Model
# Complete output of the analysis pipeline
# =========================
@dataclass
class FinalOutput:
    query: str                                          # original user query e.g. "best smartphone under 30000"
    products: List[ProductAnalysis] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Converts FinalOutput to a plain dict for JSON serialization
        and frontend consumption.
        """
        return {
            "query": self.query,
            "products": [
                {
                    "name": p.name,
                    "price": p.price,
                    "overall_score": p.overall_score,
                    "verdict": p.verdict,
                    "features": {
                        feature_name: {
                            "score": fs.score,
                            "summary": fs.summary,
                            "evidence": [
                                {
                                    "quote": e.quote,
                                    "source_name": e.source_name,
                                    "source_type": e.source_type,
                                    "url": e.url,
                                    "timestamp": e.timestamp
                                }
                                for e in fs.evidence
                            ]
                        }
                        for feature_name, fs in p.features.items()
                    }
                }
                for p in self.products
            ]
        }