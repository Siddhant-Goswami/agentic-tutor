"""
Test script for Agentic Learning Coach

Runs the agent with a test goal and displays results.
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
project_root = Path(__file__).parent

sys.path.insert(0, str(project_root))

# Load environment
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Import agent components
from src.agent.controllers.agent_controller import AgentController
from src.agent.models.agent_config import AgentConfig
from src.agent.utils.logger import AgentLogger


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_log_entry(log):
    """Print a single log entry."""
    phase = log.get("phase", "UNKNOWN")
    timestamp = log.get("timestamp", "")
    content = log.get("content", {})

    # Phase emojis
    emojis = {
        "SENSE": "🔵",
        "PLAN": "🟡",
        "ACT": "🟢",
        "OBSERVE": "🟣",
        "REFLECT": "🟠",
        "COMPLETE": "✅",
        "ERROR": "❌",
    }

    emoji = emojis.get(phase, "⚪")

    print(f"\n{emoji} [{phase}] {timestamp}")
    print("-" * 70)

    # Print content based on phase
    if phase == "SENSE":
        user_context = content.get("user_context", {})
        print(f"  Week: {user_context.get('week', 'N/A')}")
        print(f"  Topics: {user_context.get('topics', [])}")
        print(f"  Difficulty: {user_context.get('difficulty', 'N/A')}")

    elif phase == "PLAN":
        plan = content.get("plan", {})
        print(f"  Action: {plan.get('action_type', 'N/A')}")
        print(f"  Tool: {plan.get('tool', 'N/A')}")
        print(f"  Reasoning: {plan.get('reasoning', 'N/A')}")

    elif phase == "ACT":
        print(f"  Tool: {content.get('tool', 'N/A')}")
        print(f"  Result Preview: {content.get('result_preview', 'N/A')[:100]}...")

    elif phase == "OBSERVE":
        print(f"  Status: {content.get('status', 'N/A')}")
        if "error" in content:
            print(f"  Error: {content['error']}")

    elif phase == "REFLECT":
        print(f"  Reflection: {content.get('reflection', 'N/A')}")

    elif phase == "COMPLETE":
        print(f"  Status: {content.get('status', 'completed')}")
        if "reasoning" in content:
            print(f"  Reasoning: {content['reasoning']}")


async def test_agent(goal: str):
    """
    Test the agent with a given goal.

    Args:
        goal: Natural language goal for the agent
    """
    print_header("AGENTIC LEARNING COACH TEST")

    print(f"\n📝 Goal: {goal}")
    print(f"🔧 Model: {os.getenv('AGENT_LLM_MODEL', 'gpt-4o-mini')}")
    print(f"🔁 Max Iterations: {os.getenv('AGENT_MAX_ITERATIONS', '10')}")

    # Create agent config
    config = AgentConfig(
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        llm_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )

    # Initialize controller
    print("\n🤖 Initializing Agent Controller...")
    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Run agent
    print_header("AGENT EXECUTION")
    print("\n🚀 Starting agent execution...\n")

    try:
        result = await controller.run(
            goal=goal,
            user_id=os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
        )

        print_header("EXECUTION LOGS")

        # Print all logs
        for log in result.logs:
            print_log_entry(log)

        print_header("EXECUTION SUMMARY")

        print(f"\n✅ Status: {result.status}")
        print(f"🔁 Iterations: {result.iteration_count}")
        print(f"📝 Log Entries: {len(result.logs)}")
        print(f"🆔 Session ID: {result.session_id}")

        print_header("AGENT OUTPUT")

        output = result.output

        # Check for different output types
        if "error" in output:
            print(f"\n❌ Error: {output['error']}")

        elif "question" in output:
            print(f"\n❓ Clarification Needed: {output['question']}")

        elif "digest" in output or "insights" in output:
            digest = output.get("digest", output)
            insights = digest.get("insights", [])
            print(f"\n📚 Generated {len(insights)} insights")

            if "ragas_scores" in digest:
                scores = digest["ragas_scores"]
                print(f"⭐ Quality Score: {scores.get('average', 0):.2%}")

            # Show first insight
            if insights:
                print(f"\n💡 First Insight:")
                print(f"   Title: {insights[0].get('title', 'Untitled')}")
                print(f"   Content: {insights[0].get('content', '')[:200]}...")
        else:
            print(f"\n📋 Output:")
            print(f"   {output}")

        print_header("TEST COMPLETE")
        print("\n✅ Agent test completed successfully!\n")

        return result

    except Exception as e:
        print_header("ERROR")
        print(f"\n❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""

    # Test goals
    test_goals = [
        "Get my current learning context",
        # "Generate my daily digest",
        # "Help me learn about attention mechanisms",
    ]

    for i, goal in enumerate(test_goals, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(test_goals)}")
        print(f"{'='*70}")

        result = await test_agent(goal)

        if result:
            print(f"\n✅ Test {i} passed!")
        else:
            print(f"\n❌ Test {i} failed!")
            break

        # Wait a bit between tests
        if i < len(test_goals):
            print("\n⏳ Waiting 2 seconds before next test...\n")
            await asyncio.sleep(2)

    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
