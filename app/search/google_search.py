import requests
from typing import List
from urllib.parse import urlparse

from app.config.settings import SERPER_API_KEY
from app.search.models import ArticleSource


class GoogleSearcher:

    BLOCKED_DOMAINS = [
        "youtube.com",
        "youtu.be"
    ]

    """
    Uses Serper.dev API to fetch Google search results
    and converts them into structured ArticleSource objects.
    """

    def __init__(self):
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"

    def _is_blocked_domain(self, domain: str) -> bool:
        for blocked in self.BLOCKED_DOMAINS:
            if blocked in domain:
                return True
        return False

    def search(self, queries: List[str], num_results: int = 5) -> List[ArticleSource]:
        """
        Takes a list of queries, runs search for each,
        and returns combined list of ArticleSource objects.
        """
        all_articles = []

        for query in queries:
            results = self._search_single_query(query, num_results)
            all_articles.extend(results)

        return all_articles

    def _search_single_query(self, query: str, num_results: int) -> List[ArticleSource]:
        """
        Calls Serper API for a single query and parses results.
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)

            if response.status_code != 200:
                print(f"[Serper ERROR] Query failed: {query} | Status: {response.status_code}")
                return []

            data = response.json()
            return self._parse_results(data)

        except Exception as e:
            print(f"[Serper EXCEPTION] Query: {query} | Error: {e}")
            return []

    def _parse_results(self, data: dict) -> List[ArticleSource]:
        """
        Converts Serper JSON response into ArticleSource objects.
        """
        articles = []
        organic_results = data.get("organic", [])

        for item in organic_results:
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")

            if not title or not link:
                continue

            domain = self._extract_domain(link)

            if self._is_blocked_domain(domain):
                print(f"[Blocked] Skipping {link} | Domain: {domain}")
                continue

            article = ArticleSource(
                title=title,
                url=link,
                domain=domain,
                snippet=snippet
            )

            articles.append(article)

        return articles

    def _extract_domain(self, url: str) -> str:
        """
        Extracts domain name from URL.
        Example: https://www.gadgets360.com/... → gadgets360.com
        """
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain