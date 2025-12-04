"""
Test that semantic search finds MCP UI content
"""

import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
for env_path in [Path("learning-coach-mcp/.env"), Path("agent/.env"), Path(".env")]:
    if env_path.exists():
        print(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        break


async def test_mcp_search():
    """Test searching for MCP UI content."""
    from agent.research_planner import ResearchPlanner

    planner = ResearchPlanner(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    query = "I want to learn about MCP UI"
    user_id = "00000000-0000-0000-0000-000000000001"

    print(f"\n🔍 Testing search for: '{query}'\n")

    # Test content coverage analysis
    analysis = await planner.analyze_content_coverage(
        query=query,
        user_id=user_id
    )

    print(f"📊 Results:")
    print(f"   DB Results Found: {analysis.db_results_count}")
    print(f"   Needs Web Search: {analysis.needs_web_search}")
    print(f"   Confidence Score: {analysis.confidence_score}")

    if analysis.existing_sources:
        print(f"\n📚 Found Sources:")
        for i, source in enumerate(analysis.existing_sources, 1):
            print(f"   {i}. {source.get('title', 'Untitled')}")
            print(f"      URL: {source.get('url', 'N/A')}")

    if analysis.coverage_gaps:
        print(f"\n❌ Coverage Gaps:")
        for gap in analysis.coverage_gaps:
            print(f"   - {gap.topic}: {gap.reason}")

    # Check if it found content
    if analysis.db_results_count > 0:
        print(f"\n✅ SUCCESS! Found {analysis.db_results_count} results in database")
        print(f"   Semantic search is working correctly!")
        return True
    else:
        print(f"\n❌ FAILED! No results found")
        print(f"   This means MCP UI content is not in the database,")
        print(f"   or semantic search isn't working properly.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_search())
    exit(0 if success else 1)
