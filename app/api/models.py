from pydantic import BaseModel
from typing import Optional, List, Dict


# =========================
# REQUEST MODELS
# =========================

class SearchRequest(BaseModel):
    query: str

class FollowupRequest(BaseModel):
    session_id: str
    query: str


# =========================
# RESPONSE MODELS
# =========================

class EvidenceResponse(BaseModel):
    quote: str
    source_name: str
    source_type: str
    url: str
    timestamp: Optional[str] = None


class FeatureScoreResponse(BaseModel):
    score: float
    summary: str
    evidence: List[EvidenceResponse]


class ProductResponse(BaseModel):
    name: str
    price: Optional[int] = None
    overall_score: Optional[float] = None
    verdict: Optional[str] = None
    features: Dict[str, FeatureScoreResponse]


class SearchResponse(BaseModel):
    session_id: str
    query: str
    products: List[ProductResponse]


class FollowupResponse(BaseModel):
    session_id: str
    query: str
    response_type: str          # "products" or "text"
    answer: Optional[str] = None                    # for text responses
    products: Optional[List[ProductResponse]] = None  # for product responses
    intro: Optional[str] = None                     # intro text shown above product cards


class HealthResponse(BaseModel):
    status: str
    message: str
