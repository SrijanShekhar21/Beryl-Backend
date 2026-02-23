import json
from typing import Tuple, List
from ..base_engine import BaseQueryEngine
from ..rule_based.parser import Intent
from ..rule_based.rule_engine import RuleBasedEngine
from .prompt import QUERY_PROMPT

from openai import OpenAI

from app.config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

class LLMQueryEngine(BaseQueryEngine):

    def __init__(self):
        self.fallback = RuleBasedEngine()

    def run(self, user_input: str) -> Tuple[Intent, List[str]]:

        try:
            prompt = QUERY_PROMPT.format(query=user_input)
            print("Generated prompt for LLM:", prompt)  # Debug print
            
            response = client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",   # cheap + fast model
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.choices[0].message.content.strip()
            print("LLM response:", text)  # Debug print

            # Gemini sometimes wraps JSON in ```json ```
            if text.startswith("```"):
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

            data = json.loads(text)   # parse JSON

            intent = Intent(
                category=data.get("category"),
                budget=data.get("budget"),
                features=data.get("features", [])
            )

            queries = data.get("queries", [])

            if not queries:
                raise ValueError("Empty queries from LLM")

            return intent, queries

        except Exception as e:
            print("LLM failed → using rule-based fallback:", e)
            return self.fallback.run(user_input)