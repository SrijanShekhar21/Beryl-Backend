import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.search.models import ArticleSource
from app.scraper.article_scraper import ArticleScraper

# Use a real URL from your test_search output
articles = [
    ArticleSource(
        title="Test Article",
        url="https://www.gsmarena.com/best_phones_under_30000-blog-print.php3",
        domain="gsmarena.com"
    )
]

scraper = ArticleScraper()
scraped = scraper.scrape(articles)

for a in scraped:
    print(f"Title: {a.title}")
    print(f"Content length: {len(a.content)} chars")
    print(f"First 500 chars:\n{a.content[:500]}")