"""Semantic markdown chunking."""

import re
from typing import Iterator

def semantic_markdown_chunker(markdown_text: str, max_chunk_length: int = 2000) -> Iterator[str]:
    """Split markdown text roughly by headers, preserving context.
    
    Args:
        markdown_text: The markdown content to split.
        max_chunk_length: Target maximum length of a chunk (soft limit).

    Yields:
        Chunks of markdown text.
    """
    # Split by level 2 headers (##) to keep semantic rule contexts together
    chunks = re.split(r'(?=\n## )', markdown_text)
    
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        yield chunk
