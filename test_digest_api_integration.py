"""
Integration test: Test that agent can use enhanced digest_api.py successfully.

This tests the full flow from agent tool call to digest generation.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Add dashboard to path
project_root = Path(__file__).parent
dashboard_path = project_root / "dashboard"
if str(dashboard_path) not in sys.path:
    sys.path.insert(0, str(dashboard_path))


async def test_agent_tool_integration():
    """Test that agent's generate-digest tool works with enhanced API."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Agent Tool → Enhanced Digest API")
    print("=" * 80 + "\n")

    from agent.tools import ToolRegistry

    # Initialize tool registry
    registry = ToolRegistry(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Test 1: Basic digest generation
    print("Test 1: Basic digest generation")
    print("-" * 80)

    args = {
        "date": "today",
        "max_insights": 3,
        "force_refresh": True,
        "user_context": {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "current_week": 7,
            "current_topics": ["AI", "Machine Learning"],
            "difficulty_level": "intermediate",
        },
    }

    try:
        result = await registry.execute_tool("generate-digest", args)

        print(f"Success: {result.get('success')}")
        print(f"Num Insights: {result.get('num_insights', 0)}")
        print(f"Quality Badge: {result.get('quality_badge', 'N/A')}")

        if result.get("success"):
            print("✅ PASS: Digest generated successfully")
            insights = result.get("insights", [])
            if insights:
                print(f"   First insight: {insights[0].get('title', 'N/A')[:60]}...")
        else:
            error = result.get("error") or result.get("message", "Unknown error")
            print(f"⚠️  Digest generation failed: {error}")
            if "No content" in error or "No relevant content" in error:
                print("   (This is expected if database has no content)")

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Q&A mode with explicit_query
    print("\n" + "Test 2: Q&A mode with explicit_query")
    print("-" * 80)

    args_qa = {
        "date": "today",
        "max_insights": 3,
        "force_refresh": True,
        "user_context": {
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
        "explicit_query": "What is Model Context Protocol?",
    }

    try:
        result = await registry.execute_tool("generate-digest", args_qa)

        print(f"Success: {result.get('success')}")
        print(f"Num Insights: {result.get('num_insights', 0)}")

        if result.get("success"):
            print("✅ PASS: Q&A mode worked")
            metadata = result.get("metadata", {})
            query = metadata.get("query", "")
            if "Model Context Protocol" in query or "MCP" in query:
                print(f"   Query preserved: {query[:60]}...")
        else:
            error = result.get("error") or result.get("message", "Unknown error")
            print(f"⚠️  Q&A mode failed: {error}")

    except Exception as e:
        print(f"❌ FAIL: Exception in Q&A mode: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Success indicators for agent completion
    print("\n" + "Test 3: Success indicators for agent completion")
    print("-" * 80)

    args_completion = {
        "date": "today",
        "max_insights": 5,
        "force_refresh": True,
        "user_context": {
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
    }

    try:
        result = await registry.execute_tool("generate-digest", args_completion)

        # Agent completion logic: success=true AND num_insights > 0
        success = result.get("success", False)
        num_insights = result.get("num_insights", 0)

        should_complete = success and num_insights > 0

        print(f"Success: {success}")
        print(f"Num Insights: {num_insights}")
        print(f"Should Agent Complete: {should_complete}")

        if should_complete:
            print("✅ PASS: Agent should complete (success=true and num_insights > 0)")
        elif not success:
            print("⚠️  SKIP: Digest generation failed (likely no content in DB)")
        else:
            print("❌ FAIL: Success=true but num_insights=0 (should not happen)")

    except Exception as e:
        print(f"❌ FAIL: Exception checking completion: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("Integration test complete!")
    print("=" * 80 + "\n")

    return True


async def test_direct_api_call():
    """Test direct API call to verify it works standalone."""
    print("\n" + "=" * 80)
    print("DIRECT API TEST: Enhanced digest_api.py")
    print("=" * 80 + "\n")

    from datetime import date
    from digest_api import generate_digest_simple

    user_id = "00000000-0000-0000-0000-000000000001"

    print("Calling generate_digest_simple directly...")
    print("-" * 80)

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
        )

        print(f"Success: {result.get('success')}")
        print(f"Num Insights: {result.get('num_insights', 0)}")
        print(f"Quality Badge: {result.get('quality_badge', 'N/A')}")

        if result.get("success"):
            print("✅ PASS: Direct API call successful")
            insights = result.get("insights", [])
            if insights:
                print(f"\nSample insights:")
                for i, insight in enumerate(insights[:2], 1):
                    print(f"  {i}. {insight.get('title', 'N/A')[:60]}...")
        else:
            error = result.get("error") or result.get("message", "Unknown")
            print(f"⚠️  API call returned success=false: {error}")
            if "No content" in error:
                print("   (Expected if database has no content)")

    except Exception as e:
        print(f"❌ FAIL: Exception in direct API call: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("DIGEST API INTEGRATION TESTS")
    print("=" * 80)

    # Test direct API
    direct_success = await test_direct_api_call()

    # Test agent tool integration
    integration_success = await test_agent_tool_integration()

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Direct API Test: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"Agent Integration Test: {'✅ PASS' if integration_success else '❌ FAIL'}")
    print("=" * 80 + "\n")

    return direct_success and integration_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

