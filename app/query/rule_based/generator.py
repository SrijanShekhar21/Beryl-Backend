from typing import List
from .parser import Intent
from .templates import BASE_TEMPLATES, FEATURE_TEMPLATE


class QueryGenerator:

    def generate(self, intent: Intent) -> List[str]:
        queries = []

        if not intent.category:
            return queries

        category = intent.category
        budget = intent.budget if intent.budget else ""

        # Apply base templates
        for template in BASE_TEMPLATES:
            query = template.format(category=category, budget=budget)
            queries.append(query.strip())

        # Add feature-specific queries
        for feature in intent.features:
            query = FEATURE_TEMPLATE.format(
                feature=feature,
                category=category,
                budget=budget
            )
            queries.append(query.strip())

        # Remove duplicates
        queries = list(set(queries))

        return queries