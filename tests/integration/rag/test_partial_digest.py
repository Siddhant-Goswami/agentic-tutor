"""
Test partial digest generation when agent reaches max iterations.
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import json

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Import agent components
from agent.controller import AgentController, AgentConfig


async def test_partial_digest():
    """Test that agent generates partial digest when hitting max iterations."""

    print("=" * 70)
    print("  TESTING PARTIAL DIGEST GENERATION")
    print("=" * 70)

    # Create agent with low max iterations to trigger timeout
    config = AgentConfig(
        max_iterations=3,  # Low limit to trigger timeout
        llm_model="gpt-4o-mini",
        temperature=0.3,
    )

    controller = AgentController(
        config=config,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Run agent with a goal that will likely timeout
    goal = "Generate my daily learning digest with articles about transformers"

    print(f"\n📝 Goal: {goal}")
    print(f"🔁 Max Iterations: {config.max_iterations}")
    print("\n🚀 Running agent...\n")

    result = await controller.run(
        goal=goal,
        user_id=os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
    )

    print("=" * 70)
    print("  RESULT")
    print("=" * 70)

    print(f"\nStatus: {result.status}")
    print(f"Iterations: {result.iteration_count}")

    print("\n" + "=" * 70)
    print("  OUTPUT")
    print("=" * 70)

    output = result.output
    print(f"\n{json.dumps(output, indent=2)}")

    # Verify partial result structure
    print("\n" + "=" * 70)
    print("  VERIFICATION")
    print("=" * 70)

    checks = []

    # Check for required fields
    if "warning" in output:
        checks.append("✅ Warning message present")
    else:
        checks.append("❌ Warning message missing")

    if "insights" in output:
        checks.append(f"✅ Insights present ({len(output.get('insights', []))} items)")
    else:
        checks.append("❌ Insights missing")

    if "recommendations" in output:
        checks.append(f"✅ Recommendations present ({len(output.get('recommendations', []))} items)")
    else:
        checks.append("❌ Recommendations missing")

    if "missing" in output:
        checks.append(f"✅ Missing items documented ({len(output.get('missing', []))} items)")
    else:
        checks.append("❌ Missing items not documented")

    if "assumptions" in output:
        checks.append(f"✅ Assumptions documented ({len(output.get('assumptions', []))} items)")
    else:
        checks.append("❌ Assumptions not documented")

    if "sources" in output:
        sources = output.get("sources", [])
        checks.append(f"✅ Sources with citations ({len(sources)} items)")
        if sources:
            print(f"\n   First source: {sources[0].get('title', 'N/A')}")
            print(f"   URL: {sources[0].get('url', 'N/A')}")
    else:
        checks.append("❌ Sources/citations missing")

    if "status" in output and output["status"] == "partial":
        checks.append("✅ Status correctly marked as 'partial'")
    else:
        checks.append("❌ Status not marked as partial")

    for check in checks:
        print(f"\n{check}")

    print("\n" + "=" * 70)

    # Overall assessment
    passed = all("✅" in check for check in checks)

    if passed:
        print("\n🎉 TEST PASSED - Partial digest generated correctly!")
    else:
        print("\n⚠️  TEST INCOMPLETE - Some fields missing")

    print("=" * 70 + "\n")

    return result


if __name__ == "__main__":
    asyncio.run(test_partial_digest())
