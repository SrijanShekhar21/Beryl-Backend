from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.models import (
    SearchRequest, FollowupRequest,
    FollowupResponse, HealthResponse
)
from app.api.session import session_store
from app.api.streaming import progress_stream
from app.query.llm_based.llm_engine import LLMQueryEngine
from app.search.orchestrator import SearchOrchestrator
from app.scraper.article_scraper import ArticleScraper


app = FastAPI(
    title="Beryl API",
    description="Beryl — Smart Decision Optimization Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://beryl-frontend-tau.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

query_engine = LLMQueryEngine()
search_orchestrator = SearchOrchestrator()
scraper = ArticleScraper()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        message=f"Beryl running. Active sessions: {session_store.active_sessions()}"
    )


@app.post("/search")
async def search(request: SearchRequest):
    print(f"\n[API] Search: {request.query}")

    # Step 1 — Understand query (extracts category + generates search queries)
    intent, search_queries = query_engine.run(request.query)
    category = intent.category or "product"
    print(f"[API] Category: {category} | Queries: {search_queries}")

    # Step 2 — Search + scrape
    articles, videos = search_orchestrator.run(search_queries)
    articles = scraper.scrape(articles)

    # Step 3 — Create session
    session_id, orchestrator = session_store.create_session()

    # Step 4 — Stream analysis with category passed through
    return StreamingResponse(
        progress_stream(
            session_id=session_id,
            query=request.query,
            category=category,          # ← passed dynamically from intent
            articles=articles,
            videos=videos,
            orchestrator=orchestrator
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/followup", response_model=FollowupResponse)
async def followup(request: FollowupRequest):
    print(f"\n[API] Follow-up: {request.session_id} | {request.query}")

    orchestrator = session_store.get_session(request.session_id)

    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please run a new search first."
        )

    if not orchestrator.final_output:
        raise HTTPException(
            status_code=400,
            detail="No analysis results found for this session."
        )

    result = orchestrator.handle_followup(request.query)

    return FollowupResponse(
        session_id=request.session_id,
        query=request.query,
        response_type=result["response_type"],
        answer=result.get("answer"),
        products=result.get("products"),
        intro=result.get("intro")
    )


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    session_store.delete_session(session_id)
    return {"status": "ok", "message": f"Session {session_id} deleted"}
