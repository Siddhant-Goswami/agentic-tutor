"""
Test if match_embeddings RPC function is working.
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

async def test_rpc():
    print("=" * 70)
    print("TESTING match_embeddings RPC FUNCTION")
    print("=" * 70)

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Generate a query embedding
    query = "Model Context Protocol user interface"
    print(f"\n📝 Query: {query}")

    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536,
    )
    query_embedding = response.data[0].embedding

    print(f"✅ Generated embedding: {len(query_embedding)} dimensions")
    print(f"   First 5 values: {query_embedding[:5]}")
    print(f"   Type: {type(query_embedding)}")

    # Test 1: Call RPC with very low threshold
    print(f"\n" + "=" * 70)
    print("TEST 1: Call with threshold 0.0 (should return everything)")
    print("=" * 70)

    try:
        result = supabase.rpc(
            "match_embeddings",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,  # Very low threshold
                "match_count": 50,
                "filter_user_id": None,  # No filtering
            },
        ).execute()

        print(f"✅ RPC call succeeded")
        print(f"📊 Results: {len(result.data) if result.data else 0} chunks")

        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                print(f"\n   {i}. {chunk.get('content_title', 'Unknown')[:60]}")
                print(f"      Similarity: {chunk.get('similarity', 0):.4f}")
                print(f"      URL: {chunk.get('content_url', '')}")
        else:
            print("\n❌ No results returned!")
            print("   This suggests either:")
            print("   1. Migration wasn't applied (function still has RLS issue)")
            print("   2. Embedding format is incompatible")
            print("   3. No active sources in database")

    except Exception as e:
        print(f"❌ RPC call failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Try with string format embedding
    print(f"\n" + "=" * 70)
    print("TEST 2: Try with embedding as string (PostgreSQL array format)")
    print("=" * 70)

    try:
        # Convert to PostgreSQL array string format
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        print(f"   Format: string array, length: {len(embedding_str)}")

        result = supabase.rpc(
            "match_embeddings",
            {
                "query_embedding": embedding_str,
                "match_threshold": 0.0,
                "match_count": 50,
                "filter_user_id": None,
            },
        ).execute()

        print(f"✅ RPC call with string format succeeded")
        print(f"📊 Results: {len(result.data) if result.data else 0} chunks")

        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                print(f"\n   {i}. {chunk.get('content_title', 'Unknown')[:60]}")
                print(f"      Similarity: {chunk.get('similarity', 0):.4f}")

    except Exception as e:
        print(f"❌ RPC call with string format failed: {e}")

    # Test 3: Check if we can get an embedding from DB and use it
    print(f"\n" + "=" * 70)
    print("TEST 3: Use an existing embedding from database")
    print("=" * 70)

    try:
        # Get an embedding from the database
        db_result = supabase.table("embeddings").select("embedding, chunk_text").limit(1).execute()

        if db_result.data:
            db_embedding_str = db_result.data[0]['embedding']
            chunk_text = db_result.data[0]['chunk_text'][:100]

            print(f"✅ Got embedding from DB")
            print(f"   Chunk: {chunk_text}...")
            print(f"   Embedding type: {type(db_embedding_str)}")
            print(f"   Embedding length: {len(db_embedding_str)}")

            # Try to search with this embedding (should find itself with similarity ~1.0)
            print(f"\n   Searching with this embedding (should find itself)...")

            # Parse the string embedding
            if isinstance(db_embedding_str, str):
                # It's already in string format, try using it directly
                result = supabase.rpc(
                    "match_embeddings",
                    {
                        "query_embedding": db_embedding_str,
                        "match_threshold": 0.0,
                        "match_count": 10,
                        "filter_user_id": None,
                    },
                ).execute()

                print(f"   Results: {len(result.data) if result.data else 0} chunks")

                if result.data:
                    print(f"   ✅ Found {len(result.data)} matches!")
                    print(f"   Top match similarity: {result.data[0].get('similarity', 0):.4f}")

    except Exception as e:
        print(f"❌ Test with DB embedding failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("RPC FUNCTION TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_rpc())
