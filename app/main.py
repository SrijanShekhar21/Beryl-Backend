from app.query.llm_based.llm_engine import LLMQueryEngine
from app.search.orchestrator import SearchOrchestrator
from app.scraper.article_scraper import ArticleScraper
from app.analysis.orchestrator import AnalysisOrchestrator


def main():

    # =========================
    # STEP 1 — Understand the user query
    # LLM extracts intent + generates 5 optimized search queries
    # =========================
    user_query = input("What are you looking for? → ").strip()

    print("\n[Main] Understanding query...")
    query_engine = LLMQueryEngine()
    intent, search_queries = query_engine.run(user_query)

    print(f"\n[Main] Intent: category={intent.category}, budget={intent.budget}, features={intent.features}")
    print(f"[Main] Generated {len(search_queries)} search queries:")
    for q in search_queries:
        print(f"  → {q}")

    # =========================
    # STEP 2 — Search Google + YouTube, fetch transcripts
    # =========================
    print("\n[Main] Running search...")
    search_orchestrator = SearchOrchestrator()
    articles, videos = search_orchestrator.run(search_queries)

    print(f"\n[Main] Got {len(articles)} articles and {len(videos)} videos with transcripts")

    # =========================
    # STEP 3 — Scrape article content
    # =========================
    print("\n[Main] Scraping articles...")
    scraper = ArticleScraper()
    articles = scraper.scrape(articles)

    print(f"[Main] Successfully scraped {len(articles)} articles")

    # =========================
    # STEP 4 — Analysis pipeline
    # Chunk → Embed → Discover products → Analyze per product
    # =========================
    print("\n[Main] Starting analysis pipeline...")
    analysis_orchestrator = AnalysisOrchestrator()
    final_output = analysis_orchestrator.run(
        user_query=user_query,
        articles=articles,
        videos=videos
    )

    # =========================
    # STEP 5 — Show initial results
    # =========================
    print("\n========== RESULTS ==========\n")
    for product in final_output.products:
        print(f"📱 {product.name}")
        print(f"   Price: ₹{product.price or 'N/A'}")
        print(f"   Overall Score: {product.overall_score}/10")
        print(f"   Verdict: {product.verdict}")
        print()

    # =========================
    # STEP 6 — Follow-up loop
    # User can ask follow-up questions about the results
    # without triggering a new search
    # =========================
    print("\n[Main] You can now ask follow-up questions about these phones.")
    print("[Main] Type 'exit' to quit.\n")

    while True:
        followup = input("Your question → ").strip()

        if followup.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        if not followup:
            continue

        print("\n[Main] Processing follow-up...\n")
        answer = analysis_orchestrator.handle_followup(followup)
        print(f"\n{answer}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()