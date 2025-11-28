"""
Run content ingestion with full article extraction.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
project_root = Path(__file__).parent
learning_coach_path = project_root / "learning-coach-mcp"
src_path = learning_coach_path / "src"

sys.path.insert(0, str(src_path))

# Load environment
env_path = learning_coach_path / ".env"
load_dotenv(env_path)

# Import after path setup
from ingestion.orchestrator import IngestionOrchestrator


async def main():
    """Run ingestion with full content extraction."""

    print("=" * 70)
    print("CONTENT INGESTION WITH FULL ARTICLE EXTRACTION")
    print("=" * 70)

    print("\n🔧 Configuration:")
    print(f"   Fetch full content: YES")
    print(f"   Chunk size: 750 tokens")
    print(f"   Overlap: 100 tokens")

    # Initialize orchestrator with full content fetching enabled
    orchestrator = IngestionOrchestrator(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        fetch_full_content=True,  # Enable full content extraction
    )

    print("\n🚀 Starting ingestion...")

    # Run ingestion for all active sources
    stats = await orchestrator.ingest_all_active_sources(
        user_id=os.getenv("DEFAULT_USER_ID")
    )

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)

    print(f"\n📊 Statistics:")
    print(f"   Sources processed: {stats.get('sources_processed', 0)}")
    print(f"   Sources failed: {stats.get('sources_failed', 0)}")
    print(f"   Articles processed: {stats.get('total_articles', 0)}")
    print(f"   Total chunks: {stats.get('total_chunks', 0)}")

    if stats.get('total_articles', 0) > 0:
        avg_chunks = stats.get('total_chunks', 0) / stats.get('total_articles', 1)
        print(f"   Average chunks per article: {avg_chunks:.1f}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
