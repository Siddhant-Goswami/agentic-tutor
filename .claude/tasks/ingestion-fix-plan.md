# Ingestion Pipeline Fix Plan

**Date:** 2025-11-28
**Status:** Investigation Complete - Ready for Implementation

---

## Root Cause Analysis

### Problem Statement

The database shows very few embeddings (~10 visible), all with `chunk_sequence = 0`, indicating:
- Each article is creating only **1 chunk**
- Content is insufficient for proper semantic search
- Agent cannot find relevant detailed content

###Investigation Findings

#### 1. RSS Feed Returns Only Summaries ❌

**Test Results:**
```
RSS URL: https://rss.app/feeds/qu967jeuhCa7lfcs.xml
Entries: 12
Average content length: ~460 characters (~70 words)
```

**Example:**
- **Title:** "SEPs Are Moving to Pull Requests"
- **Content:** Only 73 words (summary only)
- **Full blog post:** ~2000+ words (NOT in RSS feed)

#### 2. Current Ingestion Flow

```
RSS Feed → Parse Entry → Extract Summary (70 words)
                             ↓
                    Chunk (creates 1 chunk only)
                             ↓
                    Embed (1 embedding per article)
                             ↓
                    Store (chunk_sequence = 0)
```

**Why This Fails:**
- RSS feeds typically contain **summaries**, not full articles
- 70-word summaries are below the minimum chunk size (100 tokens)
- Result: Each article = 1 tiny chunk = poor search quality

#### 3. Code Analysis

**Current RSS Fetcher (`rss_fetcher.py:120-130`):**
```python
# Extract content (prefer content over summary)
content = ""
if hasattr(entry, "content") and entry.content:
    content = entry.content[0].value  # Still just summary
elif hasattr(entry, "summary"):
    content = entry.summary  # Also just summary
```

**Problem:** Both `content` and `summary` from RSS only contain excerpts.

**Current Chunker (`chunker.py:53-132`):**
- Chunk size: 750 tokens
- Minimum chunk: 100 tokens
- Works correctly, but input is too short

**Current Orchestrator (`orchestrator.py:196`):**
```python
chunks = chunk_document(article)  # Article has only summary text
```

---

## Solution Design

### Approach: Full Article Content Fetching

Add a **content extraction stage** after RSS parsing:

```
RSS Feed → Parse Entry → Extract URL
                            ↓
                    Fetch Full HTML from URL  ← NEW
                            ↓
                    Extract Main Content       ← NEW
                            ↓
                    Chunk (creates 10-20 chunks)
                            ↓
                    Embed (10-20 embeddings per article)
                            ↓
                    Store
```

### Implementation Strategy

#### Phase 1: Add HTML Content Fetcher

**New File:** `learning-coach-mcp/src/ingestion/content_extractor.py`

**Purpose:** Fetch and extract main content from article URLs

**Features:**
- Fetch full HTML from article URL
- Extract main content (remove navigation, ads, etc.)
- Handle common blog platforms (Medium, Substack, Hugo, Jekyll)
- Fallback to BeautifulSoup if specialized extraction fails

**Libraries:**
- `newspaper3k` - Article extraction (handles most blogs)
- `trafilatura` - Fallback extraction
- `httpx` - HTTP requests
- `BeautifulSoup4` - HTML parsing

#### Phase 2: Update RSS Fetcher

**File:** `learning-coach-mcp/src/ingestion/rss_fetcher.py`

**Changes:**
1. Add `fetch_full_content` parameter (default: True)
2. After parsing entry, if full content needed:
   - Call content extractor with article URL
   - Replace summary with full extracted content
3. Keep summary as fallback if extraction fails

**New Flow:**
```python
async def fetch_feed(self, feed_url, fetch_full_content=True):
    # ... existing code ...
    for entry in feed.entries:
        article = self._parse_entry(entry)

        if fetch_full_content and article.get("url"):
            # NEW: Fetch full article content
            full_content = await self.content_extractor.extract(article["url"])
            if full_content:
                article["content"] = full_content
                article["content_source"] = "full_article"
            else:
                article["content_source"] = "rss_summary"

        articles.append(article)
```

#### Phase 3: Update Orchestrator

**File:** `learning-coach-mcp/src/ingestion/orchestrator.py`

**Changes:**
1. Add content extraction toggle (default: enabled)
2. Add retry logic for failed extractions
3. Log content source (summary vs full article)
4. Add statistics tracking

**Metrics to Track:**
- Articles with full content vs summaries
- Average chunks per article
- Extraction success rate
- Total embeddings created

#### Phase 4: Database Migration (Optional)

**Enhancement:** Add content metadata

```sql
-- Add column to track content source
ALTER TABLE content
ADD COLUMN content_source TEXT DEFAULT 'rss_summary'
CHECK (content_source IN ('rss_summary', 'full_article', 'manual'));

-- Add column for extraction attempt tracking
ALTER TABLE content
ADD COLUMN extraction_attempted_at TIMESTAMPTZ;
```

---

## Detailed Implementation

### 1. Content Extractor (NEW)

**File:** `learning-coach-mcp/src/ingestion/content_extractor.py`

```python
"""
Content Extractor

Fetches and extracts main article content from URLs.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from newspaper import Article
from trafilatura import extract
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract main content from article URLs."""

    def __init__(self, user_agent: str = "AI Learning Coach/1.0"):
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

            # Try newspaper3k first (best for blogs)
            content = self._extract_with_newspaper(url, html)
            if content and len(content) > 500:
                logger.info(f"Extracted {len(content)} chars with newspaper3k")
                return content

            # Fallback to trafilatura
            content = self._extract_with_trafilatura(html)
            if content and len(content) > 500:
                logger.info(f"Extracted {len(content)} chars with trafilatura")
                return content

            # Last resort: BeautifulSoup
            content = self._extract_with_beautifulsoup(html)
            if content and len(content) > 500:
                logger.info(f"Extracted {len(content)} chars with BeautifulSoup")
                return content

            logger.warning(f"Could not extract meaningful content from {url}")
            return None

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {e}")
            return None

    def _extract_with_newspaper(self, url: str, html: str) -> Optional[str]:
        """Extract content using newspaper3k."""
        try:
            article = Article(url)
            article.download(input_html=html)
            article.parse()
            return article.text
        except Exception as e:
            logger.debug(f"newspaper3k extraction failed: {e}")
            return None

    def _extract_with_trafilatura(self, html: str) -> Optional[str]:
        """Extract content using trafilatura."""
        try:
            return extract(html)
        except Exception as e:
            logger.debug(f"trafilatura extraction failed: {e}")
            return None

    def _extract_with_beautifulsoup(self, html: str) -> Optional[str]:
        """Extract content using BeautifulSoup (last resort)."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                element.decompose()

            # Find main content area
            main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")

            if main:
                text = main.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed: {e}")
            return None
```

### 2. Update RSS Fetcher

**File:** `learning-coach-mcp/src/ingestion/rss_fetcher.py`

**Changes:**

```python
from .content_extractor import ContentExtractor  # ADD

class RSSFetcher:
    def __init__(self, user_agent: str = "AI Learning Coach/1.0", fetch_full_content: bool = True):
        self.user_agent = user_agent
        self.fetch_full_content = fetch_full_content
        self.content_extractor = ContentExtractor(user_agent) if fetch_full_content else None

    async def fetch_feed(
        self,
        feed_url: str,
        since: Optional[datetime] = None,
        max_articles: int = 50,
        fetch_full_content: Optional[bool] = None,  # NEW parameter
    ) -> List[Dict[str, Any]]:
        # ... existing code ...

        # Extract articles
        articles = []
        for entry in feed.entries[:max_articles]:
            article = self._parse_entry(entry)

            # NEW: Fetch full content if enabled
            if (fetch_full_content if fetch_full_content is not None else self.fetch_full_content):
                if article.get("url"):
                    logger.info(f"Fetching full content for: {article['title']}")
                    full_content = await self.content_extractor.extract(article["url"])

                    if full_content and len(full_content) > len(article["content"]):
                        article["content"] = full_content
                        article["content_source"] = "full_article"
                        logger.info(f"✓ Got full content: {len(full_content)} chars")
                    else:
                        article["content_source"] = "rss_summary"
                        logger.warning(f"Using RSS summary for: {article['title']}")
            else:
                article["content_source"] = "rss_summary"

            # Filter by date if specified
            if since and article.get("published_at"):
                if article["published_at"] <= since:
                    continue

            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from {feed_url}")
        return articles
```

### 3. Update Orchestrator

**File:** `learning-coach-mcp/src/ingestion/orchestrator.py`

**Changes:**

```python
def __init__(
    self,
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    chunk_size: int = 750,
    overlap: int = 100,
    embedding_model: str = "text-embedding-3-small",
    embedding_dimensions: int = 1536,
    fetch_full_content: bool = True,  # NEW parameter
):
    # ... existing code ...
    self.rss_fetcher = RSSFetcher(fetch_full_content=fetch_full_content)  # UPDATED
```

**Update _process_articles:**

```python
async def _process_articles(
    self,
    articles: List[Dict[str, Any]],
    source_id: str,
    user_id: str,
) -> Dict[str, Any]:
    articles_processed = 0
    chunks_created = 0
    duplicates_skipped = 0
    full_content_count = 0  # NEW
    summary_only_count = 0  # NEW

    for article in articles:
        try:
            # ... existing deduplication code ...

            # Track content source
            content_source = article.get("content_source", "rss_summary")
            if content_source == "full_article":
                full_content_count += 1
            else:
                summary_only_count += 1

            # Store article in content table
            content_result = (
                self.db.table("content")
                .insert(
                    {
                        "source_id": source_id,
                        "title": article["title"],
                        "author": article.get("author", "Unknown"),
                        "published_at": article["published_at"].isoformat()
                        if article.get("published_at")
                        else None,
                        "url": article["url"],
                        "content_hash": content_hash,
                        "raw_text": article["content"],  # Now contains full content
                        "metadata": {
                            "tags": article.get("tags", []),
                            "word_count": len(article["content"].split()),
                            "content_source": content_source,  # NEW
                        },
                    }
                )
                .execute()
            )

            # ... rest of existing code ...

        except Exception as e:
            logger.error(f"Error processing article '{article.get('title', 'unknown')}': {e}")
            continue

    return {
        "status": "success",
        "articles_processed": articles_processed,
        "chunks_created": chunks_created,
        "duplicates_skipped": duplicates_skipped,
        "full_content_fetched": full_content_count,  # NEW
        "summary_only": summary_only_count,  # NEW
    }
```

---

## Testing Plan

### 1. Unit Tests

**Test Content Extractor:**
```python
async def test_content_extractor():
    extractor = ContentExtractor()

    # Test with MCP blog post
    url = "http://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/"
    content = await extractor.extract(url)

    assert content is not None
    assert len(content) > 1000  # Should be full article
    assert "Model Context Protocol" in content

    print(f"✓ Extracted {len(content)} characters")
    print(f"✓ Word count: {len(content.split())} words")
```

### 2. Integration Tests

**Test Full Pipeline:**
```bash
# Run ingestion with full content fetching
cd learning-coach-mcp
python -m src.ingestion.orchestrator
```

**Expected Results:**
- Articles: 12
- Average chunks per article: 10-20 (vs current 1)
- Total embeddings: 120-240 (vs current ~10)

### 3. Verification

**Check Database:**
```sql
-- Count embeddings per article
SELECT
    c.title,
    COUNT(e.id) as chunk_count,
    c.metadata->>'content_source' as source
FROM content c
LEFT JOIN embeddings e ON e.content_id = c.id
GROUP BY c.id, c.title
ORDER BY chunk_count DESC;
```

**Expected Output:**
```
Title                              | chunk_count | source
-----------------------------------|-------------|-------------
"One Year of MCP..."               | 15          | full_article
"MCP Apps: Extending servers..."   | 18          | full_article
"Server Instructions..."           | 12          | full_article
```

---

## Deployment Steps

### 1. Install Dependencies

```bash
cd learning-coach-mcp
pip install newspaper3k trafilatura
```

### 2. Create Content Extractor

```bash
touch src/ingestion/content_extractor.py
# Add implementation from above
```

### 3. Update RSS Fetcher

```bash
# Edit src/ingestion/rss_fetcher.py
# Add content extraction logic
```

### 4. Update Orchestrator

```bash
# Edit src/ingestion/orchestrator.py
# Add full content fetching parameter
```

### 5. Clear Old Data (Optional)

```sql
-- Delete old summary-only embeddings
DELETE FROM embeddings;
DELETE FROM content;

-- OR mark for re-ingestion
UPDATE sources SET last_fetched = NULL;
```

### 6. Run New Ingestion

```bash
cd learning-coach-mcp
python -m src.ingestion.orchestrator
```

### 7. Verify Results

```bash
python quick_test_ingestion.py
```

---

## Success Criteria

✅ **Content Length:**
- RSS summary: ~70 words ❌
- Full article: 500-2000+ words ✅

✅ **Chunks per Article:**
- Current: 1 chunk ❌
- Target: 10-20 chunks ✅

✅ **Total Embeddings:**
- Current: ~10 ❌
- Target: 100-200+ ✅

✅ **Search Quality:**
- Can find detailed explanations ✅
- Can locate specific topics ✅
- Agent gets good context ✅

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Content extraction fails | Falls back to summary | Keep RSS summary as fallback |
| Slow ingestion | Takes longer | Run as background job, add caching |
| Website blocks requests | Can't fetch content | Use respectful User-Agent, add rate limiting |
| Content format varies | Extraction quality varies | Multiple extraction strategies (newspaper, trafilatura, BeautifulSoup) |

---

## Timeline

- **Phase 1:** Create content extractor - 30 minutes
- **Phase 2:** Update RSS fetcher - 20 minutes
- **Phase 3:** Update orchestrator - 15 minutes
- **Phase 4:** Testing - 20 minutes
- **Phase 5:** Deployment - 15 minutes

**Total:** ~2 hours

---

## Next Steps

1. ✅ **Create this plan** (Done)
2. ⏳ **Get user approval**
3. ⏳ **Implement content extractor**
4. ⏳ **Update RSS fetcher**
5. ⏳ **Update orchestrator**
6. ⏳ **Test end-to-end**
7. ⏳ **Deploy and verify**

---

**Status:** Ready for implementation pending user approval
**Priority:** High (blocks effective agent operation)
**Complexity:** Medium
