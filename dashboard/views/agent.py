"""
Agent View

Interactive interface for running the autonomous learning coach agent.
"""

import streamlit as st
import sys
from pathlib import Path
import os
import asyncio

# Add parent directories to path for imports
dashboard_path = Path(__file__).parent.parent
project_root = dashboard_path.parent
sys.path.insert(0, str(project_root))


def show():
    """Display the agent interaction view."""

    st.title("🤖 Learning Coach Agent")
    st.markdown(
        """
    **Autonomous Agent Mode** - The agent will reason about your goal, decide which tools to call,
    and adapt based on results. Watch the reasoning unfold in real-time!
    """
    )

    st.markdown("---")

    # Agent input section
    st.markdown("### 📝 What would you like to learn?")

    # Provide some example goals
    with st.expander("💡 Example Goals"):
        st.markdown(
            """
        - "Generate my daily learning digest"
        - "Help me understand attention mechanisms in transformers"
        - "Find visual explanations of multi-head attention"
        - "What did I learn last week about transformers?"
        - "Create a quiz on attention mechanisms at intermediate level"
        """
        )

    # Goal input
    goal = st.text_area(
        "Enter your learning goal:",
        placeholder="E.g., 'Help me learn about attention mechanisms' or 'Generate my daily digest'",
        height=100,
        help="Describe what you want to learn or accomplish in natural language",
    )

    # Advanced options
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)

        with col1:
            max_iterations = st.number_input(
                "Max Iterations",
                min_value=1,
                max_value=20,
                value=10,
                help="Maximum number of agent iterations before timeout",
            )

        with col2:
            show_full_logs = st.checkbox(
                "Show Full Logs",
                value=False,
                help="Display complete log details (more verbose)",
            )

    # Run button
    run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True)

    st.markdown("---")

    # Execute agent when button is clicked
    if run_button and goal:
        # Set max iterations via environment
        os.environ["AGENT_MAX_ITERATIONS"] = str(max_iterations)

        with st.spinner("🤖 Agent is thinking and working..."):
            # Run agent
            result = run_agent_async(goal, st.session_state.user_id)

        # Display results
        if result:
            # Status indicator
            status = result.get("status", "unknown")

            if status == "completed":
                st.success("✅ Agent completed successfully!")
            elif status == "timeout":
                st.warning("⏱️ Agent reached maximum iterations")
            elif status == "needs_clarification":
                st.info("❓ Agent needs clarification")
            elif status == "failed":
                st.error("❌ Agent execution failed")

            # Metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                iterations = result.get("iterations", 0)
                st.metric("Iterations", f"{iterations}/{max_iterations}")

            with col2:
                logs = result.get("logs", [])
                st.metric("Log Entries", len(logs))

            with col3:
                session_id = result.get("session_id", "N/A")
                st.metric("Session ID", session_id[:8] + "...")

            st.markdown("---")

            # Output section
            output = result.get("output", {})

            if output:
                st.markdown("### 📋 Agent Output")

                # Check for errors
                if "error" in output:
                    st.error(f"**Error:** {output['error']}")

                # Check for clarification questions
                elif "question" in output and output.get("type") == "clarification_needed":
                    st.info(f"**Question:** {output['question']}")
                    st.markdown(
                        "💡 _Refine your goal based on this question and run the agent again._"
                    )

                # Check for digest output
                elif "digest" in output or "insights" in output:
                    _render_digest_output(output)

                # Generic output
                else:
                    with st.expander("View Output", expanded=True):
                        st.json(output)

            st.markdown("---")

            # Logs section
            if logs:
                st.markdown("### 🔍 Agent Reasoning Logs")
                st.markdown(
                    "_See how the agent thought through the problem step by step_"
                )

                from components.log_viewer import render_logs

                render_logs(logs)

    elif run_button and not goal:
        st.warning("⚠️ Please enter a learning goal first")


def run_agent_async(goal: str, user_id: str) -> dict:
    """
    Run the agent asynchronously.

    Args:
        goal: User's learning goal
        user_id: User ID

    Returns:
        Agent result dictionary
    """
    try:
        from agent.controller import AgentController, AgentConfig

        # Get config
        config = AgentConfig(
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
            llm_model=os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini"),
            temperature=0.3,
        )

        # Initialize controller
        controller = AgentController(
            config=config,
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        # Run agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(controller.run(goal, user_id))
        loop.close()

        return {
            "output": result.output,
            "logs": result.logs,
            "iterations": result.iteration_count,
            "status": result.status,
            "session_id": result.session_id,
        }

    except Exception as e:
        st.error(f"Error running agent: {e}")
        return {
            "output": {"error": str(e)},
            "logs": [],
            "iterations": 0,
            "status": "failed",
            "session_id": "N/A",
        }


def _render_digest_output(output: dict) -> None:
    """
    Render digest output with nice formatting.

    Args:
        output: Output containing digest or insights
    """
    digest = output.get("digest", output)

    # Quality scores
    if "ragas_scores" in digest:
        scores = digest["ragas_scores"]
        avg_score = scores.get("average", 0)

        st.markdown("#### 📊 Quality Metrics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Overall Quality", f"{avg_score:.2%}")

        with col2:
            faithfulness = scores.get("faithfulness", 0)
            st.metric("Faithfulness", f"{faithfulness:.2%}")

        with col3:
            relevance = scores.get("answer_relevance", 0)
            st.metric("Relevance", f"{relevance:.2%}")

        st.markdown("---")

    # Insights
    insights = digest.get("insights", [])

    if insights:
        st.markdown(f"#### 💡 Learning Insights ({len(insights)})")

        for i, insight in enumerate(insights, 1):
            with st.expander(f"{i}. {insight.get('title', 'Untitled')}", expanded=(i == 1)):
                content = insight.get("content", "")
                st.markdown(content)

                # Source
                source = insight.get("source", {})
                if source:
                    st.caption(
                        f"📚 Source: {source.get('identifier', 'Unknown')} | "
                        f"Published: {source.get('published_at', 'N/A')}"
                    )

        st.markdown("---")

    # Quiz
    quiz = digest.get("quiz", [])

    if quiz:
        st.markdown(f"#### 📝 Quiz Questions ({len(quiz)})")

        for i, q in enumerate(quiz, 1):
            st.markdown(f"**Question {i}:** {q.get('question', '')}")

            options = q.get("options", [])
            if options:
                for opt in options:
                    st.markdown(f"- {opt}")

            with st.expander("Show Answer"):
                st.success(f"**Answer:** {q.get('correct_answer', 'N/A')}")
                explanation = q.get("explanation", "")
                if explanation:
                    st.markdown(f"**Explanation:** {explanation}")

            st.markdown("")

        st.markdown("---")

    # Sources
    sources = digest.get("sources", [])

    if sources:
        st.markdown(f"#### 📚 Sources ({len(sources)})")

        for source in sources:
            url = source.get("url", "#")
            title = source.get("title", "Untitled")
            identifier = source.get("identifier", "Unknown")

            st.markdown(f"- [{title}]({url}) - {identifier}")

    # Full output option
    with st.expander("🔍 View Full Output (JSON)"):
        st.json(digest)
