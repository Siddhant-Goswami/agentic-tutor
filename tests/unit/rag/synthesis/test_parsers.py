"""
Tests for Insight Parsers
"""

import pytest
import json
from src.rag.synthesis.parsers import InsightParser


class TestInsightParser:
    """Test cases for InsightParser."""

    def test_parse_insights_valid_json(self):
        """Test parsing valid JSON response."""
        parser = InsightParser()

        response = json.dumps({
            "insights": [
                {
                    "title": "Test Insight",
                    "explanation": "This is a test explanation.",
                    "relevance_reason": "Very relevant",
                    "practical_takeaway": "Do this now",
                    "source": {
                        "title": "Source Title",
                        "author": "Author Name",
                        "url": "https://example.com",
                        "published_date": "2024-01-01"
                    },
                    "metadata": {
                        "confidence": 0.9,
                        "estimated_read_time": 5,
                        "difficulty_level": "intermediate",
                        "tags": ["test", "example"]
                    }
                }
            ]
        })

        insights = parser.parse_insights(response)

        assert len(insights) == 1
        assert insights[0]["title"] == "Test Insight"
        assert insights[0]["explanation"] == "This is a test explanation."
        assert insights[0]["source"]["title"] == "Source Title"

    def test_parse_insights_markdown_wrapped(self):
        """Test parsing JSON wrapped in markdown code block."""
        parser = InsightParser()

        response = """Here are the insights:

```json
{
  "insights": [
    {
      "title": "Wrapped Insight",
      "explanation": "Test explanation"
    }
  ]
}
```
"""

        insights = parser.parse_insights(response)

        assert len(insights) == 1
        assert insights[0]["title"] == "Wrapped Insight"

    def test_parse_insights_plain_markdown(self):
        """Test parsing JSON wrapped in plain markdown block."""
        parser = InsightParser()

        response = """```
{
  "insights": [
    {
      "title": "Plain Block",
      "explanation": "Test"
    }
  ]
}
```"""

        insights = parser.parse_insights(response)

        assert len(insights) == 1
        assert insights[0]["title"] == "Plain Block"

    def test_parse_insights_missing_optional_fields(self):
        """Test parsing insights with only required fields."""
        parser = InsightParser()

        response = json.dumps({
            "insights": [
                {
                    "title": "Minimal Insight",
                    "explanation": "Just the basics"
                }
            ]
        })

        insights = parser.parse_insights(response)

        assert len(insights) == 1
        assert insights[0]["title"] == "Minimal Insight"
        assert insights[0]["explanation"] == "Just the basics"
        # Check defaults are added
        assert "source" in insights[0]
        assert "metadata" in insights[0]
        assert insights[0]["source"]["title"] == "Unknown"

    def test_parse_insights_multiple(self):
        """Test parsing multiple insights."""
        parser = InsightParser()

        response = json.dumps({
            "insights": [
                {
                    "title": "Insight 1",
                    "explanation": "Explanation 1"
                },
                {
                    "title": "Insight 2",
                    "explanation": "Explanation 2"
                },
                {
                    "title": "Insight 3",
                    "explanation": "Explanation 3"
                }
            ]
        })

        insights = parser.parse_insights(response)

        assert len(insights) == 3
        assert insights[0]["title"] == "Insight 1"
        assert insights[1]["title"] == "Insight 2"
        assert insights[2]["title"] == "Insight 3"

    def test_parse_insights_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        parser = InsightParser()

        response = "This is not valid JSON"

        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parser.parse_insights(response)

    def test_parse_insights_missing_insights_key(self):
        """Test parsing JSON missing 'insights' key raises error."""
        parser = InsightParser()

        response = json.dumps({"results": []})

        with pytest.raises(ValueError, match="missing 'insights' key"):
            parser.parse_insights(response)

    def test_parse_insights_insights_not_list(self):
        """Test parsing when 'insights' is not a list raises error."""
        parser = InsightParser()

        response = json.dumps({"insights": "not a list"})

        with pytest.raises(ValueError, match="Expected insights to be list"):
            parser.parse_insights(response)

    def test_parse_insights_skips_invalid(self):
        """Test that invalid insights are skipped with warning."""
        parser = InsightParser()

        response = json.dumps({
            "insights": [
                {
                    "title": "Valid Insight",
                    "explanation": "Good explanation"
                },
                {
                    "title": "Missing explanation"
                    # Missing required 'explanation' field
                },
                {
                    "title": "Another Valid",
                    "explanation": "Also good"
                }
            ]
        })

        insights = parser.parse_insights(response)

        # Should only get the valid ones
        assert len(insights) == 2
        assert insights[0]["title"] == "Valid Insight"
        assert insights[1]["title"] == "Another Valid"

    def test_validate_insights_quality_min(self):
        """Test quality validation with minimum insights."""
        parser = InsightParser()

        insights = [
            {"title": "Test", "explanation": "Explanation"}
        ]

        # Should pass with 1 insight (default min)
        assert parser.validate_insights_quality(insights, min_insights=1)

    def test_validate_insights_quality_too_few(self):
        """Test quality validation fails with too few insights."""
        parser = InsightParser()

        insights = [
            {"title": "Test", "explanation": "Explanation"}
        ]

        with pytest.raises(ValueError, match="Too few insights"):
            parser.validate_insights_quality(insights, min_insights=3)

    def test_validate_insights_quality_max(self):
        """Test quality validation with maximum insights."""
        parser = InsightParser()

        insights = [
            {"title": f"Test {i}", "explanation": "Explanation"}
            for i in range(5)
        ]

        # Should pass with 5 insights (max 10)
        assert parser.validate_insights_quality(insights, max_insights=10)

    def test_validate_insights_quality_too_many(self):
        """Test quality validation fails with too many insights."""
        parser = InsightParser()

        insights = [
            {"title": f"Test {i}", "explanation": "Explanation"}
            for i in range(15)
        ]

        with pytest.raises(ValueError, match="Too many insights"):
            parser.validate_insights_quality(insights, max_insights=10)

    def test_validate_insight_missing_title(self):
        """Test validation fails for insight missing title."""
        parser = InsightParser()

        insight = {"explanation": "No title"}

        with pytest.raises(ValueError, match="Missing required field: title"):
            parser._validate_insight(insight, 0)

    def test_validate_insight_missing_explanation(self):
        """Test validation fails for insight missing explanation."""
        parser = InsightParser()

        insight = {"title": "No explanation"}

        with pytest.raises(ValueError, match="Missing required field: explanation"):
            parser._validate_insight(insight, 0)

    def test_extract_json_from_nested_object(self):
        """Test extracting JSON from text with nested object."""
        parser = InsightParser()

        response = """
        Some text before
        {
            "insights": [
                {
                    "title": "Nested",
                    "explanation": "Test",
                    "metadata": {
                        "nested": "value"
                    }
                }
            ]
        }
        Some text after
        """

        result = parser._extract_json(response)

        assert "insights" in result
        assert len(result["insights"]) == 1
        assert result["insights"][0]["metadata"]["nested"] == "value"
