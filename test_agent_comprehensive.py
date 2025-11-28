"""
Comprehensive test for the standalone agent module.
Tests multiple scenarios to verify agent separation from MCP.
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

# Import agent components (should work without MCP)
from agent.controller import AgentController, AgentConfig
from agent.logger import AgentLogger


def print_separator(char="=", length=70):
    print(f"\n{char * length}")


def print_header(text):
    print_separator("=")
    print(f"  {text}")
    print_separator("=")


async def test_scenario(scenario_name: str, goal: str):
    """Test a specific scenario."""
    print_header(f"TEST: {scenario_name}")
    print(f"\n📝 Goal: {goal}")

    # Create agent config
    config = AgentConfig(
        max_iterations=10,
        llm_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )

    # Initialize controller
    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Run agent
    print("\n🚀 Running agent...\n")

    try:
        result = await controller.run(
            goal=goal,
            user_id=os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
        )

        # Print summary
        print_separator("-")
        print(f"✅ Status: {result.status}")
        print(f"🔁 Iterations: {result.iteration_count}")
        print(f"📝 Log Entries: {len(result.logs)}")

        # Print logs
        print_separator("-")
        print("AGENT REASONING:")
        for log in result.logs:
            phase = log.get("phase", "UNKNOWN")
            print(f"\n  [{phase}]")

            content = log.get("content", {})
            if phase == "PLAN":
                plan = content.get("plan", {})
                print(f"    Action: {plan.get('action_type')}")
                print(f"    Reasoning: {plan.get('reasoning', 'N/A')[:100]}...")
            elif phase == "REFLECT":
                reflection = content.get("reflection", "")
                print(f"    {reflection[:150]}...")

        print_separator("=")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print_separator("=")
        return False


async def main():
    """Run comprehensive tests."""

    print_header("COMPREHENSIVE AGENT TEST SUITE")
    print("\nTesting standalone agent module (no MCP dependency)")

    test_scenarios = [
        ("Get User Context", "Get my current learning context"),
        ("Search Content", "Find articles about attention mechanisms"),
        ("Generate Digest", "Generate my daily learning digest"),
    ]

    results = []

    for i, (name, goal) in enumerate(test_scenarios, 1):
        print(f"\n\n{'='*70}")
        print(f"SCENARIO {i}/{len(test_scenarios)}")
        print(f"{'='*70}")

        success = await test_scenario(name, goal)
        results.append((name, success))

        if i < len(test_scenarios):
            print("\n⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)

    # Final summary
    print_header("TEST SUMMARY")

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {name}")

    total_passed = sum(1 for _, success in results if success)
    print(f"\n  Total: {total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠️  {len(results) - total_passed} test(s) failed")

    print_separator("=")


if __name__ == "__main__":
    asyncio.run(main())
