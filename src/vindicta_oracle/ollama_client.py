"""Ollama client for local LLM inference."""
import ollama
from pydantic import BaseModel


class OllamaConfig(BaseModel):
    """Configuration for Ollama local inference."""
    model: str = "llama3.2"
    temperature: float = 0.7
    max_tokens: int = 512


class OllamaClient:
    """Wrapper for local Ollama LLM inference."""
    
    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig()
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using local Ollama model."""
        response = ollama.chat(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        )
        return response["message"]["content"]
