"""
Simple test for digest generation workflow.
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_digest_generation():
    """Test that agent can generate digest with simple goal."""
    from agent.controller import AgentController, AgentConfig
    import os

    print("\n" + "=" * 80)
    print("TEST: Direct Digest Generation")
    print("=" * 80 + "\n")

    config = AgentConfig(
        max_iterations=5,  # Should only need 2-3
        llm_model="gpt-4o-mini",
        temperature=0.3
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Test with explicit digest goal
    print("Running agent with goal: 'Generate my daily digest'\n")

    result = await controller.run(
        goal="Generate my daily digest",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    print(f"\nResult status: {result.status}")
    print(f"Iterations: {result.iteration_count}")

    if result.status == "completed":
        print("✅ SUCCESS! Agent completed digest generation")
        if "digest" in result.output or "insights" in result.output:
            print(f"   Output contains digest/insights")
            if "insights" in result.output:
                insights_count = len(result.output.get("insights", []))
                print(f"   Insights generated: {insights_count}")
        else:
            print("⚠️  Output doesn't contain digest")
            print(f"   Output keys: {list(result.output.keys())}")
    elif result.status == "timeout":
        print(f"❌ FAILED: Agent timed out after {result.iteration_count} iterations")
    else:
        print(f"❌ FAILED: Agent status is {result.status}")

    print("\n" + "=" * 80)

    # Print last few log entries
    if result.logs:
        print("\nLast 5 agent log entries:")
        for log in result.logs[-5:]:
            print(f"  [{log.get('phase', 'N/A')}] {log.get('data', {})}")

    return result.status == "completed"


if __name__ == "__main__":
    success = asyncio.run(test_digest_generation())
    sys.exit(0 if success else 1)
