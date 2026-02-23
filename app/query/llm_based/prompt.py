QUERY_PROMPT = """
You are a query understanding engine.

From the user query, extract:
- category (single word)
- budget (integer, null if not present)
- features (list of important user priorities)

Then generate 5 optimized and diverse search queries which should fetch the latest results relevant to the user intent.
Try to generate queires which says the current date for better freshness.
Also understand what the user is looking for so try to include that in the queries.

Return STRICT JSON only in this format:

{{
  "category": "...",
  "budget": ...,
  "features": [...],
  "queries": [...]
}}

No explanation. No text outside JSON.
User query: "{query}"
"""