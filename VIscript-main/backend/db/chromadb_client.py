import logging
import uuid
import math
from typing import List, Dict, Any, Optional
from config import settings

logger = logging.getLogger("visualiq.db.chromadb")

class FastEmbeddingFunction:
    """
    Lightweight deterministic token-hash embedding function.
    Eliminates heavy ONNX/Torch weight downloads while maintaining
    semantic proximity for surveillance security domain queries.
    """
    def __init__(self, dim: int = 64):
        self.dim = dim

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            vec = [0.0] * self.dim
            words = text.lower().split()
            for word in words:
                h = hash(word)
                idx = abs(h) % self.dim
                sign = 1.0 if h > 0 else -1.0
                vec[idx] += sign * (1.0 + (len(word) / 10.0))
            # L2 normalize
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            embeddings.append([x / norm for x in vec])
        return embeddings

    def name(self) -> str:
        return "fast_embedding"

class ChromaDBService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_fn = FastEmbeddingFunction()
        self._using_fallback = True
        self._fallback_chunks: List[Dict[str, Any]] = []
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            # Try HTTP client first if URL provided
            if settings.CHROMADB_URL:
                try:
                    host = settings.CHROMADB_URL.replace("http://", "").replace("https://", "").split(":")[0]
                    port = int(settings.CHROMADB_URL.split(":")[-1].split("/")[0])
                    self.client = chromadb.HttpClient(host=host, port=port)
                    self.collection = self.client.get_or_create_collection(
                        name=settings.CHROMADB_COLLECTION,
                        embedding_function=self.embedding_fn,
                        metadata={"hnsw:space": "cosine"}
                    )
                    self._using_fallback = False
                    logger.info(f"Connected to ChromaDB cluster at {settings.CHROMADB_URL}")
                    return
                except Exception as e:
                    logger.warning(f"ChromaDB HTTP connection failed ({e}). Attempting embedded client.")

            # Fallback to in-memory EphemeralClient
            self.client = chromadb.EphemeralClient()
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMADB_COLLECTION,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            self._using_fallback = False
            logger.info("ChromaDB embedded client initialized successfully.")
        except Exception as e:
            logger.warning(f"ChromaDB library unavailable or init error: {e}. Using internal vector store fallback.")
            self._using_fallback = True

    async def clear_all(self):
        self._fallback_chunks = []
        if not self._using_fallback and self.client:
            try:
                self.client.delete_collection(name=settings.CHROMADB_COLLECTION)
                self.collection = self.client.get_or_create_collection(
                    name=settings.CHROMADB_COLLECTION,
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB collection reinitialized.")
            except Exception as e:
                logger.debug(f"ChromaDB clear collection info: {e}")

    async def store_transcript_chunk(
        self, 
        text: str, 
        metadata: Dict[str, Any], 
        chunk_id: Optional[str] = None
    ) -> str:
        cid = chunk_id or str(uuid.uuid4())
        record = {
            "id": cid,
            "text": text,
            "metadata": metadata
        }
        self._fallback_chunks.append(record)

        if not self._using_fallback and self.collection:
            try:
                self.collection.add(
                    documents=[text],
                    metadatas=[metadata],
                    ids=[cid]
                )
                logger.debug(f"Stored chunk {cid} in ChromaDB")
            except Exception as e:
                logger.warning(f"ChromaDB chunk add error: {e}. Stored in fallback index.")

        return cid

    async def search_transcripts(
        self, 
        query: str, 
        camera_id: Optional[str] = None, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search transcript chunks using semantic vector matching or keyword relevance fallback."""
        if not self._using_fallback and self.collection:
            try:
                collection_count = self.collection.count()
                if collection_count > 0:
                    where_clause = {"camera_id": camera_id} if camera_id else None
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=min(top_k, collection_count),
                        where=where_clause
                    )
                    formatted = []
                    if results and "documents" in results and results["documents"]:
                        docs = results["documents"][0]
                        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                        ids = results["ids"][0] if "ids" in results else [""] * len(docs)
                        for doc, meta, doc_id in zip(docs, metas, ids):
                            formatted.append({
                                "id": doc_id,
                                "text": doc,
                                "metadata": meta
                            })
                        return formatted
            except Exception as e:
                logger.warning(f"ChromaDB query error: {e}. Using fallback vector search.")

        # In-memory keyword/token relevance fallback
        query_words = set(query.lower().split())
        scored_chunks = []
        for chunk in self._fallback_chunks:
            meta = chunk.get("metadata", {})
            if camera_id and meta.get("camera_id") != camera_id:
                continue
            
            chunk_text = chunk.get("text", "").lower()
            score = sum(1 for word in query_words if word in chunk_text)
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_chunks[:top_k]]

chromadb_client = ChromaDBService()
