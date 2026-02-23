import requests
from typing import List, Optional

from app.config.settings import SERPER_API_KEY
from app.search.models import ArticleSource


class ArticleScraper:
    """
    Uses Serper Scrape API to fetch readable article content.
    """

    def __init__(self):
        self.api_url = "https://scrape.serper.dev"
        self.headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

    def _fetch_content(self, url: str) -> Optional[str]:
        try:
            payload = {"url": url}

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=20
            )

            if response.status_code != 200:
                print(f"[Scraper] Failed {url} | Status {response.status_code}")
                return None

            data = response.json()

            text = data.get("text")

            return self._clean_text(text)

        except Exception as e:
            print(f"[Scraper Error] {url} | {e}")
            return None

    def scrape(self, articles: List[ArticleSource]) -> List[ArticleSource]:

        cleaned_articles = []

        for article in articles:
            print(f"[Scraping] {article.url}")

            content = self._fetch_content(article.url)

            if content:
                article.content = content
                cleaned_articles.append(article)
            else:
                print(f"[Skipped] No valid content for {article.url}")

        return cleaned_articles

    def _clean_text(self, text: str) -> str:
        lines = text.splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        return " ".join(lines)