# Implementation Plan: Web Search & Human-in-the-Loop Research Planner

**Date:** 2025-11-29
**Status:** Planning
**Objective:** Add intelligent web search capability with research planning and human approval

---

## Problem Statement

Currently, after data ingestion, the agent may not have sufficient resources to answer user queries. The system needs:

1. **Web search capability** - Find high-quality educational resources beyond the ingested content
2. **Human-in-the-loop** - Ask users for permission before performing web searches
3. **Research planning** - Analyze existing content, identify gaps, and create a research plan
4. **User approval** - Present the research plan for user review/modification before execution
5. **Proper citations** - Clearly mark web-sourced content as unverified and cite sources

---

## Architecture Overview

### Current Flow (Problem)
```
User Query → Agent → Search DB → Limited Results → Partial/Poor Answer
```

### New Flow (Solution)
```
User Query → Agent → Analyze DB Index → Create Research Plan →
  ↓
Ask User: "Enable web search?" →
  ↓
YES → Present Research Plan → User Approves/Modifies →
  ↓
Execute Web Search → Augment with External Sources →
  ↓
Return Answer with Clear Source Attribution
```

---

## Component Design

### 1. Web Search Tool Integration

**Technology Choice:** Tavily API (recommended from research)

**Reasons:**
- AI-native design for LLM consumption
- Built-in citation support
- Free tier: 1,000 searches/month
- $30/month for 4,000 searches (production)
- Fast response times
- Clean, structured responses

**Alternative/Fallback:** Brave Search API (2,000 free calls/month)

**Implementation:**
- Add new tool `web-search` to `agent/tools.py`
- Wrap Tavily Python SDK
- Return results with full citation metadata
- Mark all results with `source_type: "web_search"` to differentiate from trusted DB sources

### 2. Content Index Analyzer

**Purpose:** Analyze existing database content before deciding what to search for

**New Component:** `agent/research_planner.py`

**Key Functions:**
```python
async def analyze_content_coverage(user_id: str, query: str) -> ContentAnalysis:
    """
    Analyze what content we have vs. what's missing for the query.

    Returns:
    - topics_covered: List of topics we have good coverage on
    - gaps: List of topics/areas with insufficient content
    - existing_sources: List of DB sources found
    - recommended_searches: Suggested web search queries
    """

async def create_research_plan(
    query: str,
    content_analysis: ContentAnalysis,
    user_context: dict
) -> ResearchPlan:
    """
    Create a structured research plan.

    Returns:
    - search_queries: List of web searches to perform
    - rationale: Why each search is needed
    - expected_sources: Type of sources we're looking for
    - db_results: What we already have
    """
```

### 3. Human-in-the-Loop Approval System

**New Phase in Agent Loop:** `PLAN_APPROVAL`

**Flow:**
```
SENSE → PLAN → [CHECK IF WEB SEARCH NEEDED] →
  ↓
  YES → CREATE_RESEARCH_PLAN → PRESENT_TO_USER →
    ↓
    APPROVED → ACT (web search) → OBSERVE → REFLECT → COMPLETE
    ↓
    DENIED → ACT (DB only) → OBSERVE → REFLECT → COMPLETE
    ↓
    MODIFIED → UPDATE_PLAN → ACT (modified) → OBSERVE → REFLECT → COMPLETE
```

**Implementation:**
- Add new action type: `PLAN_APPROVAL` to planning prompt
- Extend `AgentController` to handle approval workflow
- Store plan in session state
- Return plan to user via Streamlit
- Accept user input: APPROVE / DENY / MODIFY

### 4. Database Schema Extensions

**New Table:** `research_plans`

```sql
CREATE TABLE research_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    content_analysis JSONB NOT NULL,
    search_queries JSONB NOT NULL,
    status TEXT CHECK (status IN ('pending', 'approved', 'denied', 'modified')),
    user_modifications JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ
);
```

**New Table:** `web_search_results`

```sql
CREATE TABLE web_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    research_plan_id UUID REFERENCES research_plans(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    results JSONB NOT NULL,
    source_api TEXT NOT NULL, -- 'tavily', 'brave', etc.
    searched_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### 5. UI Extensions (Streamlit Dashboard)

**New Component:** `dashboard/components/research_planner_ui.py`

**Features:**
1. **Research Plan Viewer**
   - Show content analysis (what we have vs. gaps)
   - Display proposed web search queries with rationale
   - Estimated number of searches needed

2. **Approval Controls**
   - ✅ Approve All button
   - ❌ Deny (use DB only) button
   - ✏️ Modify button (opens editor)

3. **Query Editor**
   - Edit/add/remove search queries
   - Adjust search parameters

4. **Results Display**
   - Clear separation: "From Your Trusted Sources" vs. "From Web Search"
   - Citation display with source URLs
   - Warning banner: "⚠️ Web results are not from your curated sources"

---

## Implementation Phases

### Phase 1: Web Search Tool (MVP)
**Estimated Time:** 2-3 hours
**Files to Create/Modify:**
- `agent/tools.py` - Add web-search tool
- `.env` - Add TAVILY_API_KEY
- `requirements.txt` - Add tavily-python

**Tasks:**
1. Install Tavily Python SDK
2. Implement `_web_search_schema()` in ToolRegistry
3. Implement `_execute_web_search()` method
4. Add to available tools list
5. Test basic web search functionality

**Success Criteria:**
- Agent can call web-search tool
- Returns structured results with citations
- Logs show web search execution

### Phase 2: Content Analyzer
**Estimated Time:** 3-4 hours
**Files to Create/Modify:**
- `agent/research_planner.py` (new)
- `agent/tools.py` - Add analyze-content-coverage tool

**Tasks:**
1. Create ContentAnalysis dataclass
2. Implement DB content indexing logic
3. Implement gap detection algorithm
4. Generate recommended search queries based on gaps
5. Unit tests for analyzer

**Success Criteria:**
- Can analyze DB content for a given query
- Identifies coverage gaps accurately
- Generates relevant search query suggestions

### Phase 3: Research Plan Creation
**Estimated Time:** 2-3 hours
**Files to Create/Modify:**
- `agent/research_planner.py` - Add plan creation
- `agent/prompts/research_planning.txt` (new)

**Tasks:**
1. Create ResearchPlan dataclass
2. Implement plan creation logic with LLM
3. Create research planning prompt
4. Format plan for user presentation

**Success Criteria:**
- Generates structured research plans
- Plans include rationale and expected outcomes
- Plans are human-readable

### Phase 4: Human-in-the-Loop Workflow
**Estimated Time:** 4-5 hours
**Files to Create/Modify:**
- `agent/controller.py` - Add approval phase
- `agent/prompts/planning.txt` - Add PLAN_APPROVAL action
- `database/migrations/006_research_tables.sql` (new)

**Tasks:**
1. Create database migration for new tables
2. Extend AgentController with approval workflow
3. Add PLAN_APPROVAL action type
4. Implement plan storage and retrieval
5. Handle user responses (approve/deny/modify)

**Success Criteria:**
- Agent pauses for approval when web search needed
- Stores plan in database
- Resumes execution after approval
- Handles denials gracefully

### Phase 5: Streamlit UI Integration
**Estimated Time:** 3-4 hours
**Files to Create/Modify:**
- `dashboard/components/research_planner_ui.py` (new)
- `dashboard/views/agent.py` - Integrate approval UI

**Tasks:**
1. Create research plan viewer component
2. Add approval buttons and workflow
3. Create query editor interface
4. Add source attribution display
5. Style with clear visual separation

**Success Criteria:**
- Research plan displays clearly
- User can approve/deny/modify
- Results show clear source attribution
- Web results have warning banner

### Phase 6: Citation Management
**Estimated Time:** 2 hours
**Files to Create/Modify:**
- `agent/prompts/planning.txt` - Add citation requirements
- `agent/prompts/reflection.txt` - Add citation validation
- `dashboard/views/agent.py` - Enhance citation display

**Tasks:**
1. Update prompts to emphasize citations
2. Add citation validation in reflection phase
3. Enhance UI citation display
4. Add "From Web Search" badges

**Success Criteria:**
- All web results include citations
- Citations are validated
- UI clearly distinguishes source types

---

## Configuration

### New Environment Variables

```bash
# Web Search Configuration
TAVILY_API_KEY=tvly-xxxxx
BRAVE_API_KEY=xxxxx  # Fallback
WEB_SEARCH_ENABLED=true
WEB_SEARCH_MAX_RESULTS=5

# Research Planner Configuration
REQUIRE_RESEARCH_APPROVAL=true
AUTO_ANALYZE_CONTENT=true
MIN_DB_RESULTS_THRESHOLD=3  # If < 3 results, suggest web search
```

### Agent Configuration Updates

```python
@dataclass
class AgentConfig:
    max_iterations: int = 10
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    log_level: str = "INFO"

    # New web search configs
    web_search_enabled: bool = True
    require_research_approval: bool = True
    min_db_results_threshold: int = 3
    web_search_max_results: int = 5
```

---

## Tool Schema: web-search

```python
def _web_search_schema(self) -> Dict[str, Any]:
    """Schema for web-search tool."""
    return {
        "name": "web-search",
        "description": "Search the web for educational content when database doesn't have sufficient information. Requires user approval. Returns results with full citations.",
        "input_schema": {
            "query": "string (search query)",
            "max_results": "integer (1-10, default: 5)",
            "search_depth": "string ('basic' or 'advanced', default: 'basic')",
            "include_domains": "array of strings (optional, e.g., ['edu', 'org'])",
        },
        "output_schema": {
            "results": "array of objects with title, content, url, published_date, score",
            "source_api": "string (which API was used)",
            "citations": "array of citation objects"
        },
        "requires_approval": True,  # Special flag
        "example": {
            "input": {
                "query": "transformer architecture attention mechanism tutorials",
                "max_results": 5,
                "include_domains": ["edu", "org"]
            },
            "output": {
                "results": [
                    {
                        "title": "Illustrated Transformer",
                        "content": "Visual explanation...",
                        "url": "https://...",
                        "score": 0.95
                    }
                ],
                "source_api": "tavily",
                "citations": [...]
            }
        }
    }
```

---

## Tool Schema: analyze-content-coverage

```python
def _analyze_content_coverage_schema(self) -> Dict[str, Any]:
    """Schema for analyze-content-coverage tool."""
    return {
        "name": "analyze-content-coverage",
        "description": "Analyze existing database content to identify what we have and what's missing for a given query",
        "input_schema": {
            "query": "string (user's learning query)",
            "user_id": "string (UUID)"
        },
        "output_schema": {
            "db_results_count": "integer",
            "topics_covered": "array of strings",
            "coverage_gaps": "array of gap objects",
            "recommended_searches": "array of search query suggestions",
            "needs_web_search": "boolean"
        }
    }
```

---

## Prompt Updates

### Planning Prompt Addition

```markdown
## Web Search Decision Process

Before answering a user query:

1. First call `analyze-content-coverage` to check database
2. If `needs_web_search` is true:
   - Create a research plan
   - Return action type: PLAN_APPROVAL
   - Include research plan in output
3. Wait for user approval
4. If approved, call `web-search` with approved queries
5. Combine DB results + web results in final answer

## PLAN_APPROVAL Action Type

Use this when you need user permission for web search:

```json
{
  "action_type": "PLAN_APPROVAL",
  "research_plan": {
    "query": "original user query",
    "db_results": {...},
    "proposed_searches": [
      {
        "query": "specific search query",
        "rationale": "why this search is needed",
        "estimated_results": 5
      }
    ],
    "estimated_total_searches": 2
  },
  "reasoning": "Database has insufficient content on X. Requesting approval to search web for..."
}
```

### Reflection Prompt Addition

```markdown
## Citation Validation

When web search results are included:

1. Verify each result has a citation with URL
2. Check that sources are clearly marked as "web search"
3. Ensure no mixing of trusted DB sources with unverified web sources
4. Validate that citations are properly formatted
```

---

## Example User Flow

### Scenario: User asks about a topic not in DB

```
1. User: "Help me understand quantum computing basics"

2. Agent SENSE: Gathers user context (Week 7, intermediate level)

3. Agent PLAN: Decides to analyze content coverage
   Action: analyze-content-coverage

4. Agent ACT: Executes analysis
   Result: {
     "db_results_count": 1,
     "coverage_gaps": ["quantum gates", "superposition", "entanglement"],
     "needs_web_search": true,
     "recommended_searches": [
       "quantum computing tutorials for beginners",
       "quantum gates explained visually"
     ]
   }

5. Agent REFLECT: "Only 1 result in DB, insufficient for good answer"

6. Agent PLAN:
   Action: PLAN_APPROVAL
   Research Plan: {
     "db_results": "Found 1 article on quantum basics",
     "gaps": ["quantum gates", "superposition", "entanglement"],
     "proposed_searches": [
       {
         "query": "quantum computing tutorials for beginners site:edu",
         "rationale": "Need beginner-friendly explanations",
         "estimated_results": 5
       },
       {
         "query": "quantum gates visual explanation",
         "rationale": "User prefers visual content, need gate diagrams",
         "estimated_results": 5
       }
     ],
     "estimated_total_searches": 2
   }

7. UI Shows:
   ┌─────────────────────────────────────────────────┐
   │ 🔍 Research Plan Requires Approval              │
   ├─────────────────────────────────────────────────┤
   │ Your Database Coverage:                         │
   │ ✓ 1 article found on quantum basics             │
   │                                                 │
   │ Coverage Gaps Identified:                       │
   │ ❌ Quantum gates                                │
   │ ❌ Superposition                                │
   │ ❌ Entanglement                                 │
   │                                                 │
   │ Proposed Web Searches:                          │
   │ 1. "quantum computing tutorials for beginners   │
   │     site:edu"                                   │
   │    → Need beginner-friendly explanations        │
   │                                                 │
   │ 2. "quantum gates visual explanation"           │
   │    → User prefers visual content, need diagrams │
   │                                                 │
   │ Estimated searches: 2 (10 total results)        │
   │                                                 │
   │ ⚠️ Web results are not from your curated        │
   │    sources and may need verification.           │
   │                                                 │
   │ [✅ Approve] [❌ Deny] [✏️ Modify]              │
   └─────────────────────────────────────────────────┘

8. User clicks "✅ Approve"

9. Agent ACT: Executes web searches
   - Calls web-search for query 1
   - Calls web-search for query 2

10. Agent OBSERVE: Got 10 high-quality results with citations

11. Agent REFLECT: "Good mix of DB + web content, ready to synthesize"

12. Agent PLAN: COMPLETE with combined results

13. UI Shows:
    ┌────────────────────────────────────────────┐
    │ 📚 From Your Trusted Sources (1)           │
    │ • Quantum Basics Overview                  │
    │                                            │
    │ 🌐 From Web Search (10)                    │
    │ ⚠️ Not from your curated sources           │
    │                                            │
    │ • Introduction to Quantum Computing        │
    │   [MIT OpenCourseWare]                     │
    │   📎 https://ocw.mit.edu/...               │
    │                                            │
    │ • Visual Guide to Quantum Gates            │
    │   [Quantum Computing UK]                   │
    │   📎 https://quantumcomputinguk.org/...    │
    │   ...                                      │
    └────────────────────────────────────────────┘
```

---

## Testing Strategy

### Unit Tests

```python
# test_web_search_tool.py
def test_web_search_basic():
    """Test basic web search functionality"""

def test_web_search_with_domain_filter():
    """Test domain filtering (edu, org)"""

def test_web_search_citation_format():
    """Test citation structure and completeness"""

# test_research_planner.py
def test_content_analysis_with_gaps():
    """Test gap detection when DB has insufficient content"""

def test_content_analysis_sufficient_coverage():
    """Test when DB has enough content (no web search needed)"""

def test_research_plan_creation():
    """Test research plan generation"""

# test_approval_workflow.py
def test_approval_request_generation():
    """Test PLAN_APPROVAL action creation"""

def test_approval_granted():
    """Test agent resumes after approval"""

def test_approval_denied():
    """Test agent uses DB-only after denial"""

def test_plan_modification():
    """Test agent handles modified plans"""
```

### Integration Tests

```python
# test_e2e_web_search.py
async def test_full_web_search_flow():
    """
    End-to-end test:
    1. Query with insufficient DB content
    2. Analyze content
    3. Create research plan
    4. Request approval
    5. Auto-approve
    6. Execute web search
    7. Return combined results
    """
```

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Tavily API rate limits | High | Medium | Implement rate limiting, add Brave fallback, cache results |
| Web search returns low-quality sources | Medium | Medium | Domain filtering (edu, org), quality scoring, user feedback |
| User ignores approval modal | Low | Low | Clear UI, sensible defaults, timeout behavior |
| Cost overruns from excessive searches | Medium | Low | Set max searches per session, monthly budget alerts |
| Citation formatting errors | Low | Medium | Structured citation schema, validation, tests |

---

## Success Criteria

### Technical Metrics
- [ ] Web search tool successfully integrated
- [ ] Content analyzer detects gaps accurately (>90% precision)
- [ ] Research plans are well-formed and actionable
- [ ] Approval workflow functions correctly
- [ ] Citations are complete and properly formatted
- [ ] UI clearly separates DB vs web sources

### User Experience Metrics
- [ ] Users understand the approval prompt
- [ ] Research plans are helpful and clear
- [ ] Source attribution is obvious and trustworthy
- [ ] Agent provides better answers with web search enabled
- [ ] <2 second response time for web searches

### Quality Metrics
- [ ] Web search results are relevant (>80% relevance score)
- [ ] Citations are accurate (100% have valid URLs)
- [ ] No mixing of source types without clear labels
- [ ] User satisfaction with answer quality increases

---

## Future Enhancements (Out of Scope)

1. **Multi-source aggregation** - Combine multiple search APIs
2. **Smart caching** - Cache popular search results
3. **Source quality scoring** - ML model to rank source reliability
4. **Automatic domain trust lists** - User can pre-approve domains
5. **Budget management** - Track API costs per user
6. **Search result deduplication** - Detect similar web + DB results
7. **Federated search** - Search academic databases (arXiv, PubMed)

---

## Dependencies

### New Python Packages

```
tavily-python==0.5.0
brave-search-python==0.2.0  # Fallback
```

### API Keys Required

```
TAVILY_API_KEY - Get from https://tavily.com (1,000 free searches/month)
BRAVE_API_KEY - Get from https://brave.com/search/api/ (2,000 free/month)
```

---

## Rollout Plan

### Development (Week 1)
- Implement Phase 1-3 (web search + analyzer + planner)
- Unit tests
- Local testing

### Staging (Week 2)
- Implement Phase 4-5 (approval workflow + UI)
- Integration tests
- User acceptance testing with 5 beta users

### Production (Week 3)
- Deploy with feature flag `WEB_SEARCH_ENABLED=false`
- Enable for 10% of users
- Monitor costs and quality
- Gradual rollout to 50%, then 100%

---

## Cost Estimates

### Tavily Pricing
- Free tier: 1,000 searches/month
- Project Plan: $30/month (4,000 searches)
- Estimated usage: ~500 searches/month with 50 active users
- **Cost:** FREE (within free tier)

### Brave Search (Fallback)
- Free tier: 2,000 searches/month
- **Cost:** FREE

### Development Time
- Phase 1-6: ~20 hours
- Testing: ~5 hours
- Documentation: ~3 hours
- **Total:** ~28 hours (~1 week)

---

## Open Questions

1. **Q:** Should we allow web search without approval for trusted query patterns?
   **A:** No for MVP. Add auto-approval rules in v2.

2. **Q:** How many web search results should we fetch per query?
   **A:** Default to 5, max 10. Configurable per user.

3. **Q:** Should we store web search results in DB for reuse?
   **A:** Yes, in `web_search_results` table. Cache for 7 days.

4. **Q:** What happens if both Tavily and Brave APIs fail?
   **A:** Graceful degradation - return DB-only results with notice.

5. **Q:** Should research plan show estimated API costs?
   **A:** Yes for v2. Display "~2 API credits" in approval UI.

---

## References

- [Tavily API Documentation](https://docs.tavily.com)
- [Brave Search API Docs](https://brave.com/search/api/)
- [Web Search Research Report](./.claude/tasks/web-search-research-2025.md)
- [Agent Implementation Plan](./agentic-learning-coach-implementation-plan.md)

---

## Approval Checklist

Before starting implementation:

- [ ] Plan reviewed by stakeholder
- [ ] API keys obtained (Tavily + Brave)
- [ ] Database migration reviewed
- [ ] UI mockups approved
- [ ] Testing strategy agreed upon
- [ ] Cost estimates accepted
- [ ] Timeline feasible

---

**Next Steps:**
1. Review this plan
2. Approve/modify
3. Begin Phase 1 implementation
4. Create feature branch: `feature/web-search-research-planner`
