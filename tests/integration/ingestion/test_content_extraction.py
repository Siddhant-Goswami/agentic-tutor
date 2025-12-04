"""
Test content extraction from MCP blog.
"""

import sys
import asyncio
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "learning-coach-mcp" / "src"))

from ingestion.content_extractor import ContentExtractor


async def test_extraction():
    """Test extracting content from MCP blog."""
    print("=" * 70)
    print("TESTING CONTENT EXTRACTION")
    print("=" * 70)

    extractor = ContentExtractor()

    # Test URLs from MCP blog
    test_urls = [
        "http://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/",
        "http://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/",
    ]

    for url in test_urls:
        print(f"\n📄 Testing: {url}")
        print("-" * 70)

        try:
            content = await extractor.extract(url)

            if content:
                words = len(content.split())
                chars = len(content)

                print(f"✅ SUCCESS")
                print(f"   Characters: {chars:,}")
                print(f"   Words: {words:,}")
                print(f"   Preview: {content[:200]}...")

                # Verify it's substantial content
                if words > 500:
                    print(f"   ✓ Content is substantial (>{words} words)")
                else:
                    print(f"   ⚠️  Content seems short ({words} words)")

            else:
                print(f"❌ FAILED - No content extracted")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_extraction())
