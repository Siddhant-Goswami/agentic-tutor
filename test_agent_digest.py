"""
Test agent with digest generation goal
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
project_root = Path(__file__).parent
learning_coach_path = project_root / "learning-coach-mcp"
src_path = learning_coach_path / "src"

sys.path.insert(0, str(src_path))
sys.path.insert(0, str(learning_coach_path))

# Load environment
env_path = learning_coach_path / ".env"
load_dotenv(env_path)

from agent.controller import AgentController, AgentConfig


async def main():
    print("="*70)
    print("  TESTING: Generate Daily Digest")
    print("="*70)

    config = AgentConfig(
        max_iterations=10,
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

    print("\n🚀 Running agent with goal: 'Generate my daily learning digest'\n")

    result = await controller.run(
        goal="Generate my daily learning digest",
        user_id=os.getenv("DEFAULT_USER_ID")
    )

    print(f"\n✅ Status: {result.status}")
    print(f"🔁 Iterations: {result.iteration_count}")
    print(f"📝 Total log entries: {len(result.logs)}")

    print("\n" + "="*70)
    print("  AGENT REASONING LOG")
    print("="*70)

    for i, log in enumerate(result.logs, 1):
        phase = log.get("phase")
        content = log.get("content", {})

        print(f"\n[{i}] {phase}")

        if phase == "PLAN":
            plan = content.get("plan", {})
            print(f"    Action: {plan.get('action_type')}")
            print(f"    Tool: {plan.get('tool', 'N/A')}")
            print(f"    Reasoning: {plan.get('reasoning', 'N/A')[:100]}...")

        elif phase == "ACT":
            print(f"    Executed: {content.get('tool')}")

        elif phase == "REFLECT":
            reflection = content.get('reflection', '')
            print(f"    {reflection[:150]}...")

    print("\n" + "="*70)
    print("  OUTPUT SUMMARY")
    print("="*70)

    output = result.output
    if "insights" in output:
        print(f"\n✅ Generated {len(output['insights'])} insights")
    elif "digest" in output and "insights" in output["digest"]:
        print(f"\n✅ Generated {len(output['digest']['insights'])} insights")
    else:
        print(f"\n📋 Output keys: {list(output.keys())}")

    print("\n✅ Test complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
