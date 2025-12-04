"""
Response Parsers for Synthesis

Parses and validates LLM responses for synthesis operations.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class InsightParser:
    """Parses and validates synthesized insights from LLM responses."""

    def __init__(self):
        """Initialize insight parser."""
        pass

    def parse_insights(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse insights from LLM response.

        Args:
            response_text: Raw LLM response text

        Returns:
            List of parsed insight dictionaries

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response
        insights_data = self._extract_json(response_text)

        # Validate structure
        if not isinstance(insights_data, dict):
            raise ValueError(f"Expected dict, got {type(insights_data)}")

        if "insights" not in insights_data:
            raise ValueError("Response missing 'insights' key")

        insights = insights_data["insights"]

        if not isinstance(insights, list):
            raise ValueError(f"Expected insights to be list, got {type(insights)}")

        # Validate each insight
        validated_insights = []
        for idx, insight in enumerate(insights):
            try:
                validated = self._validate_insight(insight, idx)
                validated_insights.append(validated)
            except Exception as e:
                logger.warning(f"Skipping invalid insight {idx}: {e}")
                continue

        logger.info(f"Successfully parsed {len(validated_insights)} insights")

        return validated_insights

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.

        Handles JSON wrapped in markdown code blocks or plain text.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON cannot be extracted
        """
        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            response_text,
            re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding raw JSON object
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Log error with truncated response
        logger.error(f"Could not extract JSON from response: {response_text[:500]}")
        raise ValueError("Could not extract valid JSON from response")

    def _validate_insight(self, insight: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Validate and normalize a single insight.

        Args:
            insight: Raw insight dictionary
            index: Index of insight in list

        Returns:
            Validated and normalized insight

        Raises:
            ValueError: If insight is invalid
        """
        required_fields = ["title", "explanation"]

        # Check required fields
        for field in required_fields:
            if field not in insight:
                raise ValueError(f"Missing required field: {field}")

        # Validate types
        if not isinstance(insight["title"], str):
            raise ValueError(f"'title' must be string, got {type(insight['title'])}")

        if not isinstance(insight["explanation"], str):
            raise ValueError(f"'explanation' must be string, got {type(insight['explanation'])}")

        # Normalize field names (handle variations)
        normalized = {
            "title": insight["title"],
            "explanation": insight["explanation"],
            "relevance_reason": insight.get("relevance_reason", ""),
            "practical_takeaway": insight.get("practical_takeaway", ""),
        }

        # Handle source (can be dict or missing)
        if "source" in insight and isinstance(insight["source"], dict):
            normalized["source"] = {
                "title": insight["source"].get("title", "Unknown"),
                "author": insight["source"].get("author", "Unknown"),
                "url": insight["source"].get("url", ""),
                "published_date": insight["source"].get("published_date", ""),
            }
        else:
            normalized["source"] = {
                "title": "Unknown",
                "author": "Unknown",
                "url": "",
                "published_date": "",
            }

        # Handle metadata (optional)
        if "metadata" in insight and isinstance(insight["metadata"], dict):
            normalized["metadata"] = {
                "confidence": insight["metadata"].get("confidence", 0.8),
                "estimated_read_time": insight["metadata"].get("estimated_read_time", 5),
                "difficulty_level": insight["metadata"].get("difficulty_level", "intermediate"),
                "tags": insight["metadata"].get("tags", []),
            }
        else:
            normalized["metadata"] = {
                "confidence": 0.8,
                "estimated_read_time": 5,
                "difficulty_level": "intermediate",
                "tags": [],
            }

        return normalized

    def validate_insights_quality(
        self,
        insights: List[Dict[str, Any]],
        min_insights: int = 1,
        max_insights: Optional[int] = None,
    ) -> bool:
        """
        Validate that insights meet quality standards.

        Args:
            insights: List of insights to validate
            min_insights: Minimum number of insights required
            max_insights: Maximum number of insights allowed (optional)

        Returns:
            True if insights meet quality standards

        Raises:
            ValueError: If validation fails
        """
        if len(insights) < min_insights:
            raise ValueError(
                f"Too few insights: got {len(insights)}, need at least {min_insights}"
            )

        if max_insights and len(insights) > max_insights:
            raise ValueError(
                f"Too many insights: got {len(insights)}, max {max_insights}"
            )

        # Check for duplicate titles
        titles = [insight["title"] for insight in insights]
        if len(titles) != len(set(titles)):
            logger.warning("Found duplicate insight titles")

        # Check explanation lengths
        for insight in insights:
            explanation_len = len(insight["explanation"].split())
            if explanation_len < 50:
                logger.warning(
                    f"Short explanation ({explanation_len} words) in '{insight['title']}'"
                )

        return True
