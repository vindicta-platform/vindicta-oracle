"""ChromaDB concrete client for vector storage."""

from typing import Any
import chromadb

class ChromaDBClient:
    """Persistent vector store using ChromaDB."""

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "rules") -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Upsert documents with embeddings and metadata."""
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 5,
    ) -> dict[str, Any]:
        """Query the store by embedding similarity."""
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
        )

    def get(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get documents by ID or filter."""
        return self.collection.get(
            ids=ids,
            where=where,
        )
