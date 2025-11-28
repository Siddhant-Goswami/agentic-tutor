"""
Content Extractor

Fetches and extracts main article content from URLs.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract main content from article URLs."""

    def __init__(self, user_agent: str = "AI Learning Coach/1.0"):
        """
        Initialize content extractor.

        Args:
            user_agent: User agent string for HTTP requests
        """
        self.user_agent = user_agent
        self.timeout = 30.0

    async def extract(self, url: str) -> Optional[str]:
        """
        Extract full article content from URL.

        Args:
            url: Article URL

        Returns:
            Extracted article text, or None if extraction fails
        """
        logger.info(f"Extracting content from: {url}")

        try:
            # Fetch HTML
            html = await self._fetch_html(url)
            if not html:
                return None

            # Try specialized extraction for common platforms
            content = self._extract_with_beautifulsoup(html)

            if content and len(content) > 500:
                logger.info(f"Extracted {len(content)} chars ({len(content.split())} words)")
                return content

            logger.warning(f"Could not extract meaningful content from {url}")
            return None

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    async def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {e}")
            return None

    def _extract_with_beautifulsoup(self, html: str) -> Optional[str]:
        """
        Extract content using BeautifulSoup.

        Handles most blog platforms by finding main content areas
        and removing navigation, ads, etc.

        Args:
            html: HTML content

        Returns:
            Extracted text or None if failed
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup([
                "script", "style", "nav", "footer", "header",
                "aside", "form", "button", "iframe", "noscript"
            ]):
                element.decompose()

            # Remove common navigation/sidebar classes
            for class_name in [
                "navigation", "sidebar", "menu", "header", "footer",
                "ad", "advertisement", "social", "share", "comment",
                "related", "recommend"
            ]:
                for element in soup.find_all(class_=re.compile(class_name, re.I)):
                    element.decompose()

            # Find main content area
            # Try common content containers in order of preference
            main = None

            # Try semantic HTML5 tags
            main = soup.find("article")
            if not main:
                main = soup.find("main")

            # Try common content divs/sections
            if not main:
                main = soup.find("div", class_=re.compile(r"(post|article|content|entry)[-_]?(body|content)?", re.I))

            if not main:
                main = soup.find("section", class_=re.compile(r"(post|article|content)", re.I))

            # Try by ID
            if not main:
                main = soup.find(id=re.compile(r"(post|article|content|main)", re.I))

            # Fallback to body
            if not main:
                main = soup.find("body")

            if main:
                # Extract text from main content
                text = main.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Remove very short lines that are likely navigation
            paragraphs = text.split(". ")
            cleaned_paragraphs = [p for p in paragraphs if len(p.split()) > 5]
            text = ". ".join(cleaned_paragraphs)

            return text if len(text) > 100 else None

        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed: {e}")
            return None


async def extract_content(url: str, user_agent: str = "AI Learning Coach/1.0") -> Optional[str]:
    """
    Convenience function to extract content from a URL.

    Args:
        url: Article URL
        user_agent: User agent string

    Returns:
        Extracted article text or None
    """
    extractor = ContentExtractor(user_agent)
    return await extractor.extract(url)
