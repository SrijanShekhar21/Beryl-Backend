import json
from typing import List, Optional, Dict, Any
from openai import OpenAI

from app.config.settings import OPENAI_API_KEY
from app.search.models import ArticleSource, VideoSource
from app.analysis.chunker import Chunker
from app.analysis.embedder import Embedder
from app.analysis.analyzer import Analyzer
from app.analysis.models import FinalOutput, ProductAnalysis
from app.analysis.prompts import FOLLOWUP_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)
FOLLOWUP_MODEL = "gpt-4o-mini"


class AnalysisOrchestrator:

    def __init__(self):
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.analyzer = Analyzer(embedder=self.embedder)
        self.final_output: Optional[FinalOutput] = None
        self.category: str = "product"

    # =========================
    # MAIN ANALYSIS RUN
    # =========================
    def run(
        self,
        user_query: str,
        category: str,
        articles: List[ArticleSource],
        videos: List[VideoSource]
    ) -> FinalOutput:

        print("\n========== ANALYSIS ORCHESTRATOR START ==========\n")
        self.category = category

        print("[Orchestrator] Chunking content...")
        all_chunks = self.chunker.chunk_all(articles, videos)

        if not all_chunks:
            print("[Orchestrator] No chunks produced. Aborting.")
            return FinalOutput(query=user_query)

        print("[Orchestrator] Embedding and indexing chunks...")
        self.embedder.index(all_chunks)

        print("[Orchestrator] Running LLM analysis...")
        # Pass category so analyzer can determine features dynamically
        self.final_output = self.analyzer.analyze(user_query, category=category)

        print("\n========== ANALYSIS ORCHESTRATOR COMPLETE ==========\n")
        return self.final_output

    # =========================
    # FOLLOW-UP HANDLER
    # =========================
    def handle_followup(self, followup_query: str) -> Dict[str, Any]:
        if not self.final_output or not self.final_output.products:
            return {
                "response_type": "text",
                "answer": "No analysis available yet. Please run a new search first."
            }

        # Detect if the follow-up matches any feature we analyzed
        matched_features = self._detect_features(followup_query)

        if matched_features:
            print(f"[Orchestrator] Follow-up matched features: {matched_features}")
            return self._handle_feature_followup(followup_query, matched_features)
        else:
            print("[Orchestrator] No feature match — using text fallback")
            return self._handle_text_followup(followup_query)

    # =========================
    # FEATURE FOLLOW-UP
    # Returns sorted product cards with relevant features highlighted
    # =========================
    def _handle_feature_followup(
        self,
        followup_query: str,
        features: List[str]
    ) -> Dict[str, Any]:

        primary_feature = features[0]

        # Sort by primary feature score
        sorted_products = sorted(
            self.final_output.products,
            key=lambda p: (
                p.features.get(primary_feature).score
                if p.features.get(primary_feature) else 0
            ),
            reverse=True
        )

        # Build product dicts with only the relevant features highlighted
        product_dicts = []
        for product in sorted_products:
            features_data = {}
            for feature in features:
                if feature in product.features:
                    fs = product.features[feature]
                    features_data[feature] = {
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

            product_dicts.append({
                "name": product.name,
                "price": product.price,
                "overall_score": product.overall_score,
                "verdict": product.verdict,
                "features": features_data
            })

        intro = self._generate_intro(sorted_products, primary_feature)

        return {
            "response_type": "products",
            "intro": intro,
            "products": product_dicts
        }

    # =========================
    # TEXT FOLLOW-UP
    # For questions not matching any known feature
    # =========================
    def _handle_text_followup(self, followup_query: str) -> Dict[str, Any]:
        context = json.dumps(self.final_output.to_dict(), indent=2)

        prompt = FOLLOWUP_PROMPT.format(
            followup_query=followup_query,
            context=context
        )

        try:
            response = client.chat.completions.create(
                model=FOLLOWUP_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return {
                "response_type": "text",
                "answer": response.choices[0].message.content.strip()
            }
        except Exception as e:
            print(f"[Orchestrator] Text followup failed: {e}")
            return {
                "response_type": "text",
                "answer": "Sorry, I couldn't process that. Please try again."
            }

    # =========================
    # FEATURE DETECTION FROM FOLLOW-UP QUERY
    # Dynamically matches against features we actually analyzed
    # instead of a hardcoded list
    # =========================
    def _detect_features(self, query: str) -> List[str]:
        """
        Matches the follow-up query against the features we actually analyzed.
        Uses the feature keys and labels from the analyzer — fully dynamic.
        """
        query_lower = query.lower()
        matched = []

        # Get the features and labels that were actually used in analysis
        analyzed_features = self.analyzer.features
        analyzed_labels = self.analyzer.feature_labels

        for feature_key in analyzed_features:
            # Check if feature key words appear in query
            key_words = feature_key.replace("_", " ").split()
            label_words = analyzed_labels.get(feature_key, "").lower().split()

            all_words = key_words + label_words

            if any(word in query_lower for word in all_words if len(word) > 2):
                matched.append(feature_key)

        return matched

    # =========================
    # GENERATE INTRO TEXT
    # =========================
    def _generate_intro(
        self,
        sorted_products: List[ProductAnalysis],
        feature: str
    ) -> str:
        feature_label = self.analyzer.feature_labels.get(
            feature,
            feature.replace("_", " ").title()
        )
        top = sorted_products[0].name if sorted_products else "N/A"
        fs = sorted_products[0].features.get(feature) if sorted_products else None
        top_score = fs.score if fs else 0

        return (
            f"Here are the products ranked by **{feature_label}**. "
            f"**{top}** leads with a score of **{top_score}/10**. "
            f"Click any feature bar to see exact reviewer quotes."
        )
