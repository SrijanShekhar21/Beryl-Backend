import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.chunker import Chunker
from app.analysis.embedder import Embedder
from app.search.models import ArticleSource

article = ArticleSource(
    title="Best phones under 30000",
    url="https://gsmarena.com/test",
    domain="gsmarena.com",
    content=(
        "Samsung Galaxy A55 has an excellent 50MP camera. "
        "OnePlus Nord CE4 has 100W fast charging. "
        "Poco X6 Pro is the best for gaming with Dimensity 8300. "
    ) * 100
)

chunker = Chunker()
chunks = chunker.chunk_all([article], [])

embedder = Embedder()
embedder.index(chunks)

print(f"\nIndexed {len(chunks)} chunks")

# Test semantic search
results = embedder.search("best camera phone", top_k=3)
print(f"\nTop 3 results for 'best camera phone':")
for r in results:
    print(f"  → {r.text[:100]}")

# Test product search
results = embedder.search_by_product("Samsung Galaxy A55", top_k=3)
print(f"\nTop 3 results for Samsung Galaxy A55:")
for r in results:
    print(f"  → {r.text[:100]}")