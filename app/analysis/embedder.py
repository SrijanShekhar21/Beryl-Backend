from typing import List, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.analysis.models import Chunk


class Embedder:
    """
    Embeds chunks using sentence-transformers and stores them in ChromaDB.
    Supports semantic search with optional metadata filtering.

    Model: all-MiniLM-L6-v2 (free, fast, runs locally, no API cost)
    DB: ChromaDB in-memory (resets per session — perfect for your use case
        since each user query starts fresh)
    """

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = "chunks"

    def __init__(self):
        print("[Embedder] Loading embedding model...")
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)

        # In-memory ChromaDB — no disk setup needed
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = self.client.create_collection(name=self.COLLECTION_NAME)
        print("[Embedder] ChromaDB collection ready.")

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

        print(f"[Embedder] Indexing {len(chunks)} chunks...")

        texts = [chunk.text for chunk in chunks]
        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [self._build_metadata(chunk) for chunk in chunks]

        # Embed all at once (batch is faster than one by one)
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()

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
        top_k: int = 50,
        source_type: Optional[str] = None   # "youtube" or "article" or None for both
    ) -> List[Chunk]:
        """
        Embeds the query and retrieves top_k most similar chunks.
        Optionally filter by source_type.
        """
        query_embedding = self.model.encode(query).tolist()

        where_filter = {}
        if source_type:
            where_filter = {"source_type": {"$eq": source_type}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )

        return self._parse_results(results)

    # =========================
    # SEARCH BY PRODUCT NAME
    # =========================
    def search_by_product(
        self,
        product_name: str,
        top_k: int = 10
    ) -> List[Chunk]:
        """
        Retrieves chunks most semantically similar to a product + features query.
        This is called per-product during the analysis step to guarantee
        every product gets its own focused set of chunks.
        """
        # Build a rich query so we retrieve feature-relevant chunks too
        query = f"{product_name} camera battery display performance value"
        return self.search(query=query, top_k=top_k)

    # =========================
    # HELPERS
    # =========================
    def _build_metadata(self, chunk: Chunk) -> dict:
        """
        Builds the metadata dict stored alongside each chunk in ChromaDB.
        ChromaDB only supports str, int, float, bool in metadata — no None values.
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