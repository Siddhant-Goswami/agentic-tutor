"""
Test Web Search Tool

Simple test to verify Tavily web search integration.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from agent.tools import ToolRegistry

# Load environment variables from multiple possible locations
env_paths = [
    Path(__file__).parent / "learning-coach-mcp" / ".env",
    Path(__file__).parent / "agent" / ".env",
    Path(__file__).parent / ".env",
]

for env_path in env_paths:
    if env_path.exists():
        print(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        break


async def test_web_search():
    """Test basic web search functionality."""
    print("🔍 Testing Web Search Tool\n")

    # Check if API key is set
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("⚠️  TAVILY_API_KEY not found in environment")
        print("   Please add it to your .env file to test web search")
        print("\nTo get a free API key:")
        print("   1. Visit https://tavily.com")
        print("   2. Sign up (free tier: 1,000 searches/month)")
        print("   3. Add to .env: TAVILY_API_KEY=tvly-xxxxx\n")
        return

    # Initialize tool registry
    print("Initializing ToolRegistry...")
    tools = ToolRegistry(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test web search
    print("\nExecuting web search: 'machine learning tutorials for beginners'\n")

    result = await tools.execute_tool(
        "web-search",
        {
            "query": "machine learning tutorials for beginners",
            "max_results": 3,
            # Domain filtering requires full domains, not just TLDs
            # "include_domains": ["wikipedia.org", "khanacademy.org"]
        }
    )

    # Display results
    if "error" in result:
        print(f"❌ Error: {result['error']}\n")
        return

    print(f"✅ Search successful!")
    print(f"   Source API: {result.get('source_api')}")
    print(f"   Results found: {result.get('count')}\n")

    print("📚 Top Results:")
    print("=" * 80)

    for i, item in enumerate(result.get("results", []), 1):
        print(f"\n{i}. {item.get('title')}")
        print(f"   URL: {item.get('url')}")
        print(f"   Score: {item.get('score'):.2f}")
        print(f"   Content: {item.get('content', '')[:150]}...")
        print(f"   Source Type: {item.get('source_type')}")

    print("\n" + "=" * 80)
    print("\n📝 Citations:")

    for i, citation in enumerate(result.get("citations", []), 1):
        print(f"{i}. {citation.get('title')} - {citation.get('url')}")

    print(f"\n🔍 Search Metadata:")
    metadata = result.get("search_metadata", {})
    print(f"   Query: {metadata.get('query')}")
    print(f"   Searched at: {metadata.get('searched_at')}")
    print(f"   Search depth: {metadata.get('search_depth')}")

    print("\n✅ Web search test completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(test_web_search())
