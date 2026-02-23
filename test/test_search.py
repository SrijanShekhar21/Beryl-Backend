import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.query.llm_based.llm_engine import LLMQueryEngine
from app.search.orchestrator import SearchOrchestrator

user_query = input("What are you looking for? → ").strip()

query_engine = LLMQueryEngine()
intent, search_queries = query_engine.run(user_query)

print("Intent:", intent)
print("Queries:", search_queries)

orchestrator = SearchOrchestrator()
articles, videos = orchestrator.run(search_queries)

print(f"\nArticles: {len(articles)}")
for a in articles:
    print(f"  → {a.title} | {a.url}")

print(f"\nVideos with transcripts: {len(videos)}")
for v in videos:
    print(f"  → {v.title} | segments: {len(v.transcript_segments)}")
    if v.transcript_segments:
        print(f"     First segment: {v.transcript_segments[0]}")