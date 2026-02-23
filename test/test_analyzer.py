import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.search.models import ArticleSource
from app.analysis.chunker import Chunker
from app.analysis.embedder import Embedder
from app.analysis.analyzer import Analyzer

# Use real content from your earlier scraper test
article = ArticleSource(
    title="Best phones under 30000",
    url="https://gsmarena.com/test",
    domain="gsmarena.com",
    content="""
    Samsung Galaxy A55 is our top pick under 30000. 
    The 50MP camera is exceptional and produces stunning photos even at night.
    Battery life is decent at around 1.5 days on moderate usage.
    
    OnePlus Nord CE4 is the best for charging speed with its 100W fast charging.
    The camera is good but not as consistent as the A55 in low light.
    Performance is smooth for daily tasks.
    
    Poco X6 Pro dominates gaming benchmarks. The Dimensity 8300 chipset handles
    everything thrown at it. Camera is average but gaming performance is unmatched.
    """ * 20  # repeat to make it long enough to chunk properly
)

chunker = Chunker()
chunks = chunker.chunk_all([article], [])

embedder = Embedder()
embedder.index(chunks)

analyzer = Analyzer(embedder=embedder)
final_output = analyzer.analyze("best smartphone under 30000")

print(f"\nProducts found: {len(final_output.products)}")
for product in final_output.products:
    print(f"\n📱 {product.name}")
    print(f"   Score: {product.overall_score}")
    print(f"   Verdict: {product.verdict}")
    for feature_name, fs in product.features.items():
        print(f"   {feature_name}: {fs.score}/10 — {fs.summary}")
        for e in fs.evidence:
            print(f"      Quote: \"{e.quote}\"")
            print(f"      Source: {e.source_name} | {e.url}")