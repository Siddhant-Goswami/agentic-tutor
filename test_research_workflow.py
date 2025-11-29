"""
Test Research Workflow

Tests the complete workflow:
1. Analyze content coverage
2. Create research plan
3. Show approval workflow
"""

import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
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


async def test_content_coverage():
    """Test content coverage analysis."""
    print("\n" + "="*80)
    print("TEST 1: Content Coverage Analysis")
    print("="*80 + "\n")

    from agent.tools import ToolRegistry

    tools = ToolRegistry(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Analyze coverage for a topic likely not in DB
    result = await tools.execute_tool(
        "analyze-content-coverage",
        {
            "query": "quantum computing basics",
            "user_id": "00000000-0000-0000-0000-000000000001"
        }
    )

    print(f"Query: 'quantum computing basics'")
    print(f"\nDatabase Results: {result.get('db_results_count')}")
    print(f"Needs Web Search: {result.get('needs_web_search')}")
    print(f"Confidence Score: {result.get('confidence_score')}")

    coverage_gaps = result.get('coverage_gaps', [])
    if coverage_gaps:
        print(f"\nCoverage Gaps ({len(coverage_gaps)}):")
        for gap in coverage_gaps:
            print(f"  - {gap.get('topic')}: {gap.get('reason')}")
            print(f"    Suggested query: {gap.get('suggested_query')}")

    if result.get('needs_web_search'):
        print("\n✅ Web search is recommended!")
    else:
        print("\n✅ Database has sufficient content")

    return result


async def test_research_plan():
    """Test research plan creation."""
    print("\n" + "="*80)
    print("TEST 2: Research Plan Creation")
    print("="*80 + "\n")

    from agent.research_planner import ResearchPlanner

    planner = ResearchPlanner(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Analyze content
    analysis = await planner.analyze_content_coverage(
        query="quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    print(f"Database Results: {analysis.db_results_count}")
    print(f"Needs Web Search: {analysis.needs_web_search}")

    if analysis.needs_web_search:
        # Create research plan
        plan = await planner.create_research_plan(
            content_analysis=analysis,
            user_context={"difficulty": "intermediate"}
        )

        print(f"\n📋 Research Plan Created:")
        print(f"   Total Searches: {plan.estimated_total_searches}")
        print(f"   API Credits: {plan.estimated_api_credits}")
        print(f"\nProposed Searches:")
        for i, query in enumerate(plan.search_queries, 1):
            print(f"   {i}. {query.query}")
            print(f"      Rationale: {query.rationale}")
            print(f"      Priority: {query.priority}")

        print(f"\nRationale: {plan.rationale}")

        return plan
    else:
        print("\n✅ No research plan needed - database has enough content")
        return None


async def test_agent_workflow():
    """Test the complete agent workflow."""
    print("\n" + "="*80)
    print("TEST 3: Agent Workflow (Simulated)")
    print("="*80 + "\n")

    from agent.controller import AgentController, AgentConfig

    config = AgentConfig(
        max_iterations=5,
        llm_model="gpt-4o-mini"
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Run agent with a query likely to trigger web search
    print("Running agent with query: 'Help me learn quantum computing basics'\n")

    result = await controller.run(
        goal="Help me learn quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    print(f"Status: {result.status}")
    print(f"Iterations: {result.iteration_count}")

    if result.status == "needs_approval":
        print("\n✅ SUCCESS! Agent requested approval for web search")
        print(f"\nResearch Plan:")
        research_plan = result.output.get('research_plan', {})
        print(f"  DB Results: {research_plan.get('db_results', {}).get('count', 0)}")
        print(f"  Gaps: {research_plan.get('coverage_gaps', [])}")
        print(f"  Proposed Searches: {len(research_plan.get('proposed_searches', []))}")
    elif result.status == "completed":
        print("\n✅ Agent completed (may have used DB-only content)")
    else:
        print(f"\n⚠️  Unexpected status: {result.status}")

    # Show logs
    print(f"\n📝 Agent Logs ({len(result.logs)} entries):")
    for log in result.logs[:5]:  # Show first 5
        print(f"  [{log.get('phase')}] {log.get('content', {}).get('message', '')[:80]}")

    return result


async def main():
    """Run all tests."""
    print("\n" + "🧪 Testing Research Workflow" + "\n")

    # Test 1: Content Coverage
    await test_content_coverage()

    # Test 2: Research Plan
    await test_research_plan()

    # Test 3: Full Agent Workflow
    await test_agent_workflow()

    print("\n" + "="*80)
    print("✅ All tests complete!")
    print("="*80 + "\n")

    print("Next steps:")
    print("1. Restart your Streamlit app: Press Ctrl+C and run 'streamlit run dashboard/app.py' again")
    print("2. Go to Agent Mode in the dashboard")
    print("3. Try: 'Help me learn quantum computing basics'")
    print("4. You should see the approval modal appear!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
