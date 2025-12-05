# Complete Refactoring Migration Plan

**Created:** 2025-12-04
**Status:** Draft - Awaiting Approval
**Goal:** Fully migrate to new refactored codebase in `src/`, remove legacy code, clean up repo
**Estimated Timeline:** 2-3 days (aggressive MVP approach)

---

## Executive Summary

### Current State

**Refactored Code (in `src/`, not yet integrated):**
- ✅ **Phase 1-2-3 Complete:** Core infrastructure, Agent system, RAG foundations
- ✅ **103+ tests passing** for refactored code
- ⚠️ **NOT yet integrated** - old code still in use

**Legacy Code (currently active):**
- `agent/` (5 files, ~1,490 lines) - Used by dashboard
- `learning-coach-mcp/src/` (26+ files, ~6,758 lines) - Used by MCP server
- **Total legacy code:** ~8,248 lines to migrate/remove

**The Problem:**
- Two parallel codebases exist
- Old code actively used by dashboard & MCP server
- New refactored code not integrated
- Confusing for developers

### Migration Goal

**Complete migration to `src/` structure:**
```
OLD:
├── agent/                    ❌ Remove
├── learning-coach-mcp/src/   ❌ Refactor & slim down
└── src/                      ⚠️ Not integrated

NEW:
├── src/                      ✅ Primary codebase
│   ├── core/
│   ├── agent/
│   ├── rag/
│   ├── ingestion/
│   ├── ui/
│   ├── tools/
│   └── database/
├── learning-coach-mcp/        ✅ MCP server only
│   └── server.py
└── dashboard/                 ✅ Streamlit UI (imports from src/)
```

---

## Detailed Analysis

### What's Been Refactored (Phases 1-3) ✅

| Component | Old Location | New Location | Status | Tests |
|-----------|-------------|--------------|--------|-------|
| **Core Infrastructure** | N/A | `src/core/` | ✅ Complete | 19 |
| **Agent Controllers** | `agent/controller.py` (736L) | `src/agent/controllers/` | ✅ Complete | 26 |
| **Agent Tools** | `agent/tools.py` (754L) | `src/agent/tools/` | ✅ Complete | 19 |
| **Agent Models** | Mixed | `src/agent/models/` | ✅ Complete | - |
| **RAG Core** | N/A | `src/rag/core/` | ✅ Complete | 12 |
| **RAG Synthesis** | `learning-coach-mcp/src/rag/synthesizer.py` | `src/rag/synthesis/` | ✅ Complete | 11 |
| **RAG Evaluation** | `learning-coach-mcp/src/rag/evaluator.py` | `src/rag/evaluation/` | ✅ Complete | 16 |
| **RAG Retrieval** | `learning-coach-mcp/src/rag/retriever.py` | `src/rag/retrieval/` | ✅ Complete | - |

**Total Refactored:** 103+ tests, ~4,360 lines

### What Needs Migration (Missing)

| Component | Old Location | Lines | New Location | Priority |
|-----------|-------------|-------|--------------|----------|
| **DigestGenerator** | `learning-coach-mcp/src/rag/digest_generator.py` | 417 | `src/rag/digest/` | 🔴 Critical |
| **Agent Logger** | `agent/logger.py` | ? | `src/agent/utils/` | 🟡 Medium |
| **Research Planner** | `agent/research_planner.py` | ? | `src/agent/planning/` | 🟡 Medium |
| **Ingestion System** | `learning-coach-mcp/src/ingestion/` | ~800 | `src/ingestion/` | 🟢 Low |
| **UI Templates** | `learning-coach-mcp/src/ui/` | ~300 | `src/ui/` | 🟢 Low |
| **Tools** | `learning-coach-mcp/src/tools/` | ~400 | `src/tools/` | 🟢 Low |
| **DB Utilities** | `learning-coach-mcp/src/utils/db.py` | ~100 | `src/database/` | 🟡 Medium |
| **Config** | `learning-coach-mcp/src/config.py` | ~50 | `src/core/config.py` | 🟡 Medium |

**Total To Migrate:** ~2,067 lines

### What Uses Old Code (Import Dependencies)

**Dashboard (`dashboard/`):**
```python
# dashboard/views/agent.py (line 313, 353)
from agent.tools import ToolRegistry           ❌ OLD
from agent.controller import AgentController    ❌ OLD

# MUST CHANGE TO:
from src.agent.tools.registry import ToolRegistry           ✅ NEW
from src.agent.controllers.agent_controller import AgentController  ✅ NEW
```

**MCP Server (`learning-coach-mcp/src/server.py`):**
```python
# learning-coach-mcp/src/server.py (line 68)
from .rag.digest_generator import DigestGenerator  ❌ OLD

# MUST CHANGE TO:
from src.rag.digest import DigestGenerator  ✅ NEW
```

**Tests (`tests/integration/`):**
- 5 test files use `from agent.X` imports
- Need to update to `from src.agent.X`

---

## Migration Strategy

### Option A: Big Bang Migration (RECOMMENDED for clean break)
**Timeline:** 2-3 days
**Approach:** Complete all missing pieces, update all imports, remove old code in one go
**Pros:** Clean, no dual maintenance, forces completion
**Cons:** Higher risk, needs thorough testing

### Option B: Incremental Migration
**Timeline:** 4-6 weeks
**Approach:** Module by module, maintain backward compatibility
**Pros:** Lower risk, gradual rollout
**Cons:** Temporary complexity, dual maintenance

**RECOMMENDATION:** **Option A (Big Bang)** - Given user wants "fully migrate" and "remove legacy code", and we already have 103+ tests passing for refactored code.

---

## Execution Plan (Option A - Big Bang)

### Phase 1: Complete Missing Refactoring (Day 1, 4-6 hours)

#### 1.1 Critical: DigestGenerator ✅
**Goal:** Move DigestGenerator to `src/rag/digest/`

**Tasks:**
1. Create `src/rag/digest/digest_generator.py`
2. Refactor to use new imports:
   ```python
   # OLD imports
   from rag.query_builder import QueryBuilder
   from rag.retriever import VectorRetriever
   from rag.synthesizer import EducationalSynthesizer

   # NEW imports
   from src.rag.retrieval import QueryBuilder, VectorRetriever
   from src.rag.synthesis import EducationalSynthesizer
   from src.rag.evaluation import RAGASEvaluator
   ```
3. Update `src/rag/digest/__init__.py` to export DigestGenerator
4. Write tests: `tests/unit/rag/digest/test_digest_generator.py`

**Estimated Time:** 2 hours

#### 1.2 Medium: Agent Support Files
**Goal:** Move remaining agent files to `src/agent/`

**Tasks:**
1. Move `agent/logger.py` → `src/agent/utils/logger.py`
2. Move `agent/research_planner.py` → `src/agent/planning/research_planner.py`
3. Update imports internally
4. Write/update tests

**Estimated Time:** 1 hour

#### 1.3 Medium: Database & Config
**Goal:** Consolidate database and config utilities

**Tasks:**
1. Move `learning-coach-mcp/src/utils/db.py` → `src/database/client.py`
2. Merge `learning-coach-mcp/src/config.py` into `src/core/config.py`
3. Update exports in `__init__.py` files

**Estimated Time:** 1 hour

#### 1.4 Low Priority: Ingestion, UI, Tools (Optional for MVP)
**Goal:** Move remaining modules (can defer to Phase 2 if time-constrained)

**Tasks:**
1. Move `learning-coach-mcp/src/ingestion/` → `src/ingestion/`
2. Move `learning-coach-mcp/src/ui/` → `src/ui/`
3. Move `learning-coach-mcp/src/tools/` → `src/tools/`
4. Update imports

**Estimated Time:** 2 hours (or defer)

**Phase 1 Total:** 4-6 hours

---

### Phase 2: Update All Imports (Day 1-2, 2-3 hours)

#### 2.1 Update Dashboard
**File:** `dashboard/views/agent.py`

**Changes:**
```python
# Line 313
- from agent.tools import ToolRegistry
+ from src.agent.tools.registry import ToolRegistry

# Line 353
- from agent.controller import AgentController, AgentConfig
+ from src.agent.controllers.agent_controller import AgentController
+ from src.agent.models.agent_config import AgentConfig
```

**Test:** Run dashboard: `streamlit run dashboard/app.py`

**Estimated Time:** 30 minutes

#### 2.2 Update MCP Server
**File:** `learning-coach-mcp/src/server.py`

**Changes:**
```python
# Line 68
- from .rag.digest_generator import DigestGenerator
+ from src.rag.digest import DigestGenerator

# Other RAG imports (if any)
- from .rag.X import Y
+ from src.rag.X import Y
```

**Test:** Run MCP server: `fastmcp dev learning-coach-mcp/src/server.py`

**Estimated Time:** 30 minutes

#### 2.3 Update Tests
**Files:** `tests/integration/agent/*.py`, `tests/integration/rag/*.py`

**Changes:**
```python
- from agent.controller import AgentController
+ from src.agent.controllers.agent_controller import AgentController

- from agent.tools import ToolRegistry
+ from src.agent.tools.registry import ToolRegistry
```

**Test:** Run test suite: `pytest tests/`

**Estimated Time:** 1 hour

#### 2.4 Update Any Other Imports
**Search:** `grep -r "from agent\." --include="*.py"`
**Search:** `grep -r "from learning-coach-mcp.src.rag" --include="*.py"`

**Fix:** All remaining old imports

**Estimated Time:** 1 hour

**Phase 2 Total:** 2-3 hours

---

### Phase 3: Test Everything (Day 2, 3-4 hours)

#### 3.1 Unit Tests
```bash
pytest tests/unit/ -v
```
**Expected:** All tests pass (currently 109/110)

#### 3.2 Integration Tests
```bash
pytest tests/integration/ -v
```
**Expected:** All tests pass

#### 3.3 Dashboard Manual Test
```bash
streamlit run dashboard/app.py
```
**Test Cases:**
- [ ] Agent view loads
- [ ] Can create agent with tools
- [ ] Agent executes successfully
- [ ] Results display correctly

#### 3.4 MCP Server Manual Test
```bash
fastmcp dev learning-coach-mcp/src/server.py
```
**Test Cases:**
- [ ] Server starts without errors
- [ ] `generate_daily_digest` tool works
- [ ] RAG pipeline executes
- [ ] Digest returns properly

#### 3.5 E2E Test
```bash
pytest tests/e2e/test_full_workflow.py -v
```
**Expected:** Full workflow completes

**Phase 3 Total:** 3-4 hours

---

### Phase 4: Remove Legacy Code (Day 2-3, 2 hours)

#### 4.1 Remove Old Agent Directory
```bash
# Backup first (optional)
git mv agent/ .archive/agent-old/

# Or delete directly
git rm -rf agent/
```

**Files to Remove:**
- `agent/controller.py` (736 lines) - ✅ Replaced by `src/agent/controllers/`
- `agent/tools.py` (754 lines) - ✅ Replaced by `src/agent/tools/`
- `agent/logger.py` - ✅ Replaced by `src/agent/utils/logger.py`
- `agent/research_planner.py` - ✅ Replaced by `src/agent/planning/`
- `agent/__init__.py`
- `agent/prompts/` - ✅ Check if used, may need to keep or migrate

**Verify:** No remaining imports from `agent/`

#### 4.2 Clean Up learning-coach-mcp/src/
```bash
# Remove migrated RAG components
git rm learning-coach-mcp/src/rag/synthesizer.py
git rm learning-coach-mcp/src/rag/evaluator.py
git rm learning-coach-mcp/src/rag/retriever.py
git rm learning-coach-mcp/src/rag/query_builder.py
git rm learning-coach-mcp/src/rag/insight_search.py
git rm learning-coach-mcp/src/rag/digest_generator.py

# Remove if migrated
git rm learning-coach-mcp/src/utils/db.py  (if migrated to src/database/)
git rm learning-coach-mcp/src/config.py    (if merged to src/core/config.py)

# Remove if migrated (optional)
git rm -rf learning-coach-mcp/src/ingestion/  (if moved to src/ingestion/)
git rm -rf learning-coach-mcp/src/ui/         (if moved to src/ui/)
git rm -rf learning-coach-mcp/src/tools/      (if moved to src/tools/)
```

**Result:**
```
learning-coach-mcp/
├── src/
│   ├── server.py          ✅ Keep (MCP server entrypoint)
│   ├── db/                ✅ Keep (database migrations)
│   └── integrations/      ✅ Keep (external integrations)
└── tests/                 ✅ Keep (MCP-specific tests)
```

#### 4.3 Update Project Structure Docs
**Files to Update:**
- `README.md` - Update architecture diagrams
- `CONTRIBUTING.md` - Update development guide
- `docs/CODEBASE_GUIDE.md` - Update structure reference

**Estimated Time:** 30 minutes

**Phase 4 Total:** 2 hours

---

### Phase 5: Final Verification & Cleanup (Day 3, 2 hours)

#### 5.1 Full Test Suite
```bash
# Run ALL tests
pytest tests/ -v --tb=short

# Check coverage
pytest tests/ --cov=src --cov-report=html
```

**Expected:** >85% coverage

#### 5.2 Manual Smoke Tests
- [ ] Start dashboard - works
- [ ] Run agent workflow - completes
- [ ] Start MCP server - works
- [ ] Generate digest - succeeds
- [ ] View digest in dashboard - displays

#### 5.3 Code Quality Checks
```bash
# Type checking
mypy src/

# Linting (if configured)
ruff check src/

# Format check (if configured)
black --check src/
```

#### 5.4 Documentation Updates
- [ ] Update README.md with new structure
- [ ] Update QUICK_START.md if needed
- [ ] Create MIGRATION_COMPLETE.md summary
- [ ] Archive old refactoring docs to docs/archive/

**Phase 5 Total:** 2 hours

---

## Success Criteria

### Functional Requirements ✅
- [ ] Dashboard loads and runs without errors
- [ ] Agent executes workflows successfully
- [ ] MCP server starts and serves tools
- [ ] DigestGenerator produces valid output
- [ ] All integration tests pass
- [ ] E2E workflow completes

### Code Quality ✅
- [ ] All unit tests pass (>100 tests)
- [ ] All integration tests pass
- [ ] No imports from old `agent/` directory
- [ ] No imports from old `learning-coach-mcp/src/rag/` (except server.py)
- [ ] Type checking passes (mypy)
- [ ] Test coverage >85%

### Codebase Cleanliness ✅
- [ ] Old `agent/` directory removed
- [ ] Old RAG files in `learning-coach-mcp/src/rag/` removed
- [ ] Only `src/` used for core logic
- [ ] `learning-coach-mcp/` contains only server entrypoint
- [ ] Clear, single source of truth

### Documentation ✅
- [ ] README.md updated
- [ ] Architecture diagrams updated
- [ ] Migration complete summary written
- [ ] All devs can understand new structure

---

## Risk Mitigation

### Risk 1: Breaking Changes During Migration
**Mitigation:**
- Work on a feature branch: `git checkout -b migrate-to-src`
- Commit after each phase
- Run tests after every change
- Keep old code until fully verified

**Rollback Plan:**
```bash
git checkout main  # Return to working state
```

### Risk 2: Missing Functionality
**Mitigation:**
- Comprehensive test coverage before removing code
- Manual testing checklist
- Compare old vs new functionality
- Keep archived copy for 1 week

**Recovery:**
```bash
git checkout main -- agent/  # Restore old code if needed
```

### Risk 3: Import Path Issues
**Mitigation:**
- Use find/replace carefully
- Search for all variations: `from agent`, `import agent`
- Test imports in isolation before running
- Update PYTHONPATH if needed

**Check:**
```bash
python -c "from src.agent.controllers import AgentController; print('OK')"
```

### Risk 4: Performance Degradation
**Mitigation:**
- Benchmark before migration
- Benchmark after migration
- Compare response times
- Profile if issues found

**Benchmark:**
```bash
time pytest tests/integration/test_agent_basic.py
```

---

## Timeline Summary

| Phase | Task | Duration | Day |
|-------|------|----------|-----|
| **Phase 1** | Complete missing refactoring | 4-6 hours | Day 1 |
| **Phase 2** | Update all imports | 2-3 hours | Day 1-2 |
| **Phase 3** | Test everything | 3-4 hours | Day 2 |
| **Phase 4** | Remove legacy code | 2 hours | Day 2-3 |
| **Phase 5** | Final verification | 2 hours | Day 3 |
| **TOTAL** | | **13-17 hours** | **2-3 days** |

**Aggressive MVP:** Focus on critical path (DigestGenerator, imports, testing) = 1-2 days
**Thorough Migration:** Include all components (ingestion, ui, tools) = 2-3 days

---

## Alternative Approaches (Not Recommended)

### Alternative 1: Keep Both Structures
**Why Not:** Confusing, dual maintenance, defeats purpose

### Alternative 2: Gradual Module-by-Module
**Why Not:** User wants "fully migrate" and "remove legacy", implies clean break

### Alternative 3: Start Fresh
**Why Not:** 103 tests already passing, good refactoring work done

---

## Post-Migration Maintenance

### Week 1 After Migration
- Monitor for issues
- Fix any bugs found
- Update documentation based on feedback

### Month 1 After Migration
- Review code quality
- Identify tech debt
- Plan Phase 4-7 refactoring (if desired)

### Ongoing
- Keep tests green
- Maintain >85% coverage
- Continue modular patterns

---

## Approval Checklist

Before proceeding, confirm:
- [ ] Understand current state (2 parallel codebases)
- [ ] Understand migration goal (single `src/` structure)
- [ ] Accept 2-3 day timeline for complete migration
- [ ] Willing to test thoroughly before removing old code
- [ ] Understand rollback plan if issues arise
- [ ] Ready to update any external documentation/integrations

---

## Next Steps After Approval

1. **Create feature branch:** `git checkout -b migrate-to-src`
2. **Start Phase 1:** Complete missing refactoring (DigestGenerator, etc.)
3. **Continuous testing:** Run tests after each file migration
4. **Phase by phase:** Complete each phase before moving to next
5. **Final verification:** Full test suite + manual smoke tests
6. **Merge:** Once verified, merge to main
7. **Document:** Write migration complete summary

---

## Questions for User

Before starting, please confirm:

1. **MVP vs Complete:**
   - MVP: Migrate critical path only (DigestGenerator, core agent, RAG) = 1-2 days
   - Complete: Migrate everything including ingestion, ui, tools = 2-3 days
   - **Which do you prefer?**

2. **Testing:**
   - Do you have a staging environment to test before production?
   - Are all tests currently passing?

3. **Dependencies:**
   - Any external integrations that import from old structure?
   - Any CI/CD that needs updating?

---

**Ready to start migration?** 🚀

**Recommendation:** Start with **MVP approach** - critical path only, can migrate remaining components later if needed.
