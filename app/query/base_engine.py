from abc import ABC, abstractmethod
from typing import Tuple, List
from .rule_based.parser import Intent


class BaseQueryEngine(ABC):

    @abstractmethod
    def run(self, user_input: str) -> Tuple[Intent, List[str]]:
        pass