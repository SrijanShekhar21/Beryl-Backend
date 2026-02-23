import re
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------
# Intent Data Model
# ---------------------------

@dataclass
class Intent:
    category: Optional[str]
    budget: Optional[int]
    features: List[str]

# ---------------------------
# Keyword Mappings
# ---------------------------

CATEGORY_KEYWORDS = {
    "smartphone": ["phone", "smartphone", "mobile"],
    "earphone": ["earphone", "earphones", "earbuds", "buds", "headphones", "headphone"],
    "laptop": ["laptop", "notebook", "ultrabook", "macbook", "surface"],
}

FEATURE_MAP = {
    "camera": ["camera", "photography", "photos", "video"],
    "battery": ["battery", "backup", "long battery"],
    "gaming": ["gaming", "pubg", "bgmi", "heavy gaming"],
    "performance": ["performance", "fast", "smooth", "lag"],
    "anc": ["anc", "noise cancelling", "noise cancellation"],
    "sound": ["sound", "bass", "audio quality"]
}


# ---------------------------
# Intent Parser
# ---------------------------

class IntentParser:

    def parse(self, text: str) -> Intent:
        text = self._normalize(text)

        budget = self._extract_budget(text)
        category = self._extract_category(text)
        features = self._extract_features(text)

        return Intent(
            category=category,
            budget=budget,
            features=features
        )

    # ---------------------------

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    # ---------------------------

    def _extract_budget(self, text: str) -> Optional[int]:
        patterns = [
            r"(under|below|within)\s+(\d+)(k?)",
            r"(less\s+than)\s+(\d+)(k?)",
            r"(around|approx|approximately|budget)\s+(\d+)(k?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                number = int(match.group(2))
                if match.group(3) == "k":
                    number *= 1000
                return number

        # Also detect standalone 30k pattern
        match = re.search(r"(\d+)k", text)
        if match:
            return int(match.group(1)) * 1000

        return None

    # ---------------------------

    def _extract_category(self, text: str) -> Optional[str]:
        for category, keywords in CATEGORY_KEYWORDS.items():
            for word in keywords:
                pattern = r"\b" + re.escape(word) + r"\b"
                if re.search(pattern, text):
                    return category
        return None

    # ---------------------------

    def _extract_features(self, text: str) -> List[str]:
        found = []

        for standard_feature, keywords in FEATURE_MAP.items():
            for keyword in keywords:
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, text):
                    found.append(standard_feature)
                    break  # Avoid duplicate matches

        return found