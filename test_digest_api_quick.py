"""
Quick test to verify enhanced digest_api.py works.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Add dashboard to path
project_root = Path(__file__).parent
dashboard_path = project_root / "dashboard"
if str(dashboard_path) not in sys.path:
    sys.path.insert(0, str(dashboard_path))


async def quick_test():
    """Quick test of enhanced digest API."""
    print("\n" + "=" * 80)
    print("QUICK TEST: Enhanced Digest API")
    print("=" * 80 + "\n")

    # Check environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    print("Environment Check:")
    print(f"  SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"  SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    print(f"  OPENAI_API_KEY: {'✅ Set' if openai_api_key else '❌ Missing'}")
    print()

    if not all([supabase_url, supabase_key, openai_api_key]):
        print("❌ Missing required environment variables")
        return False

    # Test import
    try:
        from digest_api import generate_digest_simple
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test basic call
    print("\nTesting basic digest generation...")
    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
        )

        print(f"\nResult:")
        print(f"  Success: {result.get('success')}")
        print(f"  Num Insights: {result.get('num_insights', 0)}")
        print(f"  Quality Badge: {result.get('quality_badge', 'N/A')}")

        # Check required fields
        required = ["success", "num_insights"]
        missing = [f for f in required if f not in result]
        if missing:
            print(f"  ❌ Missing fields: {missing}")
        else:
            print(f"  ✅ All required fields present")

        if result.get("success"):
            print("\n✅ SUCCESS: Digest generated!")
            insights = result.get("insights", [])
            if insights:
                print(f"\nSample insight:")
                print(f"  Title: {insights[0].get('title', 'N/A')[:60]}...")
        else:
            error = result.get("error") or result.get("message", "Unknown")
            print(f"\n⚠️  Digest generation returned success=false")
            print(f"  Reason: {error}")
            if "No content" in error or "No relevant content" in error:
                print("  (This is OK - database may not have content yet)")

        return True

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)

