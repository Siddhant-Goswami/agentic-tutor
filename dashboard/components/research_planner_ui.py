"""
Research Planner UI Component

Displays research plans and provides approval controls for web search.
"""

import streamlit as st
from typing import Dict, Any, Optional


def render_research_plan_approval(
    research_plan: Dict[str, Any],
    session_id: str
) -> Optional[str]:
    """
    Render research plan approval UI.

    Args:
        research_plan: Research plan dictionary
        session_id: Agent session ID

    Returns:
        User decision: 'approved', 'denied', or None (waiting)
    """
    # Check if decision already made in session state
    decision_key = f"research_approval_{session_id}"

    if decision_key in st.session_state:
        # Decision was already made, return it
        decision = st.session_state[decision_key]
        # Clear the decision after returning it
        del st.session_state[decision_key]
        return decision

    st.markdown("### 🔍 Research Plan Requires Approval")
    st.markdown("---")

    # Show warning banner
    st.warning(
        "⚠️ **Web Search Required**\n\n"
        "The agent wants to search the web for additional content. "
        "Web results are not from your curated sources and may need verification."
    )

    # Database coverage
    db_results = research_plan.get("db_results", {})
    db_count = db_results.get("count", 0)

    st.markdown("#### 📚 Your Database Coverage")

    if db_count == 0:
        st.error(f"❌ No relevant content found in your database")
    elif db_count < 3:
        st.warning(f"⚠️ Only {db_count} results found in your database")
    else:
        st.info(f"✓ {db_count} results found, but gaps identified")

    # Show existing sources
    sources = db_results.get("sources", [])
    if sources:
        with st.expander(f"View {len(sources)} Database Sources"):
            for i, source in enumerate(sources, 1):
                st.markdown(f"{i}. {source}")

    st.markdown("---")

    # Coverage gaps
    coverage_gaps = research_plan.get("coverage_gaps", [])

    if coverage_gaps:
        st.markdown("#### ❌ Coverage Gaps Identified")

        for gap in coverage_gaps:
            st.markdown(f"**{gap}**")

    st.markdown("---")

    # Proposed searches
    proposed_searches = research_plan.get("proposed_searches", [])

    st.markdown("#### 🌐 Proposed Web Searches")
    st.markdown(f"**{len(proposed_searches)} search(es) planned**")

    for i, search in enumerate(proposed_searches, 1):
        with st.expander(
            f"Search {i}: {search.get('query')}"
            f" (Priority: {search.get('priority', 'medium').upper()})",
            expanded=(i == 1)
        ):
            st.markdown(f"**Query:** `{search.get('query')}`")
            st.markdown(f"**Rationale:** {search.get('rationale')}")
            st.markdown(f"**Expected Results:** {search.get('estimated_results', 5)}")
            st.markdown(f"**Priority:** {search.get('priority', 'medium').capitalize()}")

    st.markdown("---")

    # API usage estimate
    estimated_searches = research_plan.get("estimated_total_searches", len(proposed_searches))
    estimated_credits = research_plan.get("estimated_api_credits", estimated_searches)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Searches", estimated_searches)

    with col2:
        st.metric("API Credits", f"~{estimated_credits}")

    st.caption(
        "💡 Tavily free tier: 1,000 searches/month. "
        "This will use " + str(estimated_credits) + " credits."
    )

    st.markdown("---")

    # Approval buttons with session state
    st.markdown("#### 🎯 Your Decision")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve All", type="primary", use_container_width=True, key=f"approve_{session_id}"):
            st.session_state[decision_key] = "approved"
            st.rerun()

    with col2:
        if st.button("❌ Deny (DB Only)", use_container_width=True, key=f"deny_{session_id}"):
            st.session_state[decision_key] = "denied"
            st.rerun()

    with col3:
        if st.button("✏️ Modify (Advanced)", use_container_width=True, key=f"modify_{session_id}"):
            st.info("Modification UI coming soon! For now, approve or deny.")

    return None


def render_web_search_results(
    results: list,
    search_query: str
):
    """
    Render web search results with clear source attribution.

    Args:
        results: List of search result dictionaries
        search_query: The search query that was used
    """
    st.markdown("### 🌐 Web Search Results")

    st.warning(
        f"⚠️ **Not from Your Curated Sources**\n\n"
        f"The following {len(results)} results are from web search. "
        f"Please verify information before relying on it."
    )

    st.caption(f"Search query: `{search_query}`")
    st.markdown("---")

    for i, result in enumerate(results, 1):
        with st.expander(
            f"{i}. {result.get('title', 'Untitled')} "
            f"(Score: {result.get('score', 0):.2f})",
            expanded=(i <= 2)
        ):
            # Title and URL
            url = result.get('url', '')
            if url:
                st.markdown(f"**🔗 [{result.get('title', 'Untitled')}]({url})**")
            else:
                st.markdown(f"**{result.get('title', 'Untitled')}**")

            # Content preview
            content = result.get('content', '')
            if content:
                st.markdown(content[:500] + "..." if len(content) > 500 else content)

            # Metadata
            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption(f"📊 Relevance: {result.get('score', 0):.2%}")

            with col2:
                published = result.get('published_date', 'Unknown')
                st.caption(f"📅 Published: {published}")

            with col3:
                st.caption(f"🏷️ Source: Web Search")

            # Citation
            st.markdown("---")
            st.caption(
                f"**Citation:** {result.get('title', 'Untitled')}. "
                f"Retrieved from {url}"
            )


def render_source_attribution_toggle():
    """
    Render toggle to show/hide web search sources separately.
    """
    return st.checkbox(
        "📌 Show web search results separately",
        value=True,
        help="When enabled, web search results are displayed separately from your trusted database sources"
    )


def render_combined_sources(
    db_sources: list,
    web_sources: list,
    separate: bool = True
):
    """
    Render combined sources with clear separation.

    Args:
        db_sources: List of database sources
        web_sources: List of web search sources
        separate: If True, show in separate sections
    """
    if separate:
        # Separate sections
        if db_sources:
            st.markdown("### 📚 From Your Trusted Database")
            st.success(f"✓ {len(db_sources)} results from your curated sources")

            for i, source in enumerate(db_sources, 1):
                st.markdown(f"{i}. **{source.get('title', 'Untitled')}**")
                st.caption(f"   Author: {source.get('author', 'Unknown')} | {source.get('url', '')}")

            st.markdown("---")

        if web_sources:
            st.markdown("### 🌐 From Web Search")
            st.warning(f"⚠️ {len(web_sources)} results from web search (not from curated sources)")

            for i, source in enumerate(web_sources, 1):
                st.markdown(f"{i}. **{source.get('title', 'Untitled')}**")
                st.caption(
                    f"   Score: {source.get('score', 0):.2f} | "
                    f"Source: Web Search | "
                    f"{source.get('url', '')}"
                )
    else:
        # Combined list with badges
        st.markdown("### 📖 All Sources")

        all_sources = []

        for source in db_sources:
            all_sources.append({**source, 'source_type': 'database'})

        for source in web_sources:
            all_sources.append({**source, 'source_type': 'web_search'})

        for i, source in enumerate(all_sources, 1):
            source_type = source.get('source_type', 'unknown')

            if source_type == 'database':
                badge = "🟢 Trusted DB"
            else:
                badge = "🔴 Web Search"

            st.markdown(f"{i}. **{source.get('title', 'Untitled')}** `{badge}`")
            st.caption(f"   {source.get('url', '')}")
