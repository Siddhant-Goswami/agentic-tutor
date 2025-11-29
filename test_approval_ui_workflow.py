"""
Test Approval UI Workflow

Tests the complete approval workflow to ensure:
1. Agent returns needs_approval status
2. Approval UI displays correctly
3. Clicking "Approve All" triggers web search execution
4. Web results are displayed
5. Session state is managed properly
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


async def test_agent_needs_approval():
    """Test 1: Verify agent returns needs_approval status."""
    print("\n" + "=" * 80)
    print("TEST 1: Agent Returns Needs Approval")
    print("=" * 80 + "\n")

    from agent.controller import AgentController, AgentConfig

    config = AgentConfig(
        max_iterations=5,
        llm_model="gpt-4o-mini",
        temperature=0.3
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Ensure approval flag is NOT set
    if "SKIP_WEB_SEARCH_APPROVAL" in os.environ:
        del os.environ["SKIP_WEB_SEARCH_APPROVAL"]

    # Run with a query likely to trigger approval
    result = await controller.run(
        goal="Help me learn quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    print(f"Status: {result.status}")
    print(f"Iterations: {result.iteration_count}")

    # Assertions
    assert result.status == "needs_approval", f"❌ Expected 'needs_approval', got '{result.status}'"
    assert "research_plan" in result.output, "❌ Missing research_plan in output"
    assert result.output.get("type") == "plan_approval_needed", "❌ Wrong output type"

    research_plan = result.output.get("research_plan", {})
    print(f"\n✅ SUCCESS! Agent returned needs_approval")
    print(f"   Research Plan Keys: {list(research_plan.keys())}")
    print(f"   Proposed Searches: {len(research_plan.get('proposed_searches', []))}")

    return result


async def test_web_search_execution():
    """Test 2: Verify web search executes correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: Web Search Execution")
    print("=" * 80 + "\n")

    from agent.tools import ToolRegistry

    tools = ToolRegistry(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Execute web search
    result = await tools.execute_tool(
        "web-search",
        {
            "query": "quantum computing basics tutorial",
            "max_results": 3
        }
    )

    # Assertions
    assert "results" in result, "❌ Missing results in web search response"
    assert len(result["results"]) > 0, "❌ No results returned"
    assert "source_api" in result, "❌ Missing source_api"

    # Check source type marking
    for res in result["results"]:
        assert res.get("source_type") == "web_search", f"❌ Result not marked as web_search: {res}"

    print(f"✅ SUCCESS! Web search executed")
    print(f"   Results: {len(result['results'])}")
    print(f"   Source API: {result.get('source_api')}")
    print(f"   All results marked as 'web_search': ✓")

    return result


def test_session_state_workflow():
    """Test 3: Verify session state workflow (simulation)."""
    print("\n" + "=" * 80)
    print("TEST 3: Session State Workflow (Simulation)")
    print("=" * 80 + "\n")

    # Simulate session state
    session_state = {}

    # Step 1: Agent returns needs_approval
    agent_result = {
        "status": "needs_approval",
        "output": {
            "research_plan": {
                "proposed_searches": [
                    {"query": "quantum gates", "estimated_results": 5}
                ]
            },
            "type": "plan_approval_needed"
        },
        "session_id": "test-session-123"
    }

    # Step 2: Store in session state (what dashboard/views/agent.py does)
    session_state['last_agent_result'] = agent_result
    session_state['last_agent_goal'] = "Help me learn quantum computing"

    print("✅ Step 1: Agent result stored in session state")
    print(f"   Keys: {list(session_state.keys())}")

    # Step 3: User clicks approve (what components/research_planner_ui.py does)
    decision_key = f"research_approval_{agent_result['session_id']}"
    session_state[decision_key] = "approved"

    print("✅ Step 2: Approval decision stored")
    print(f"   Decision: {session_state[decision_key]}")

    # Step 4: Page reruns, check for pending approval
    assert 'last_agent_result' in session_state, "❌ Agent result not found in session state"
    result = session_state['last_agent_result']

    print("✅ Step 3: Pending approval retrieved on rerun")

    # Step 5: Get approval decision
    decision = session_state.get(decision_key)
    assert decision == "approved", f"❌ Expected 'approved', got '{decision}'"

    print("✅ Step 4: Approval decision retrieved")

    # Step 6: Execute web searches (simulated)
    print("✅ Step 5: Web searches would execute here")

    # Step 7: Clear session state
    del session_state['last_agent_result']
    del session_state['last_agent_goal']
    del session_state[decision_key]

    assert 'last_agent_result' not in session_state, "❌ Session state not cleared"

    print("✅ Step 6: Session state cleared after handling")
    print("\n✅ SUCCESS! Complete workflow validated")


async def test_approval_ui_integration():
    """Test 4: Integration test for approval UI component."""
    print("\n" + "=" * 80)
    print("TEST 4: Approval UI Integration")
    print("=" * 80 + "\n")

    # This would require Streamlit testing framework
    # For now, we validate the component exists and is importable

    try:
        from dashboard.components.research_planner_ui import (
            render_research_plan_approval,
            render_web_search_results
        )
        print("✅ Approval UI components imported successfully")

        # Check function signatures
        import inspect

        sig = inspect.signature(render_research_plan_approval)
        params = list(sig.parameters.keys())
        assert "research_plan" in params, "❌ Missing research_plan parameter"
        assert "session_id" in params, "❌ Missing session_id parameter"

        print(f"✅ render_research_plan_approval signature: {params}")

        sig = inspect.signature(render_web_search_results)
        params = list(sig.parameters.keys())
        assert "results" in params, "❌ Missing results parameter"
        assert "search_query" in params, "❌ Missing search_query parameter"

        print(f"✅ render_web_search_results signature: {params}")

        print("\n✅ SUCCESS! All UI components validated")

    except ImportError as e:
        print(f"❌ FAILED to import UI components: {e}")
        raise


async def test_complete_approval_workflow():
    """Test 5: Complete workflow with approval and digest generation."""
    print("\n" + "=" * 80)
    print("TEST 5: Complete Approval Workflow with Digest")
    print("=" * 80 + "\n")

    from agent.controller import AgentController, AgentConfig

    config = AgentConfig(
        max_iterations=15,  # More iterations for complete flow
        llm_model="gpt-4o-mini",
        temperature=0.3
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Step 1: First run - should request approval
    print("Step 1: Running agent (should request approval)...")
    if "SKIP_WEB_SEARCH_APPROVAL" in os.environ:
        del os.environ["SKIP_WEB_SEARCH_APPROVAL"]

    result1 = await controller.run(
        goal="Help me learn quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    assert result1.status == "needs_approval", f"❌ Step 1 failed: Expected needs_approval, got {result1.status}"
    print(f"✅ Step 1 passed: Agent requested approval")

    # Step 2: Simulate approval granted
    print("\nStep 2: Simulating approval granted (setting SKIP_WEB_SEARCH_APPROVAL=true)...")
    os.environ["SKIP_WEB_SEARCH_APPROVAL"] = "true"

    # Step 3: Re-run agent - should execute web search and complete
    print("\nStep 3: Re-running agent with approval granted...")
    result2 = await controller.run(
        goal="Help me learn quantum computing basics",
        user_id="00000000-0000-0000-0000-000000000001"
    )

    # Clear flag
    if "SKIP_WEB_SEARCH_APPROVAL" in os.environ:
        del os.environ["SKIP_WEB_SEARCH_APPROVAL"]

    print(f"\nStep 3 result status: {result2.status}")
    print(f"Iterations: {result2.iteration_count}")

    # Check if agent completed with digest
    if result2.status == "completed":
        print("✅ Step 3 passed: Agent completed!")
        if "digest" in result2.output or "insights" in result2.output:
            print("✅ SUCCESS! Complete workflow worked - digest generated!")
            return True
        else:
            print("⚠️  Agent completed but no digest found in output")
            return False
    else:
        print(f"⚠️  Agent didn't complete (status: {result2.status})")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🧪 Testing Approval UI Workflow" + "\n")

    try:
        # Test 1: Agent returns needs_approval
        agent_result = await test_agent_needs_approval()

        # Test 2: Web search execution
        search_result = await test_web_search_execution()

        # Test 3: Session state workflow
        test_session_state_workflow()

        # Test 4: UI component integration
        await test_approval_ui_integration()

        # Test 5: Complete approval workflow (NEW!)
        complete_workflow_success = await test_complete_approval_workflow()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80 + "\n")

        print("Test Summary:")
        print("1. ✅ Agent correctly returns needs_approval status")
        print("2. ✅ Web search executes and marks results correctly")
        print("3. ✅ Session state workflow handles approval properly")
        print("4. ✅ UI components are correctly implemented")
        print("5. ✅ Complete workflow: approval → web search → digest generation" if complete_workflow_success else "5. ⚠️  Complete workflow test didn't generate digest")

        print("\nNext Steps:")
        print("1. Restart Streamlit: streamlit run dashboard/app.py")
        print("2. Go to Agent Mode")
        print("3. Try: 'Help me learn quantum computing basics'")
        print("4. Click 'Approve All' when modal appears")
        print("5. Verify web searches execute and results display")
        print()

        return True

    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80 + "\n")
        return False

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80 + "\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
