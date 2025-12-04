"""
Response Parser Utilities

Helper functions for parsing and processing LLM responses.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code blocks.

    Args:
        response_text: Raw LLM response text

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If JSON parsing fails
    """
    # Remove markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    # Parse JSON
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {response_text}")
        raise ValueError(f"Invalid JSON response from LLM: {str(e)}")


def summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize a result dictionary for logging (to avoid huge logs).

    Args:
        result: Full result dictionary

    Returns:
        Summarized result with key information only
    """
    summary: Dict[str, Any] = {}

    # Handle error results
    if "error" in result:
        summary["error"] = result["error"]

    # Handle search/retrieval results
    if "results" in result:
        summary["results_count"] = len(result["results"])
        summary["results_preview"] = result["results"][:2]  # First 2 items

    # Handle insights
    if "insights" in result:
        summary["insights_count"] = len(result["insights"])
        summary["insights_preview"] = [
            {"title": i.get("title", "")} for i in result["insights"][:2]
        ]

    # Handle RAGAS evaluation scores
    if "ragas_scores" in result:
        summary["ragas_scores"] = result["ragas_scores"]

    # Handle user context fields
    if "week" in result:
        summary["week"] = result["week"]

    if "topics" in result:
        summary["topics"] = result["topics"]

    # If no specific fields matched, return first 500 chars of string representation
    if not summary:
        summary["preview"] = str(result)[:500]

    return summary


def format_iteration_history(iteration_history: list[Dict[str, Any]]) -> str:
    """
    Format iteration history for prompt inclusion.

    Args:
        iteration_history: List of iteration dictionaries

    Returns:
        Formatted string representation
    """
    if not iteration_history:
        return "No previous iterations"

    formatted = []
    for hist in iteration_history:
        iteration = hist.get("iteration", "?")
        action = hist.get("action", "unknown")
        reflection = hist.get("reflection", "")
        formatted.append(f"Iteration {iteration}: {action} - {reflection}")

    return "\n".join(formatted)
