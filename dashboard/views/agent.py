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

    # Workflow status indicator
    if 'digest_generation_in_progress' in st.session_state and st.session_state['digest_generation_in_progress']:
        st.info("⏳ **Workflow Status:** Generating digest with web search results...")
    elif 'digest_completed' in st.session_state and st.session_state['digest_completed']:
        st.success("✅ **Workflow Status:** Digest completed! Scroll down to view results.")
    elif 'last_agent_result' in st.session_state:
        result_status = st.session_state['last_agent_result'].get('status', '')
        if result_status == 'needs_approval':
            st.warning("⏸️ **Workflow Status:** Waiting for web search approval...")

    # Execute agent when button is clicked
    if run_button and goal:
        # Set max iterations via environment
        os.environ["AGENT_MAX_ITERATIONS"] = str(max_iterations)

        with st.spinner("🤖 Agent is thinking and working..."):
            # Run agent
            result = run_agent_async(goal, st.session_state.user_id)

        # Store result in session state for approval workflow
        if result:
            st.session_state['last_agent_result'] = result
            st.session_state['last_agent_goal'] = goal

    # Check for pending approval from previous run
    elif 'last_agent_result' in st.session_state:
        result = st.session_state['last_agent_result']
        goal = st.session_state.get('last_agent_goal', goal)
    # Check for completed digest from approval workflow
    elif 'digest_completed' in st.session_state and st.session_state['digest_completed']:
        result = st.session_state.get('digest_result')
        goal = st.session_state.get('last_agent_goal', goal)
    else:
        result = None

    # Display results (from current run, pending approval, or completed digest)
    if result:
            # Status indicator
            status = result.get("status", "unknown")

            if status == "completed":
                st.success("✅ Agent completed successfully!")
            elif status == "timeout":
                st.warning("⏱️ Agent reached maximum iterations")
            elif status == "needs_clarification":
                st.info("❓ Agent needs clarification")
            elif status == "needs_approval":
                st.info("🔍 Agent needs approval for web search")
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

                # Check for plan approval needed
                elif "research_plan" in output and output.get("type") == "plan_approval_needed":
                    from components.research_planner_ui import render_research_plan_approval

                    research_plan = output.get("research_plan", {})
                    session_id = result.get("session_id", "")

                    # Store research plan in session state
                    st.session_state['pending_research_plan'] = research_plan
                    st.session_state['pending_goal'] = goal

                    # Render approval UI
                    decision = render_research_plan_approval(research_plan, session_id)

                    if decision == "approved":
                        st.success("✅ Approved! Executing web searches now...")

                        # Store approval
                        st.session_state['research_plan_approved'] = True

                        # Execute web searches automatically
                        with st.spinner("🌐 Executing approved web searches..."):
                            # Execute each proposed search
                            all_web_results = []
                            proposed_searches = research_plan.get("proposed_searches", [])

                            for search in proposed_searches:
                                search_result = execute_web_search_sync(search.get("query"), search.get("estimated_results", 5))
                                if search_result and "results" in search_result:
                                    all_web_results.extend(search_result["results"])

                        if all_web_results:
                            st.success(f"✅ Found {len(all_web_results)} web results!")

                            # Display web search results
                            from components.research_planner_ui import render_web_search_results
                            render_web_search_results(all_web_results, "Approved research queries")

                            # Store for later use
                            st.session_state['web_search_results'] = all_web_results
                        else:
                            st.warning("⚠️ No web results found. Using database content only.")

                        st.markdown("---")

                        # Store that we're now generating digest
                        st.session_state['digest_generation_in_progress'] = True
                        st.session_state['approval_session_id'] = session_id

                        # Continue agent to generate digest with web results
                        st.info("🤖 Continuing agent to generate digest with web search results...")

                        with st.spinner("🤖 Generating digest with combined sources..."):
                            # Set flag to skip approval on re-run (agent already has web results)
                            os.environ["SKIP_WEB_SEARCH_APPROVAL"] = "true"

                            # Re-run agent with approval granted
                            # The agent will now have access to web search results via session/context
                            continued_result = run_agent_async(
                                goal=st.session_state.get('last_agent_goal', goal),
                                user_id=st.session_state.user_id
                            )

                            # Clear the skip flag
                            if "SKIP_WEB_SEARCH_APPROVAL" in os.environ:
                                del os.environ["SKIP_WEB_SEARCH_APPROVAL"]

                        # Store the digest result in session state for persistence
                        if continued_result:
                            st.session_state['digest_result'] = continued_result
                            st.session_state['digest_generation_in_progress'] = False
                            st.session_state['digest_completed'] = True

                            # Clear the pending approval state
                            if 'last_agent_result' in st.session_state:
                                del st.session_state['last_agent_result']
                            if 'last_agent_goal' in st.session_state:
                                del st.session_state['last_agent_goal']

                            st.success("✅ Agent completed digest generation!")
                            st.rerun()  # Rerun to display the digest
                        else:
                            st.error("❌ Digest generation failed")
                            st.session_state['digest_generation_in_progress'] = False

                    elif decision == "denied":
                        st.warning("❌ Denied. Agent will use database-only results.")
                        st.session_state['research_plan_approved'] = False
                        st.info(
                            "💡 _Run the agent again to get database-only results._"
                        )

                        # Clear the pending result after handling denial
                        if 'last_agent_result' in st.session_state:
                            del st.session_state['last_agent_result']
                        if 'last_agent_goal' in st.session_state:
                            del st.session_state['last_agent_goal']

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

            # Clear workflow state button
            st.markdown("---")
            if st.button("🔄 Start New Query", key="clear_workflow"):
                # Clear all workflow state
                for key in ['last_agent_result', 'last_agent_goal', 'digest_result',
                           'digest_completed', 'digest_generation_in_progress',
                           'web_search_results', 'research_plan_approved',
                           'pending_research_plan', 'pending_goal']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    elif run_button and not goal:
        st.warning("⚠️ Please enter a learning goal first")


def execute_web_search_sync(query: str, max_results: int = 5) -> dict:
    """
    Execute web search synchronously.

    Args:
        query: Search query
        max_results: Maximum results to return

    Returns:
        Search results dictionary
    """
    try:
        from agent.tools import ToolRegistry
        import asyncio

        # Initialize tool registry
        tools = ToolRegistry(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Run web search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            tools.execute_tool(
                "web-search",
                {"query": query, "max_results": max_results}
            )
        )
        loop.close()

        return result

    except Exception as e:
        st.error(f"Error executing web search: {e}")
        return {"error": str(e), "results": []}


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

    # Check if this is a partial digest (timeout result)
    is_partial = digest.get("status") == "partial"

    if is_partial:
        # Show warning for partial results
        warning = digest.get("warning", "")
        if warning:
            st.warning(f"⚠️ **Partial Result**\n\n{warning}")
            st.markdown("---")

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
            # Handle both string insights (partial digest) and object insights (full digest)
            if isinstance(insight, str):
                # Simple string insight from partial digest
                with st.expander(f"{i}. Insight", expanded=(i == 1)):
                    st.markdown(insight)
            else:
                # Object insight with title and content
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

    # Recommendations (for partial digests)
    recommendations = digest.get("recommendations", [])
    if recommendations:
        st.markdown("#### 🎯 Recommendations")
        for rec in recommendations:
            st.markdown(f"- {rec}")
        st.markdown("---")

    # Missing items (for partial digests)
    missing = digest.get("missing", [])
    if missing:
        st.markdown("#### ❓ What Was Missing")
        for item in missing:
            st.markdown(f"- {item}")
        st.markdown("---")

    # Assumptions (for partial digests)
    assumptions = digest.get("assumptions", [])
    if assumptions:
        st.markdown("#### 💭 Assumptions Made")
        for assumption in assumptions:
            st.markdown(f"- {assumption}")
        st.markdown("---")

    # Sources summary (for partial digests)
    sources_summary = digest.get("sources_summary", "")
    if sources_summary:
        st.info(f"**Sources Summary:** {sources_summary}")
        st.markdown("---")

    # Sources with attribution
    sources = digest.get("sources", [])

    if sources:
        # Separate DB and web search sources
        db_sources = [s for s in sources if s.get("source_type") != "web_search"]
        web_sources = [s for s in sources if s.get("source_type") == "web_search"]

        if db_sources and web_sources:
            # Show both with separation
            st.markdown(f"#### 📚 From Your Trusted Database ({len(db_sources)})")

            for source in db_sources:
                url = source.get("url", "#")
                title = source.get("title", "Untitled")
                st.markdown(f"- 🟢 [{title}]({url})")

            st.markdown("---")

            st.markdown(f"#### 🌐 From Web Search ({len(web_sources)})")
            st.warning("⚠️ Web search results - not from your curated sources")

            for source in web_sources:
                url = source.get("url", "#")
                title = source.get("title", "Untitled")
                score = source.get("score", "")
                score_str = f" (Score: {score:.2f})" if score else ""
                st.markdown(f"- 🔴 [{title}]({url}){score_str}")

        else:
            # All from one source type
            st.markdown(f"#### 📚 Sources ({len(sources)})")

            for source in sources:
                url = source.get("url", "#")
                title = source.get("title", "Untitled")
                source_type = source.get("source_type", "database")

                if source_type == "web_search":
                    badge = "🔴 Web"
                    score = source.get("score", "")
                    score_str = f" (Score: {score:.2f})" if score else ""
                    st.markdown(f"- {badge} [{title}]({url}){score_str}")
                else:
                    badge = "🟢 DB"
                    st.markdown(f"- {badge} [{title}]({url})")

    # Full output option
    with st.expander("🔍 View Full Output (JSON)"):
        st.json(digest)
