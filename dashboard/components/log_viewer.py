"""
Log Viewer Component

Renders agent execution logs with color coding and expandable details.
"""

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime
import json


def render_logs(logs: List[Dict[str, Any]]) -> None:
    """
    Render agent logs with color coding and expandable entries.

    Args:
        logs: List of log entries from agent execution
    """
    if not logs:
        st.info("No logs available yet.")
        return

    # Phase emoji and color mapping
    phase_config = {
        "SENSE": {"emoji": "🔵", "color": "#3b82f6"},
        "PLAN": {"emoji": "🟡", "color": "#eab308"},
        "ACT": {"emoji": "🟢", "color": "#22c55e"},
        "OBSERVE": {"emoji": "🟣", "color": "#a855f7"},
        "REFLECT": {"emoji": "🟠", "color": "#f97316"},
        "COMPLETE": {"emoji": "✅", "color": "#10b981"},
        "CLARIFY": {"emoji": "❓", "color": "#06b6d4"},
        "ERROR": {"emoji": "❌", "color": "#ef4444"},
    }

    st.markdown("---")

    # Render each log entry
    for i, log in enumerate(logs):
        phase = log.get("phase", "UNKNOWN")
        config = phase_config.get(phase, {"emoji": "⚪", "color": "#gray"})

        # Format timestamp
        timestamp = log.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp
        else:
            time_str = "N/A"

        # Header
        iteration = log.get("iteration")
        if iteration:
            header = f"{config['emoji']} {phase} - Iteration {iteration}"
        else:
            header = f"{config['emoji']} {phase}"

        # Determine if expanded by default (first 3 logs)
        expanded = i < 3

        with st.expander(f"[{time_str}] {header}", expanded=expanded):
            content = log.get("content", {})

            # Special rendering based on phase
            if phase == "SENSE":
                _render_sense_log(content)
            elif phase == "PLAN":
                _render_plan_log(content)
            elif phase == "ACT":
                _render_act_log(content)
            elif phase == "OBSERVE":
                _render_observe_log(content)
            elif phase == "REFLECT":
                _render_reflect_log(content)
            elif phase == "COMPLETE":
                _render_complete_log(content)
            elif phase == "CLARIFY":
                _render_clarify_log(content)
            elif phase == "ERROR":
                _render_error_log(content)
            else:
                # Fallback: render as JSON
                st.json(content)


def _render_sense_log(content: Dict[str, Any]) -> None:
    """Render SENSE phase log."""
    st.markdown("**Gathered User Context:**")

    user_context = content.get("user_context", {})

    if user_context:
        col1, col2, col3 = st.columns(3)

        with col1:
            week = user_context.get("week")
            if week:
                st.metric("Current Week", f"{week}/24")

        with col2:
            difficulty = user_context.get("difficulty", "N/A")
            st.metric("Difficulty", difficulty.title())

        with col3:
            topics = user_context.get("topics", [])
            st.metric("Topics", len(topics))

        if topics:
            st.markdown("**Current Topics:**")
            for topic in topics:
                st.markdown(f"- {topic}")

        if "learning_goals" in user_context and user_context["learning_goals"]:
            st.markdown(f"**Learning Goals:** {user_context['learning_goals']}")

    message = content.get("message")
    if message:
        st.success(message)


def _render_plan_log(content: Dict[str, Any]) -> None:
    """Render PLAN phase log."""
    plan = content.get("plan", {})

    action_type = plan.get("action_type", "UNKNOWN")
    reasoning = plan.get("reasoning", "")

    st.markdown(f"**Decision:** `{action_type}`")

    if reasoning:
        st.markdown("**Reasoning:**")
        st.info(reasoning)

    if action_type == "TOOL_CALL":
        tool = plan.get("tool", "unknown")
        args = plan.get("args", {})

        st.markdown(f"**Tool:** `{tool}`")

        if args:
            st.markdown("**Arguments:**")
            st.json(args)

    elif action_type == "COMPLETE":
        output = plan.get("output", {})
        if output:
            st.markdown("**Final Output:**")
            st.json(output)

    elif action_type == "CLARIFY":
        question = plan.get("question", "")
        if question:
            st.markdown("**Question:**")
            st.warning(question)


def _render_act_log(content: Dict[str, Any]) -> None:
    """Render ACT phase log."""
    tool = content.get("tool", "unknown")
    args = content.get("args", {})
    result_preview = content.get("result_preview", "")

    st.markdown(f"**Executed Tool:** `{tool}`")

    if args:
        st.markdown("**Arguments:**")
        st.json(args)

    if result_preview:
        st.markdown("**Result Preview:**")
        st.code(result_preview, language="text")


def _render_observe_log(content: Dict[str, Any]) -> None:
    """Render OBSERVE phase log."""
    tool = content.get("tool", "unknown")
    status = content.get("status", "unknown")
    result_summary = content.get("result_summary", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Tool:** `{tool}`")

    with col2:
        if status == "success":
            st.success(f"Status: {status}")
        else:
            st.error(f"Status: {status}")

    if "error" in content:
        st.error(f"**Error:** {content['error']}")

    if result_summary:
        st.markdown("**Result Summary:**")
        st.json(result_summary)


def _render_reflect_log(content: Dict[str, Any]) -> None:
    """Render REFLECT phase log."""
    reflection = content.get("reflection", "")

    if reflection:
        st.markdown("**Agent Reflection:**")
        st.info(reflection)


def _render_complete_log(content: Dict[str, Any]) -> None:
    """Render COMPLETE phase log."""
    output = content.get("output", {})
    reasoning = content.get("reasoning", "")
    status = content.get("status", "completed")

    if status == "timeout":
        st.warning("**Status:** Maximum iterations reached")
        message = content.get("message", "")
        if message:
            st.write(message)

    elif status == "completed":
        st.success("**Status:** Goal achieved!")

    if reasoning:
        st.markdown("**Reasoning:**")
        st.info(reasoning)

    if output:
        st.markdown("**Final Output:**")

        # Special rendering for digest output
        if "digest" in output:
            digest = output["digest"]
            if "insights" in digest:
                st.metric("Insights Generated", len(digest["insights"]))
            if "ragas_scores" in digest:
                scores = digest["ragas_scores"]
                avg_score = scores.get("average", 0)
                st.metric("Quality Score", f"{avg_score:.2f}")

        # Show full output as JSON
        with st.expander("View Full Output"):
            st.json(output)


def _render_clarify_log(content: Dict[str, Any]) -> None:
    """Render CLARIFY phase log."""
    question = content.get("question", "")
    reasoning = content.get("reasoning", "")

    if question:
        st.markdown("**Question for User:**")
        st.warning(question)

    if reasoning:
        st.markdown("**Why Clarification Needed:**")
        st.info(reasoning)


def _render_error_log(content: Dict[str, Any]) -> None:
    """Render ERROR phase log."""
    error = content.get("error", "Unknown error")

    st.error(f"**Error:** {error}")

    # Show full content for debugging
    with st.expander("Full Error Details"):
        st.json(content)
