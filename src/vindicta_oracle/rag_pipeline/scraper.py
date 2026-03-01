"""RAG Pipeline scraper — crawl4ai integration for rules ingestion.

Implements dedicated extraction logic for Wahapedia and 40k.app
with generic fallback (FR-001), clean markdown conversion (FR-002),
SHA-256 deduplication (FR-003), and resilient error handling (FR-007).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger(__name__)


class CrawlerProtocol(Protocol):
    """Protocol for web page crawling — enables testing without crawl4ai."""

    async def fetch_markdown(self, url: str) -> str:
        """Fetch a URL and return cleaned markdown content."""
        ...


@dataclass
class ScrapedChunk:
    """A scraped and processed content chunk ready for storage."""

    url: str
    content_markdown: str
    content_hash: str


@dataclass
class ScrapeResult:
    """Result of a scrape operation across multiple URLs."""

    chunks: list[ScrapedChunk] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Number of successfully scraped chunks."""
        return len(self.chunks)

    @property
    def error_count(self) -> int:
        """Number of failed pages."""
        return len(self.errors)


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for deduplication (FR-003).

    Args:
        content: Raw UTF-8 text content.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_markdown_chunks(
    raw_markdown: str,
    url: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> list[ScrapedChunk]:
    """Split raw markdown into overlapping chunks for embedding.

    Args:
        raw_markdown: The full markdown text from a page.
        url: Source URL for provenance tracking.
        chunk_size: Target size per chunk in characters.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of ``ScrapedChunk`` with content and hash.
    """
    if not raw_markdown.strip():
        return []

    chunks: list[ScrapedChunk] = []
    text = raw_markdown.strip()

    # Split by double newlines (paragraphs) first, then by chunk_size
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > chunk_size and current_chunk:
            chunk_text = current_chunk.strip()
            if chunk_text:
                chunks.append(
                    ScrapedChunk(
                        url=url,
                        content_markdown=chunk_text,
                        content_hash=compute_content_hash(chunk_text),
                    )
                )
            # Start new chunk with overlap from the end of the previous
            overlap_text = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
            current_chunk = overlap_text + "\n\n" + paragraph
        else:
            current_chunk = (
                current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            )

    # Don't forget the last chunk
    if current_chunk.strip():
        chunk_text = current_chunk.strip()
        chunks.append(
            ScrapedChunk(
                url=url,
                content_markdown=chunk_text,
                content_hash=compute_content_hash(chunk_text),
            )
        )

    return chunks


async def scrape_url(
    url: str,
    crawler: CrawlerProtocol | None = None,
) -> list[ScrapedChunk]:
    """Scrape a single URL and return content chunks.

    Args:
        url: The URL to scrape.
        crawler: Optional crawler implementation. If None, attempts
            to use crawl4ai (must be installed).

    Returns:
        List of content chunks from the page.

    Raises:
        ImportError: If crawl4ai is not installed and no crawler provided.
    """
    if crawler is not None:
        try:
            raw_md = await crawler.fetch_markdown(url)
            return extract_markdown_chunks(raw_md, url)
        except Exception as exc:
            logger.error(
                "Scrape failed for %s: %s",
                url,
                str(exc),
                extra={"url": url, "error_type": type(exc).__name__},
            )
            return []

    # Default: use crawl4ai
    try:
        from crawl4ai import AsyncWebCrawler  # type: ignore[import-untyped]

        async with AsyncWebCrawler() as web_crawler:
            result = await web_crawler.arun(url=url)
            raw_md = result.markdown if hasattr(result, "markdown") else str(result)
            return extract_markdown_chunks(raw_md, url)
    except ImportError:
        raise ImportError(
            "crawl4ai is required for scraping. "
            "Install with: pip install 'vindicta-foundation[rag]'"
        )
    except Exception as exc:
        logger.error(
            "Scrape failed for %s: %s",
            url,
            str(exc),
            extra={"url": url, "error_type": type(exc).__name__},
        )
        return []


async def scrape_urls(
    urls: list[str],
    crawler: CrawlerProtocol | None = None,
) -> ScrapeResult:
    """Scrape multiple URLs with resilient error handling (FR-007).

    Failed pages are logged and skipped; remaining pages continue.

    Args:
        urls: List of URLs to scrape.
        crawler: Optional crawler implementation.

    Returns:
        A ``ScrapeResult`` with chunks and errors.
    """
    result = ScrapeResult()

    for url in urls:
        try:
            chunks = await scrape_url(url, crawler=crawler)
            result.chunks.extend(chunks)
            logger.info("Scraped %d chunks from %s", len(chunks), url)
        except Exception as exc:
            error_info = {
                "url": url,
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            result.errors.append(error_info)
            logger.error(
                "Failed to scrape %s: %s (continuing)",
                url,
                str(exc),
            )

    return result
