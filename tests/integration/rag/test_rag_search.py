"""
Test RAG search to debug why MCP Apps article isn't being returned.
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client

# Load environment
project_root = Path(__file__).parent
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)


async def test_search():
    """Test search with user's query."""

    print("=" * 70)
    print("TESTING RAG SEARCH")
    print("=" * 70)

    query = "Model Context Protocol user interface guide"
    user_id = os.getenv("DEFAULT_USER_ID")

    print(f"\n📝 Query: {query}")
    print(f"👤 User ID: {user_id}")

    # Setup clients
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # First, check if there are any embeddings in the database
    print(f"\n📊 Checking database state...")

    # Check total embeddings
    embeddings_result = supabase.table("embeddings").select("id", count="exact").execute()
    print(f"   Total embeddings in DB: {embeddings_result.count}")

    # Check content with user filter
    content_result = supabase.table("content").select("id, title, url", count="exact").execute()
    print(f"   Total content items: {content_result.count}")

    # Check sources for user
    sources_result = supabase.table("sources").select("id, user_id, identifier").eq("user_id", user_id).execute()
    print(f"   Sources for user {user_id}: {len(sources_result.data)}")
    for source in sources_result.data:
        print(f"      - {source.get('identifier', 'unknown')}")

    # Check content from user's sources
    if sources_result.data:
        source_ids = [s['id'] for s in sources_result.data]
        user_content = supabase.table("content").select("id, title").in_("source_id", source_ids).execute()
        print(f"   Content from user's sources: {len(user_content.data)}")

    # 1. Generate query embedding
    print(f"\n🔍 Generating query embedding...")
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536,
    )
    query_embedding = response.data[0].embedding
    print(f"✓ Generated embedding ({len(query_embedding)} dimensions)")

    # 2. Test WITHOUT user filter first
    print(f"\n" + "=" * 70)
    print(f"TESTING WITHOUT USER FILTER (threshold 0.50)")
    print("=" * 70)

    result = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.50,
            "match_count": 20,
            "filter_user_id": None,
        },
    ).execute()

    results = result.data if result.data else []
    print(f"\n📊 Retrieved {len(results)} chunks")

    # Check if MCP Apps article is in results
    mcp_apps_url = "http://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/"

    for i, chunk in enumerate(results[:10], 1):  # Show first 10
        title = chunk.get('content_title', 'Unknown')
        url = chunk.get('content_url', '')
        similarity = chunk.get('similarity', 0)

        is_mcp_apps = url == mcp_apps_url
        marker = "🎯" if is_mcp_apps else "  "

        print(f"\n{marker} {i}. {title[:60]}")
        print(f"      Similarity: {similarity:.4f}")
        print(f"      URL: {url}")

    # 3. Test WITH user filter
    print(f"\n" + "=" * 70)
    print(f"TESTING WITH USER FILTER (threshold 0.50)")
    print("=" * 70)

    result = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.50,
            "match_count": 20,
            "filter_user_id": user_id,
        },
    ).execute()

    results = result.data if result.data else []
    print(f"\n📊 Retrieved {len(results)} chunks")

    for i, chunk in enumerate(results[:10], 1):
        title = chunk.get('content_title', 'Unknown')
        url = chunk.get('content_url', '')
        similarity = chunk.get('similarity', 0)

        is_mcp_apps = url == mcp_apps_url
        marker = "🎯" if is_mcp_apps else "  "

        print(f"\n{marker} {i}. {title[:60]}")
        print(f"      Similarity: {similarity:.4f}")
        print(f"      URL: {url}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_search())
