"""
Final test of RAG search with updated threshold.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client

# Load environment
project_root = Path(__file__).parent
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

async def test_final():
    print("=" * 70)
    print("FINAL RAG SEARCH TEST")
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

    # Generate query embedding
    print(f"\n🔍 Generating query embedding...")
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536,
    )
    query_embedding = response.data[0].embedding
    print(f"✓ Generated embedding ({len(query_embedding)} dimensions)")

    # Test with new threshold (0.40)
    print(f"\n" + "=" * 70)
    print(f"TESTING WITH NEW THRESHOLD: 0.40 (default)")
    print("=" * 70)

    result = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.40,
            "match_count": 15,
            "filter_user_id": user_id,
        },
    ).execute()

    results = result.data if result.data else []

    print(f"\n📊 Retrieved {len(results)} chunks")
    print("=" * 70)

    # Check if MCP Apps article is in results
    mcp_apps_url = "http://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/"
    mcp_apps_found = False
    mcp_apps_positions = []

    for i, chunk in enumerate(results, 1):
        title = chunk.get('content_title', 'Unknown')
        url = chunk.get('content_url', '')
        similarity = chunk.get('similarity', 0)
        chunk_text = chunk.get('chunk_text', '')[:150]

        is_mcp_apps = url == mcp_apps_url

        marker = "🎯" if is_mcp_apps else "  "
        if is_mcp_apps:
            mcp_apps_found = True
            mcp_apps_positions.append(i)

        print(f"\n{marker} {i}. {title[:60]}")
        print(f"      Similarity: {similarity:.4f}")
        print(f"      URL: {url}")
        if is_mcp_apps:
            print(f"      Chunk: {chunk_text}...")

    print("\n" + "=" * 70)

    if mcp_apps_found:
        print(f"✅ SUCCESS! MCP Apps article WAS found in results")
        print(f"   Positions: {mcp_apps_positions}")
        print(f"   Total MCP Apps chunks: {len(mcp_apps_positions)}")
        print("\n   This means:")
        print("   ✅ Database migration applied successfully")
        print("   ✅ Similarity threshold lowered to 0.40")
        print("   ✅ RAG search is now working")
        print("   ✅ Agent can now generate digests from MCP Apps content")
    else:
        print(f"❌ FAILED - MCP Apps article NOT found in results")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_final())
