
# =========================
# PROMPT 1 — FEATURE EXTRACTION
# Asks LLM to decide which features are relevant for this category
# Called once before analysis to get dynamic feature list
# =========================

FEATURE_EXTRACTION_PROMPT = """
You are a product research expert.

A user is searching for: "{user_query}"
Product category: "{category}"

Your job is to identify the most relevant features to evaluate for this product category.

Rules:
- Return 5 features that are most important for this specific product category
- Features should be specific and meaningful (e.g. "noise_cancellation" not just "sound")
- Use snake_case for feature keys (e.g. "sound_quality", "battery_life")
- Do NOT use generic features like "camera" or "display" for products where they don't apply
- Think about what a real buyer would care about most

Examples:
- Earphones/Headphones: sound_quality, bass, comfort, noise_cancellation, battery_life
- Smartphones: camera, battery, display, performance, value_for_money
- Laptops: performance, battery_life, display, build_quality, value_for_money
- TVs: display_quality, sound_quality, smart_features, value_for_money, build_quality
- Smartwatches: display, battery_life, fitness_tracking, design, value_for_money
- Cameras: image_quality, video_quality, autofocus, battery_life, value_for_money
- Tablets: display, performance, battery_life, portability, value_for_money

Return ONLY a JSON object with this format:
{{
  "features": ["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"],
  "feature_labels": {{
    "feature_1": "Human Readable Label",
    "feature_2": "Human Readable Label"
  }}
}}

No explanation. No text outside JSON.
"""


# =========================
# PROMPT 2 — DISCOVERY
# Finds all product names from chunks
# =========================

DISCOVERY_PROMPT = """
You are a product discovery engine analyzing review content.

Below is a collection of text chunks from reviews and articles.
Your ONLY job is to identify all product names mentioned.

Rules:
- Return ONLY a JSON array of canonical product names
- Normalize duplicates to their full canonical name
- Include full brand name always
- Only include products relevant to: "{user_query}"
- No explanation, no text outside JSON

Example output:
["Sony WF-1000XM5", "OnePlus Buds 3", "Samsung Galaxy Buds2 Pro"]

Content chunks:
{chunks_text}
"""


# =========================
# PROMPT 3 — PRODUCT ANALYSIS
# Deep feature analysis for ONE product with dynamic features
# =========================

ANALYSIS_PROMPT = """
You are a product expert analyst. Analyze the following content chunks about {product_name} and produce a detailed feature analysis.

IMPORTANT RULES FOR EVIDENCE:
- For each feature, copy the EXACT sentence or phrase from the source text as the quote
- Do NOT paraphrase or rewrite quotes — use the reviewer's exact words
- Only include a quote if it directly supports the score you gave
- If no strong evidence exists for a feature, give a lower score and fewer quotes

Features to analyze for this product category:
{features_list}

For each feature provide:
- score: float out of 10
- summary: one line summary of this feature for this product
- evidence: list of objects, each with:
    - quote: exact words from the source
    - source_name: name of the source
    - source_type: "youtube" or "article"
    - url: the URL provided in the chunk metadata
    - timestamp: timestamp string if youtube, null if article

Also provide:
- price: integer in the local currency if mentioned, null if not found
- overall_score: float out of 10 (weighted average based on category importance)
- verdict: one punchy sentence summarizing this product overall

Return STRICT JSON only. No explanation. No text outside JSON.

Format:
{{
  "name": "{product_name}",
  "price": <int or null>,
  "overall_score": <float>,
  "verdict": "<string>",
  "features": {{
    "feature_key": {{
      "score": <float>,
      "summary": "<string>",
      "evidence": [
        {{
          "quote": "<exact words from source>",
          "source_name": "<string>",
          "source_type": "<youtube or article>",
          "url": "<string>",
          "timestamp": "<string or null>"
        }}
      ]
    }}
  }}
}}

Content chunks about {product_name}:
{chunks_text}
"""


# =========================
# PROMPT 4 — FOLLOW UP TEXT
# For questions that don't match known features
# =========================

FOLLOWUP_PROMPT = """
You are a smart product advisor. A user has already received a list of recommended products and is asking a follow-up question.

User question: "{followup_query}"

Product data:
{context}

Answer the user's question concisely and helpfully. Reference specific products and scores. Be direct and specific.
"""
