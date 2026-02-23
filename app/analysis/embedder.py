# from typing import List, Optional
# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

# from app.analysis.models import Chunk


# class Embedder:
#     """
#     Embeds chunks using sentence-transformers and stores them in ChromaDB.
#     Supports semantic search with optional metadata filtering.

#     Model: all-MiniLM-L6-v2 (free, fast, runs locally, no API cost)
#     DB: ChromaDB in-memory (resets per session — perfect for your use case
#         since each user query starts fresh)
#     """

#     EMBEDDING_MODEL = "all-MiniLM-L6-v2"
#     COLLECTION_NAME = "chunks"

#     def __init__(self):
#         print("[Embedder] Loading embedding model...")
#         self.model = SentenceTransformer(self.EMBEDDING_MODEL)

#         # In-memory ChromaDB — no disk setup needed
#         self.client = chromadb.Client(Settings(anonymized_telemetry=False))
#         self.collection = self.client.create_collection(name=self.COLLECTION_NAME)
#         print("[Embedder] ChromaDB collection ready.")

#     # =========================
#     # INDEX ALL CHUNKS
#     # =========================
#     def index(self, chunks: List[Chunk]) -> None:
#         """
#         Embeds all chunks and stores them in ChromaDB with metadata.
#         Called once after chunking is done.
#         """
#         if not chunks:
#             print("[Embedder] No chunks to index.")
#             return

#         print(f"[Embedder] Indexing {len(chunks)} chunks...")

#         texts = [chunk.text for chunk in chunks]
#         ids = [chunk.chunk_id for chunk in chunks]
#         metadatas = [self._build_metadata(chunk) for chunk in chunks]

#         # Embed all at once (batch is faster than one by one)
#         embeddings = self.model.encode(texts, show_progress_bar=True).tolist()

#         self.collection.add(
#             ids=ids,
#             documents=texts,
#             embeddings=embeddings,
#             metadatas=metadatas
#         )

#         print(f"[Embedder] Successfully indexed {len(chunks)} chunks.")

#     # =========================
#     # SEMANTIC SEARCH
#     # =========================
#     def search(
#         self,
#         query: str,
#         top_k: int = 50,
#         source_type: Optional[str] = None   # "youtube" or "article" or None for both
#     ) -> List[Chunk]:
#         """
#         Embeds the query and retrieves top_k most similar chunks.
#         Optionally filter by source_type.
#         """
#         query_embedding = self.model.encode(query).tolist()

#         where_filter = {}
#         if source_type:
#             where_filter = {"source_type": {"$eq": source_type}}

#         results = self.collection.query(
#             query_embeddings=[query_embedding],
#             n_results=top_k,
#             where=where_filter if where_filter else None,
#             include=["documents", "metadatas", "distances"]
#         )

#         return self._parse_results(results)

#     # =========================
#     # SEARCH BY PRODUCT NAME
#     # =========================
#     def search_by_product(
#         self,
#         product_name: str,
#         top_k: int = 10
#     ) -> List[Chunk]:
#         """
#         Retrieves chunks most semantically similar to a product + features query.
#         This is called per-product during the analysis step to guarantee
#         every product gets its own focused set of chunks.
#         """
#         # Build a rich query so we retrieve feature-relevant chunks too
#         query = f"{product_name} camera battery display performance value"
#         return self.search(query=query, top_k=top_k)

#     # =========================
#     # HELPERS
#     # =========================
#     def _build_metadata(self, chunk: Chunk) -> dict:
#         """
#         Builds the metadata dict stored alongside each chunk in ChromaDB.
#         ChromaDB only supports str, int, float, bool in metadata — no None values.
#         """
#         return {
#             "source_name": chunk.source_name,
#             "source_type": chunk.source_type,
#             "url": chunk.url,
#             "chunk_id": chunk.chunk_id,
#             "video_id": chunk.video_id or "",
#             "timestamp": chunk.timestamp or "",
#             "start_seconds": chunk.start_seconds if chunk.start_seconds is not None else -1
#         }

#     def _parse_results(self, results: dict) -> List[Chunk]:
#         """
#         Converts raw ChromaDB query results back into Chunk objects.
#         """
#         chunks = []

#         documents = results.get("documents", [[]])[0]
#         metadatas = results.get("metadatas", [[]])[0]

#         for text, meta in zip(documents, metadatas):
#             chunk = Chunk(
#                 text=text,
#                 source_name=meta["source_name"],
#                 source_type=meta["source_type"],
#                 url=meta["url"],
#                 chunk_id=meta["chunk_id"],
#                 video_id=meta["video_id"] or None,
#                 timestamp=meta["timestamp"] or None,
#                 start_seconds=meta["start_seconds"] if meta["start_seconds"] != -1 else None
#             )
#             chunks.append(chunk)

#         return chunks

from typing import List, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI

from app.analysis.models import Chunk
from app.config.settings import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


class Embedder:
    """
    Embeds chunks using OpenAI text-embedding-3-small and stores them in ChromaDB.

    Why switched from sentence-transformers:
    - sentence-transformers loads a ~500MB model into RAM on startup
    - Render/Railway free tier only gives 512MB RAM — not enough
    - OpenAI embeddings are API calls — no RAM usage, no model loading
    - text-embedding-3-small is fast, cheap (~$0.00002 per 1K tokens) and accurate
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    COLLECTION_NAME = "chunks"
    BATCH_SIZE = 100    # OpenAI allows up to 2048 inputs per request, 100 is safe

    def __init__(self):
        print("[Embedder] Initializing with OpenAI embeddings...")

        # In-memory ChromaDB — resets per session, no disk setup needed
        self.chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.create_collection(name=self.COLLECTION_NAME)

        print("[Embedder] Ready.")

    # =========================
    # EMBED TEXT(S) VIA OPENAI
    # =========================
    def _embed(self, texts: List[str]) -> List[List[float]]:
        """
        Calls OpenAI embeddings API and returns a list of embedding vectors.
        Handles batching to avoid hitting API limits.
        """
        all_embeddings = []

        # Process in batches to avoid request size limits
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i:i + self.BATCH_SIZE]

            response = client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    # =========================
    # INDEX ALL CHUNKS
    # =========================
    def index(self, chunks: List[Chunk]) -> None:
        """
        Embeds all chunks and stores them in ChromaDB with metadata.
        Called once after chunking is done.
        """
        if not chunks:
            print("[Embedder] No chunks to index.")
            return

        print(f"[Embedder] Indexing {len(chunks)} chunks via OpenAI embeddings...")

        texts = [chunk.text for chunk in chunks]
        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [self._build_metadata(chunk) for chunk in chunks]

        # Embed all texts (batched internally)
        embeddings = self._embed(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(f"[Embedder] Successfully indexed {len(chunks)} chunks.")

    # =========================
    # SEMANTIC SEARCH
    # =========================
    def search(
        self,
        query: str,
        top_k: int = 20,
        source_type: Optional[str] = None   # "youtube" or "article" or None for both
    ) -> List[Chunk]:
        """
        Embeds the query and retrieves top_k most similar chunks.
        Optionally filter by source_type.
        """
        query_embedding = self._embed([query])[0]

        where_filter = None
        if source_type:
            where_filter = {"source_type": {"$eq": source_type}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        return self._parse_results(results)

    # =========================
    # SEARCH BY PRODUCT NAME
    # =========================
    def search_by_product(
        self,
        product_name: str,
        top_k: int = 5
    ) -> List[Chunk]:
        """
        Retrieves chunks most semantically similar to a product query.
        Called per-product during analysis to get focused relevant chunks.
        """
        query = f"{product_name} review features specifications"
        return self.search(query=query, top_k=top_k)

    # =========================
    # HELPERS
    # =========================
    def _build_metadata(self, chunk: Chunk) -> dict:
        """
        Builds the metadata dict stored alongside each chunk in ChromaDB.
        ChromaDB only supports str, int, float, bool — no None values allowed.
        """
        return {
            "source_name": chunk.source_name,
            "source_type": chunk.source_type,
            "url": chunk.url,
            "chunk_id": chunk.chunk_id,
            "video_id": chunk.video_id or "",
            "timestamp": chunk.timestamp or "",
            "start_seconds": chunk.start_seconds if chunk.start_seconds is not None else -1
        }

    def _parse_results(self, results: dict) -> List[Chunk]:
        """
        Converts raw ChromaDB query results back into Chunk objects.
        """
        chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for text, meta in zip(documents, metadatas):
            chunk = Chunk(
                text=text,
                source_name=meta["source_name"],
                source_type=meta["source_type"],
                url=meta["url"],
                chunk_id=meta["chunk_id"],
                video_id=meta["video_id"] or None,
                timestamp=meta["timestamp"] or None,
                start_seconds=meta["start_seconds"] if meta["start_seconds"] != -1 else None
            )
            chunks.append(chunk)

        return chunks