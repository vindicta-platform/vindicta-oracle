"""Ollama concrete client for local embeddings."""

import ollama

class OllamaEmbeddingClient:
    """Provides local embeddings via Ollama."""

    def __init__(self, model: str = "nomic-embed-text") -> None:
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        response = ollama.embeddings(model=self.model, prompt=text)
        return response["embedding"]
