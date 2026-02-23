import json
import time
from typing import List, Optional, Dict
from openai import OpenAI

from app.config.settings import OPENAI_API_KEY
from app.analysis.models import Chunk, Evidence, FeatureScore, ProductAnalysis, FinalOutput
from app.analysis.prompts import FEATURE_EXTRACTION_PROMPT, DISCOVERY_PROMPT, ANALYSIS_PROMPT
from app.analysis.embedder import Embedder


client = OpenAI(api_key=OPENAI_API_KEY)

DISCOVERY_MODEL = "gpt-4o-mini"
ANALYSIS_MODEL = "gpt-4o-mini"
FEATURE_MODEL = "gpt-4o-mini"


class Analyzer:
    """
    Runs three-stage LLM analysis:
    Stage 0 — Feature Extraction: dynamically determines relevant features for this category
    Stage 1 — Discovery: finds all product names
    Stage 2 — Per-Product Analysis: deep feature analysis with exact quotes
    """

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.features: List[str] = []
        self.feature_labels: Dict[str, str] = {}

    # =========================
    # MAIN ENTRY POINT
    # =========================
    def analyze(self, user_query: str, category: str = "product") -> FinalOutput:
        print("\n===== STARTING ANALYSIS =====\n")

        # Stage 0 — Extract relevant features for this category dynamically
        self.features, self.feature_labels = self._extract_features(user_query, category)
        print(f"[Analyzer] Features for '{category}': {self.features}")

        # Stage 1 — Discover products
        product_names = self._discover_products(user_query)

        if not product_names:
            print("[Analyzer] No products discovered.")
            return FinalOutput(query=user_query)

        print(f"[Analyzer] Discovered {len(product_names)} products: {product_names}")

        # Stage 2 — Analyze each product
        final_output = FinalOutput(query=user_query)

        for product_name in product_names:
            print(f"\n[Analyzer] Analyzing: {product_name}")
            product_analysis = self._analyze_product(product_name)

            if product_analysis:
                final_output.products.append(product_analysis)

            time.sleep(2)   # avoid rate limits

        # Filter out zero-score products
        final_output.products = [
            p for p in final_output.products
            if p.overall_score and p.overall_score > 0
        ]

        # Sort by overall score descending
        final_output.products.sort(
            key=lambda p: p.overall_score or 0,
            reverse=True
        )

        print(f"\n===== ANALYSIS COMPLETE — {len(final_output.products)} products =====\n")
        return final_output

    # =========================
    # STAGE 0 — DYNAMIC FEATURE EXTRACTION
    # =========================
    def _extract_features(
        self,
        user_query: str,
        category: str
    ) -> tuple[List[str], Dict[str, str]]:
        """
        Asks LLM to decide which features are relevant for this product category.
        Returns (feature_keys, feature_labels) where:
          feature_keys = ["sound_quality", "bass", ...]
          feature_labels = {"sound_quality": "Sound Quality", "bass": "Bass"}
        """
        prompt = FEATURE_EXTRACTION_PROMPT.format(
            user_query=user_query,
            category=category
        )

        try:
            response = client.chat.completions.create(
                model=FEATURE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            text = response.choices[0].message.content.strip()
            text = self._clean_json(text)
            data = json.loads(text)

            features = data.get("features", [])
            labels = data.get("feature_labels", {})

            # Fill in any missing labels automatically
            for f in features:
                if f not in labels:
                    labels[f] = f.replace("_", " ").title()

            return features, labels

        except Exception as e:
            print(f"[Analyzer] Feature extraction failed: {e}")
            # Generic fallback — still not hardcoded, just safe defaults
            fallback = ["quality", "performance", "battery_life", "value_for_money", "design"]
            return fallback, {f: f.replace("_", " ").title() for f in fallback}

    # =========================
    # STAGE 1 — DISCOVERY
    # =========================
    def _discover_products(self, user_query: str) -> List[str]:
        print("[Analyzer] Running discovery...")

        chunks = self.embedder.search(query=user_query, top_k=20)

        if not chunks:
            print("[Analyzer] No chunks retrieved for discovery.")
            return []

        chunks_text = self._format_chunks(chunks)
        prompt = DISCOVERY_PROMPT.format(
            user_query=user_query,
            chunks_text=chunks_text
        )

        try:
            response = client.chat.completions.create(
                model=DISCOVERY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            text = response.choices[0].message.content.strip()
            text = self._clean_json(text)
            product_names = json.loads(text)

            if not isinstance(product_names, list):
                raise ValueError("Discovery response is not a list")

            return product_names

        except Exception as e:
            print(f"[Analyzer] Discovery failed: {e}")
            return []

    # =========================
    # STAGE 2 — PER PRODUCT ANALYSIS
    # =========================
    def _analyze_product(self, product_name: str) -> Optional[ProductAnalysis]:
        chunks = self.embedder.search_by_product(product_name=product_name, top_k=5)

        if not chunks:
            print(f"[Analyzer] No chunks found for {product_name}, skipping.")
            return None

        relevant_chunks = self._filter_by_mention(chunks, product_name)

        if not relevant_chunks:
            print(f"[Analyzer] No direct mentions for {product_name}, skipping.")
            return None

        print(f"[Analyzer] {product_name} → {len(relevant_chunks)} relevant chunks")

        # Format features list for the prompt
        features_list = "\n".join([
            f"- {key}: {self.feature_labels.get(key, key.replace('_', ' ').title())}"
            for key in self.features
        ])

        chunks_text = self._format_chunks_with_metadata(relevant_chunks)

        prompt = ANALYSIS_PROMPT.format(
            product_name=product_name,
            features_list=features_list,
            chunks_text=chunks_text
        )

        try:
            response = client.chat.completions.create(
                model=ANALYSIS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            text = response.choices[0].message.content.strip()
            text = self._clean_json(text)
            data = json.loads(text)

            return self._parse_product_analysis(data)

        except Exception as e:
            print(f"[Analyzer] Analysis failed for {product_name}: {e}")
            return None

    # =========================
    # PARSE LLM RESPONSE → ProductAnalysis
    # =========================
    def _parse_product_analysis(self, data: dict) -> ProductAnalysis:
        features = {}

        for feature_key, feature_data in data.get("features", {}).items():
            evidence_list = []

            for e in feature_data.get("evidence", []):
                evidence = Evidence(
                    quote=e.get("quote", ""),
                    source_name=e.get("source_name", ""),
                    source_type=e.get("source_type", ""),
                    url=e.get("url", ""),
                    timestamp=e.get("timestamp")
                )
                evidence_list.append(evidence)

            feature_score = FeatureScore(
                score=float(feature_data.get("score", 0)),
                summary=feature_data.get("summary", ""),
                evidence=evidence_list
            )

            features[feature_key] = feature_score

        return ProductAnalysis(
            name=data.get("name", ""),
            price=data.get("price"),
            overall_score=data.get("overall_score"),
            verdict=data.get("verdict"),
            features=features
        )

    # =========================
    # HELPERS
    # =========================
    def _filter_by_mention(self, chunks: List[Chunk], product_name: str) -> List[Chunk]:
        name_lower = product_name.lower()
        parts = name_lower.split()
        variants = list(set([
            name_lower,
            " ".join(parts[1:]) if len(parts) > 1 else name_lower,
            parts[-1] if len(parts) > 1 else name_lower
        ]))

        matched = []
        for chunk in chunks:
            chunk_lower = chunk.text.lower()
            if any(variant in chunk_lower for variant in variants):
                matched.append(chunk)
        return matched

    def _format_chunks(self, chunks: List[Chunk]) -> str:
        return "\n\n".join([
            f"--- Chunk {i+1} ---\n{chunk.text}"
            for i, chunk in enumerate(chunks)
        ])

    def _format_chunks_with_metadata(self, chunks: List[Chunk]) -> str:
        parts = []
        for i, chunk in enumerate(chunks):
            meta_lines = [
                f"Source: {chunk.source_name}",
                f"Type: {chunk.source_type}",
                f"URL: {chunk.url}",
            ]
            if chunk.timestamp:
                meta_lines.append(f"Timestamp: {chunk.timestamp}")
            meta = "\n".join(meta_lines)
            parts.append(f"--- Chunk {i+1} ---\n{meta}\n\n{chunk.text}")
        return "\n\n".join(parts)

    def _clean_json(self, text: str) -> str:
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text
