import json
import asyncio
from typing import AsyncGenerator


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def progress_stream(
    session_id: str,
    query: str,
    category: str,
    articles,
    videos,
    orchestrator
) -> AsyncGenerator[str, None]:
    """
    Runs the full analysis pipeline while streaming progress
    events to the frontend via SSE.
    """

    try:
        # --- Chunking ---
        yield format_sse("progress", {
            "message": f"Processing {len(articles)} articles and {len(videos)} videos..."
        })
        await asyncio.sleep(0)

        loop = asyncio.get_event_loop()
        all_chunks = await loop.run_in_executor(
            None,
            orchestrator.chunker.chunk_all,
            articles,
            videos
        )

        yield format_sse("progress", {
            "message": f"Created {len(all_chunks)} content chunks. Building search index..."
        })
        await asyncio.sleep(0)

        # --- Embed ---
        await loop.run_in_executor(
            None,
            orchestrator.embedder.index,
            all_chunks
        )

        yield format_sse("progress", {
            "message": f"Identifying relevant features for {category}..."
        })
        await asyncio.sleep(0)

        # --- Extract features dynamically ---
        features, labels = await loop.run_in_executor(
            None,
            orchestrator.analyzer._extract_features,
            query,
            category
        )
        orchestrator.analyzer.features = features
        orchestrator.analyzer.feature_labels = labels

        yield format_sse("progress", {
            "message": f"Features identified: {', '.join(labels.values())}. Discovering products..."
        })
        await asyncio.sleep(0)

        # --- Discovery ---
        product_names = await loop.run_in_executor(
            None,
            orchestrator.analyzer._discover_products,
            query
        )

        if not product_names:
            yield format_sse("error", {
                "message": "Could not find any products in the search results. Try a different query."
            })
            return

        yield format_sse("products_found", {
            "message": f"Found {len(product_names)} products: {', '.join(product_names)}",
            "products": product_names
        })
        await asyncio.sleep(0)

        # --- Per product analysis ---
        from app.analysis.models import FinalOutput
        final_output = FinalOutput(query=query)

        for product_name in product_names:
            yield format_sse("analyzing", {
                "message": f"Analyzing {product_name}..."
            })
            await asyncio.sleep(0)

            product_analysis = await loop.run_in_executor(
                None,
                orchestrator.analyzer._analyze_product,
                product_name
            )

            if product_analysis:
                final_output.products.append(product_analysis)

        # Filter zero scores and sort
        final_output.products = [
            p for p in final_output.products
            if p.overall_score and p.overall_score > 0
        ]
        final_output.products.sort(
            key=lambda p: p.overall_score or 0,
            reverse=True
        )

        # Store in orchestrator for follow-ups
        orchestrator.final_output = final_output
        orchestrator.category = category

        yield format_sse("done", {
            "session_id": session_id,
            "query": query,
            "products": final_output.to_dict()["products"]
        })

    except Exception as e:
        print(f"[Streaming] Error: {e}")
        yield format_sse("error", {
            "message": f"Something went wrong: {str(e)}"
        })
