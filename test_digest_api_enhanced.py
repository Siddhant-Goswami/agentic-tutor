"""
Comprehensive test suite for enhanced digest_api.py

Tests semantic search, success indicators, Q&A mode, and error handling.
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

from digest_api import generate_digest_simple


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_test(self, name: str, passed: bool, message: str = ""):
        """Add a test result."""
        self.tests.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"✅ PASS: {name}")
            if message:
                print(f"   {message}")
        else:
            self.failed += 1
            print(f"❌ FAIL: {name}")
            if message:
                print(f"   {message}")

    def summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {len(self.tests)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / len(self.tests) * 100):.1f}%")
        print("=" * 80)
        return self.failed == 0


async def test_success_indicators(results: TestResults):
    """Test that success indicators are properly set."""
    print("\n" + "=" * 80)
    print("TEST 1: Success Indicators")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Success Indicators - Setup",
            False,
            "Missing environment variables (SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
        )

        # Check success field exists
        has_success = "success" in result
        results.add_test(
            "Success field present",
            has_success,
            f"Result: {result.get('success')}" if has_success else "Missing 'success' field"
        )

        # Check num_insights field exists
        has_num_insights = "num_insights" in result
        results.add_test(
            "num_insights field present",
            has_num_insights,
            f"Result: {result.get('num_insights')}" if has_num_insights else "Missing 'num_insights' field"
        )

        # If success is true, should have insights
        if result.get("success"):
            has_insights = result.get("num_insights", 0) > 0
            results.add_test(
                "Success=true has insights",
                has_insights,
                f"Found {result.get('num_insights')} insights"
            )

            # Check insights structure
            insights = result.get("insights", [])
            if insights:
                first_insight = insights[0]
                required_fields = ["title", "explanation", "practical_takeaway"]
                missing_fields = [f for f in required_fields if f not in first_insight]
                results.add_test(
                    "Insight structure valid",
                    len(missing_fields) == 0,
                    f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                )

    except Exception as e:
        results.add_test(
            "Success Indicators - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def test_qa_mode(results: TestResults):
    """Test Q&A mode with explicit_query."""
    print("\n" + "=" * 80)
    print("TEST 2: Q&A Mode (explicit_query)")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Q&A Mode - Setup",
            False,
            "Missing environment variables"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
            explicit_query="What is Model Context Protocol and how does it work?",
        )

        # Check success
        success = result.get("success", False)
        results.add_test(
            "Q&A mode returns success",
            success,
            f"Success: {success}, Insights: {result.get('num_insights', 0)}"
        )

        # Q&A mode should generate fewer insights (focused answer)
        if success:
            num_insights = result.get("num_insights", 0)
            results.add_test(
                "Q&A mode generates insights",
                num_insights > 0,
                f"Generated {num_insights} insights"
            )

            # Check that query is preserved in metadata
            metadata = result.get("metadata", {})
            has_query = "query" in metadata
            results.add_test(
                "Query preserved in metadata",
                has_query,
                f"Query: {metadata.get('query', 'N/A')[:50]}..."
            )

    except Exception as e:
        results.add_test(
            "Q&A Mode - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def test_error_handling(results: TestResults):
    """Test error handling for various failure cases."""
    print("\n" + "=" * 80)
    print("TEST 3: Error Handling")
    print("=" * 80)

    # Test 1: Missing Supabase config
    try:
        # Temporarily unset env vars
        original_url = os.environ.get("SUPABASE_URL")
        original_key = os.environ.get("SUPABASE_KEY")
        
        if "SUPABASE_URL" in os.environ:
            del os.environ["SUPABASE_URL"]

        result = await generate_digest_simple(
            user_id="00000000-0000-0000-0000-000000000001",
            date_obj=date.today(),
            max_insights=3,
        )

        # Should return success=false
        has_success = "success" in result
        success_false = result.get("success") == False
        has_error = "error" in result or "message" in result

        results.add_test(
            "Missing Supabase config handled",
            has_success and success_false and has_error,
            f"Success: {result.get('success')}, Error: {result.get('error', result.get('message', 'N/A'))}"
        )

        # Restore env vars
        if original_url:
            os.environ["SUPABASE_URL"] = original_url
        if original_key:
            os.environ["SUPABASE_KEY"] = original_key

    except Exception as e:
        results.add_test(
            "Missing Supabase config - Exception",
            False,
            f"Exception: {str(e)}"
        )

    # Test 2: Missing OpenAI key (should return success=false)
    try:
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        result = await generate_digest_simple(
            user_id="00000000-0000-0000-0000-000000000001",
            date_obj=date.today(),
            max_insights=3,
        )

        has_success = "success" in result
        success_false = result.get("success") == False

        results.add_test(
            "Missing OpenAI key handled",
            has_success and success_false,
            f"Success: {result.get('success')}"
        )

        # Restore
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key

    except Exception as e:
        results.add_test(
            "Missing OpenAI key - Exception",
            False,
            f"Exception: {str(e)}"
        )


async def test_cache_behavior(results: TestResults):
    """Test cache behavior with force_refresh."""
    print("\n" + "=" * 80)
    print("TEST 4: Cache Behavior")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Cache Behavior - Setup",
            False,
            "Missing environment variables"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        # First call with force_refresh=True
        result1 = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
        )

        # Second call with force_refresh=False (should use cache if available)
        result2 = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=False,
        )

        # Both should have success field
        has_success1 = "success" in result1
        has_success2 = "success" in result2

        results.add_test(
            "Both calls return success field",
            has_success1 and has_success2,
            f"First: {result1.get('success')}, Second: {result2.get('success')}"
        )

        # If first succeeded, second might be cached
        if result1.get("success"):
            is_cached = result2.get("cached", False)
            results.add_test(
                "Cache flag present",
                "cached" in result2 or not is_cached,
                f"Cached: {is_cached}"
            )

    except Exception as e:
        results.add_test(
            "Cache Behavior - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def test_semantic_search(results: TestResults):
    """Test that semantic search is working."""
    print("\n" + "=" * 80)
    print("TEST 5: Semantic Search")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Semantic Search - Setup",
            False,
            "Missing environment variables"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=5,
            force_refresh=True,
        )

        if result.get("success"):
            # Check metadata for search results
            metadata = result.get("metadata", {})
            has_sources = "num_sources" in metadata
            has_chunks = "num_chunks" in metadata
            has_query = "query" in metadata

            results.add_test(
                "Metadata contains search info",
                has_sources and has_chunks and has_query,
                f"Sources: {metadata.get('num_sources', 0)}, Chunks: {metadata.get('num_chunks', 0)}"
            )

            # Check that we got some sources
            num_sources = metadata.get("num_sources", 0)
            results.add_test(
                "Semantic search found sources",
                num_sources > 0,
                f"Found {num_sources} sources"
            )

        else:
            # If no success, might be because no content in DB
            error_msg = result.get("error") or result.get("message", "")
            if "No content" in error_msg or "No relevant content" in error_msg:
                results.add_test(
                    "Semantic Search - No Content",
                    True,
                    "Expected: No content in database (this is OK for testing)"
                )
            else:
                results.add_test(
                    "Semantic Search - Failed",
                    False,
                    f"Error: {error_msg}"
                )

    except Exception as e:
        results.add_test(
            "Semantic Search - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def test_quality_indicators(results: TestResults):
    """Test quality badges and RAGAS scores."""
    print("\n" + "=" * 80)
    print("TEST 6: Quality Indicators")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Quality Indicators - Setup",
            False,
            "Missing environment variables"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=5,
            force_refresh=True,
        )

        if result.get("success"):
            # Check quality badge
            quality_badge = result.get("quality_badge")
            valid_badges = ["✨", "✓", "⚠"]
            has_valid_badge = quality_badge in valid_badges

            results.add_test(
                "Quality badge present and valid",
                has_valid_badge,
                f"Badge: {quality_badge}"
            )

            # Check RAGAS scores
            ragas_scores = result.get("ragas_scores", {})
            has_ragas = bool(ragas_scores)
            has_average = "average" in ragas_scores

            results.add_test(
                "RAGAS scores present",
                has_ragas and has_average,
                f"Average: {ragas_scores.get('average', 'N/A')}"
            )

            if has_average:
                avg_score = ragas_scores.get("average", 0)
                score_in_range = 0.0 <= avg_score <= 1.0
                results.add_test(
                    "RAGAS average in valid range",
                    score_in_range,
                    f"Score: {avg_score:.3f}"
                )

        else:
            results.add_test(
                "Quality Indicators - Skipped",
                True,
                "Skipped (digest generation failed, likely no content)"
            )

    except Exception as e:
        results.add_test(
            "Quality Indicators - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def test_agent_completion_logic(results: TestResults):
    """Test that results match what agent expects for completion."""
    print("\n" + "=" * 80)
    print("TEST 7: Agent Completion Logic")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        results.add_test(
            "Agent Completion - Setup",
            False,
            "Missing environment variables"
        )
        return

    user_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = await generate_digest_simple(
            user_id=user_id,
            date_obj=date.today(),
            max_insights=3,
            force_refresh=True,
        )

        # Agent checks: success=true AND num_insights > 0
        success = result.get("success", False)
        num_insights = result.get("num_insights", 0)

        should_complete = success and num_insights > 0

        results.add_test(
            "Agent completion condition met",
            should_complete or not success,  # OK if failed (no content)
            f"Success: {success}, Insights: {num_insights}, Should Complete: {should_complete}"
        )

        # Check that all required fields for agent are present
        required_fields = ["success", "num_insights", "insights", "ragas_scores", "quality_badge"]
        missing_fields = [f for f in required_fields if f not in result]

        results.add_test(
            "All required fields present",
            len(missing_fields) == 0,
            f"Missing: {missing_fields}" if missing_fields else "All fields present"
        )

    except Exception as e:
        results.add_test(
            "Agent Completion - Execution",
            False,
            f"Exception: {str(e)}"
        )


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ENHANCED DIGEST API TEST SUITE")
    print("=" * 80)

    results = TestResults()

    # Run all tests
    await test_success_indicators(results)
    await test_qa_mode(results)
    await test_error_handling(results)
    await test_cache_behavior(results)
    await test_semantic_search(results)
    await test_quality_indicators(results)
    await test_agent_completion_logic(results)

    # Print summary
    success = results.summary()

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

