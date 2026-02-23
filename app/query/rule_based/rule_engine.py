from typing import Tuple, List
from ..base_engine import BaseQueryEngine
from .parser import IntentParser, Intent
from .generator import QueryGenerator


class RuleBasedEngine(BaseQueryEngine):

    def __init__(self):
        self.parser = IntentParser()
        self.generator = QueryGenerator()

    def run(self, user_input: str) -> Tuple[Intent, List[str]]:
        intent = self.parser.parse(user_input)
        queries = self.generator.generate(intent)
        return intent, queries