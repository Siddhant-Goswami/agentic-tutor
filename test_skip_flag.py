"""
Quick test to verify SKIP_WEB_SEARCH_APPROVAL flag is working
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


async def test_skip_flag():
    """Test if SKIP flag prevents approval request."""
    from agent.controller import AgentController, AgentConfig

    # Set the skip flag BEFORE running agent
    os.environ["SKIP_WEB_SEARCH_APPROVAL"] = "true"

    config = AgentConfig(
        max_iterations=10,
        llm_model="gpt-4o-mini",
        temperature=0.3
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("\n🧪 Testing with SKIP_WEB_SEARCH_APPROVAL=true")
    print("Expected: Agent should call web-search directly, NOT request approval\n")

    result = await controller.run(
        goal="Help me learn quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    # Clear flag
    if "SKIP_WEB_SEARCH_APPROVAL" in os.environ:
        del os.environ["SKIP_WEB_SEARCH_APPROVAL"]

    print(f"\n📊 Result:")
    print(f"   Status: {result.status}")
    print(f"   Iterations: {result.iteration_count}")
    print(f"   Output keys: {list(result.output.keys())}")

    # Check logs for PLAN_APPROVAL vs web-search
    print(f"\n📝 Agent actions taken:")
    for log in result.logs:
        if log.get("phase") == "ACT":
            content = log.get("content", {})
            tool = content.get("tool", "N/A")
            print(f"   - {tool}")

    # Analyze result
    if result.status == "needs_approval":
        print("\n❌ FAILED: Agent still requested approval despite SKIP flag!")
        print("   The environment variable is not being checked properly.")
        return False
    elif result.status == "completed":
        print("\n✅ SUCCESS: Agent completed without requesting approval!")
        return True
    elif result.status == "timeout":
        print("\n⚠️  TIMEOUT: Agent reached max iterations")
        print("   This might mean the agent is working but needs more iterations.")
        return False
    else:
        print(f"\n❓ UNEXPECTED: Status = {result.status}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_skip_flag())
    exit(0 if success else 1)
