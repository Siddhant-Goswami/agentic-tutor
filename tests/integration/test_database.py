"""
Test direct database access to debug embedding search.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
project_root = Path(__file__).parent
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 70)
print("TESTING DIRECT DATABASE ACCESS")
print("=" * 70)

# 1. Try to select from embeddings table directly
print("\n1. Testing direct embeddings table access...")
try:
    result = supabase.table("embeddings").select("id, chunk_sequence, chunk_text").limit(5).execute()
    print(f"✅ Can read embeddings table: {len(result.data)} rows")
    if result.data:
        print(f"   Sample: {result.data[0].get('chunk_text', '')[:100]}...")
except Exception as e:
    print(f"❌ Error reading embeddings: {e}")

# 2. Try to select from content table
print("\n2. Testing content table access...")
try:
    result = supabase.table("content").select("id, title, url").limit(5).execute()
    print(f"✅ Can read content table: {len(result.data)} rows")
    for item in result.data:
        print(f"   - {item.get('title', 'Unknown')}")
except Exception as e:
    print(f"❌ Error reading content: {e}")

# 3. Try to select from sources table
print("\n3. Testing sources table access...")
try:
    result = supabase.table("sources").select("id, identifier, active, user_id").execute()
    print(f"✅ Can read sources table: {len(result.data)} rows")
    for source in result.data:
        print(f"   - {source.get('identifier', 'Unknown')} (active: {source.get('active')}, user: {source.get('user_id')})")
except Exception as e:
    print(f"❌ Error reading sources: {e}")

# 4. Check if embeddings have actual vector data
print("\n4. Checking if embeddings have vector data...")
try:
    # Select one embedding to check if it has a vector
    result = supabase.table("embeddings").select("id, embedding").limit(1).execute()
    if result.data and result.data[0].get('embedding'):
        embedding = result.data[0]['embedding']
        print(f"✅ Embeddings have vector data")
        print(f"   Type: {type(embedding)}")
        print(f"   Length: {len(embedding) if isinstance(embedding, (list, str)) else 'N/A'}")
        if isinstance(embedding, list):
            print(f"   First 5 values: {embedding[:5]}")
    else:
        print(f"❌ Embeddings table has no vector data!")
except Exception as e:
    print(f"❌ Error checking embedding vectors: {e}")

# 5. Test a simple vector operation
print("\n5. Testing vector similarity calculation...")
try:
    # Get one embedding
    result = supabase.table("embeddings").select("id, embedding, chunk_text").limit(1).execute()
    if result.data and result.data[0].get('embedding'):
        test_embedding = result.data[0]['embedding']
        chunk_id = result.data[0]['id']
        chunk_text = result.data[0]['chunk_text'][:100]

        print(f"✅ Got test embedding from chunk: {chunk_text}...")

        # Try to use it in a similarity search against itself (should return similarity ~1.0)
        # This tests if the vector operations work at all
        print(f"\n   Testing self-similarity (should be ~1.0)...")

        # Can't easily test this with Supabase client, would need RPC
        print(f"   (Need to test via RPC function)")

except Exception as e:
    print(f"❌ Error testing vector operations: {e}")

print("\n" + "=" * 70)
print("DIRECT ACCESS TEST COMPLETE")
print("=" * 70)
