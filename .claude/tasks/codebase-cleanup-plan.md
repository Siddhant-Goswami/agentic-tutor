# Codebase Cleanup Plan

**Created:** 2025-12-04
**Status:** Draft - Awaiting Approval
**Goal:** Remove unused files and code while preserving all active functionality

---

## Current State Analysis

### Directory Structure Overview

```
agentic-tutor/
├── agent/                          ✅ ACTIVE - Used by dashboard & MCP
├── src/                            ⚠️  PARTIAL - Phase 1-2 refactoring (not fully integrated)
├── learning-coach-mcp/             ✅ ACTIVE - RAG system, MCP server
├── dashboard/                      ✅ ACTIVE - Streamlit UI
├── database/                       ✅ ACTIVE - SQL migrations
├── tests/                          ✅ ACTIVE - Organized test suite
├── docs/                           ✅ ACTIVE - Documentation
├── examples/                       ✅ ACTIVE - Demo code
├── [20+ test files at root]       ❌ DEPRECATED - Move to tests/
├── [15+ .md docs at root]          ⚠️  MIXED - Archive historical ones
└── [Various utility scripts]       ⚠️  EVALUATE - Keep useful ones
```

### Import Analysis

**Active Imports (KEEP):**
- `from agent.controller import AgentController` (dashboard, MCP)
- `from agent.tools import ToolRegistry` (dashboard)
- `from learning-coach-mcp.src.rag.*` (multiple modules)
- `from learning-coach-mcp.src.ingestion.*` (orchestrator, embedder)

**Unused Imports (INVESTIGATE):**
- `from src.agent.*` - New structure, not yet integrated
- `from src.core.*` - New structure, not yet integrated
- `from src.rag.*` - New structure, not yet created

---

## Cleanup Categories

### Category 1: Test Files at Root (MOVE → tests/)

**Files to Move:**
```
./test_agent_comprehensive.py       → tests/integration/test_agent_workflow.py
./test_agent_digest.py              → tests/integration/test_agent_digest.py
./test_agent.py                     → tests/unit/agent/test_agent_basic.py
./test_approval_ui_workflow.py      → tests/integration/test_approval_workflow.py
./test_content_extraction.py        → tests/unit/ingestion/test_content_extraction.py
./test_db_direct.py                 → tests/integration/test_database.py
./test_digest_generation_simple.py  → tests/integration/test_digest_simple.py
./test_digest_init.py               → tests/unit/rag/test_digest_init.py
./test_e2e.py                       → tests/e2e/test_full_workflow.py
./test_partial_digest.py            → tests/integration/test_partial_digest.py
./test_rag_final.py                 → tests/integration/test_rag_final.py
./test_rag_search.py                → tests/integration/test_rag_search.py
./test_ragas_eval_simple.py         → tests/unit/rag/test_ragas_simple.py
./test_ragas_llm.py                 → tests/unit/rag/test_ragas_llm.py
./test_research_workflow.py         → tests/integration/test_research_workflow.py
./test_rpc_function.py              → tests/unit/mcp/test_rpc.py
./test_search_fix.py                → tests/integration/test_search_fix.py
./test_skip_flag.py                 → tests/unit/agent/test_skip_flag.py
./test_web_search.py                → tests/integration/test_web_search.py
```

**Action:** Move to appropriate test directory with proper naming

---

### Category 2: Historical Documentation (ARCHIVE → docs/archive/)

**Files to Archive:**
```
./APPROVAL_WORKFLOW_FIX.md          → docs/archive/fixes/
./DIGEST_GENERATION_FIX.md          → docs/archive/fixes/
./SEMANTIC_SEARCH_FIX.md            → docs/archive/fixes/
./STATE_PERSISTENCE_FIX.md          → docs/archive/fixes/
./DASHBOARD_CLEANUP.md              → docs/archive/maintenance/
./E2E_TEST_SUMMARY.md               → docs/archive/testing/
./IMPLEMENTATION_COMPLETE.md        → docs/archive/milestones/
./IMPLEMENTATION_SUMMARY.md         → docs/archive/milestones/
./PROGRESS.md                       → docs/archive/milestones/
./TEST_REPORT.md                    → docs/archive/testing/
./TEST_RESULTS.md                   → docs/archive/testing/
./VERIFICATION_COMPLETE.md          → docs/archive/milestones/
```

**Keep at Root:**
```
./README.md                         ✅ Primary documentation
./CONTRIBUTING.md                   ✅ Contributor guide
./QUICK_START.md                    ✅ User guide
./SETUP_GUIDE.md                    ✅ Installation guide
./AGENT_QUICK_START.md              ✅ Agent-specific guide
./DOCUMENTATION_UPDATE_SUMMARY.md   ✅ Recent updates
```

**Action:** Create `docs/archive/` structure and move historical docs

---

### Category 3: Utility Scripts (MOVE → scripts/)

**Files to Move:**
```
./quick_test_ingestion.py           → scripts/test_ingestion.py
./run_ingestion.py                  → scripts/run_ingestion.py
./run_migration.py                  → scripts/run_migration.py
./setup_and_test.py                 → scripts/setup_and_test.py
```

**Action:** Create `scripts/` directory if not exists, move utility scripts

---

### Category 4: Refactoring Artifacts (EVALUATE)

**New Structure (src/):**
```
src/
├── core/                           ⚠️  Created but NOT integrated
│   ├── config.py
│   ├── exceptions.py
│   └── types.py
├── agent/                          ⚠️  Created but NOT integrated
│   ├── models/
│   ├── controllers/
│   ├── tools/
│   └── utils/
└── rag/                            ❓ Not created yet (Phase 3)
```

**Decision Needed:**
1. **Option A (Complete Migration):** Finish migrating to `src/` structure
   - Update all imports in dashboard, MCP, tests
   - Make old `agent/` import from new `src/agent/`
   - Gradual deprecation with warnings

2. **Option B (Rollback):** Remove `src/` and keep current structure
   - Delete `src/` directory
   - Focus on improving existing structure
   - Postpone refactoring until necessary

3. **Option C (Hybrid):** Keep both temporarily
   - Leave `src/` as reference implementation
   - Use patterns from `src/` to improve `agent/`
   - Remove `src/` after incorporating improvements

**Recommendation:** Option C (Hybrid) - Learn from refactoring without breaking changes

**Action:** Keep `src/` but add README explaining it's reference code

---

### Category 5: Unused Code in Active Files (CODE REVIEW NEEDED)

**Files Requiring Manual Review:**
```
agent/tools.py (754 lines)          - Check for unused tools
agent/controller.py (736 lines)     - Check for deprecated code paths
learning-coach-mcp/src/rag/*.py     - Check for unused functions
dashboard/views/*.py                - Check for unused UI components
```

**Action:** Requires developer to review and mark with # TODO: REMOVE or # DEPRECATED

---

## Cleanup Execution Plan

### Phase 1: Safe Moves (No Breaking Changes) - 30 minutes

1. **Create Directory Structure**
   ```bash
   mkdir -p tests/{unit,integration,e2e}/{agent,rag,ingestion,mcp}
   mkdir -p docs/archive/{fixes,maintenance,testing,milestones}
   mkdir -p scripts
   ```

2. **Move Test Files**
   ```bash
   # Move each test file with git mv to preserve history
   git mv test_agent.py tests/unit/agent/test_agent_basic.py
   # ... (repeat for all test files)
   ```

3. **Move Historical Docs**
   ```bash
   git mv APPROVAL_WORKFLOW_FIX.md docs/archive/fixes/
   # ... (repeat for all historical docs)
   ```

4. **Move Utility Scripts**
   ```bash
   git mv quick_test_ingestion.py scripts/test_ingestion.py
   # ... (repeat for all scripts)
   ```

5. **Update Import Paths** (if any tests import each other)
   ```bash
   # Update imports in moved test files
   sed -i '' 's/from test_/from tests.unit./g' tests/unit/**/*.py
   ```

6. **Verify Tests Still Pass**
   ```bash
   pytest tests/ -v
   ```

### Phase 2: src/ Directory Decision - Developer Discussion

1. **Review Refactoring Progress**
   - Read: `.claude/tasks/codebase-refactoring-plan.md`
   - Read: `.claude/tasks/REFACTORING_ROADMAP.md`
   - Discuss: Complete migration vs. rollback vs. hybrid

2. **If Hybrid (Recommended):**
   ```bash
   # Add README to src/ explaining status
   echo "# Refactoring Reference Implementation

   This directory contains the Phase 1-2 refactoring work.
   Status: Reference implementation, not yet integrated.

   See: .claude/tasks/REFACTORING_ROADMAP.md for details.
   " > src/README.md
   ```

3. **If Rollback:**
   ```bash
   # Remove src/ directory
   git rm -rf src/
   ```

4. **If Complete Migration:**
   - Follow migration plan in `.claude/tasks/MIGRATION_GUIDE.md`
   - Update all imports
   - Add deprecation warnings to old structure
   - Timeline: 2-3 weeks

### Phase 3: Code Cleanup - Iterative (As Needed)

1. **Add Deprecation Markers**
   ```python
   # In files with unused code
   import warnings

   def deprecated_function():
       warnings.warn(
           "deprecated_function is deprecated, use new_function instead",
           DeprecationWarning,
           stacklevel=2
       )
       # ... existing code
   ```

2. **Track Technical Debt**
   ```bash
   # Create technical debt tracking file
   echo "# Technical Debt Tracking

   ## Deprecated Code
   - [ ] agent/tools.py: Remove unused tool X (line 123)
   - [ ] agent/controller.py: Remove legacy path Y (line 456)

   ## Code Smells
   - [ ] Large files (>500 lines): Consider splitting
   - [ ] Duplicated code: Consider extracting

   " > docs/TECHNICAL_DEBT.md
   ```

3. **Gradual Cleanup**
   - One file per week
   - Add tests before removing code
   - Document changes

---

## Expected Outcomes

### After Phase 1 (Safe Moves)

**Before:**
```
agentic-tutor/
├── test_*.py (20 files)            ❌ Scattered at root
├── *_FIX.md, *_SUMMARY.md (15)     ❌ Mixed with core docs
├── quick_*.py, run_*.py (4)        ❌ Scripts at root
└── ...
```

**After:**
```
agentic-tutor/
├── tests/                          ✅ Organized test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                           ✅ Clean documentation
│   ├── archive/                   ✅ Historical docs preserved
│   └── ... (active docs)
├── scripts/                        ✅ Utility scripts organized
│   └── ... (utility scripts)
└── ... (core files only at root)
```

**Benefits:**
- ✅ Clean root directory
- ✅ Organized test structure
- ✅ Preserved git history
- ✅ No breaking changes
- ✅ Easy to find files

### After Phase 2 (src/ Decision)

**If Hybrid:**
- `src/` kept as reference with README
- Learn patterns without disruption
- Option to migrate later

**If Rollback:**
- Clean removal of unused refactoring
- Focus on current structure

**If Complete Migration:**
- Modern, modular codebase
- Full refactoring benefits
- 2-3 week timeline

### After Phase 3 (Code Cleanup)

- Deprecated code marked
- Technical debt tracked
- Gradual improvement plan

---

## Risk Mitigation

### Risks

1. **Breaking Tests**
   - **Mitigation:** Use `git mv` to preserve history, update imports carefully
   - **Verification:** Run full test suite after each move

2. **Lost Documentation**
   - **Mitigation:** Archive, don't delete; use descriptive paths
   - **Verification:** Keep index in docs/archive/README.md

3. **Import Path Issues**
   - **Mitigation:** Test all moved files, update any relative imports
   - **Verification:** Check with `pytest tests/ -v`

4. **Git History Confusion**
   - **Mitigation:** Use `git mv` instead of manual move
   - **Verification:** `git log --follow <file>` works

### Rollback Plan

If anything breaks:
```bash
# Rollback to before cleanup
git reset --hard HEAD

# Or rollback specific file
git checkout HEAD -- <file>
```

---

## Success Metrics

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Root directory files | 60+ | <15 | 📋 |
| Test organization | Scattered | Organized | 📋 |
| Doc organization | Mixed | Categorized | 📋 |
| Import clarity | Mixed | Clear | 📋 |
| Git history | Preserved | Preserved | 📋 |

---

## Approval Checklist

Before proceeding:
- [ ] Review cleanup categories
- [ ] Decide on src/ strategy (Hybrid/Rollback/Complete)
- [ ] Approve test file moves
- [ ] Approve documentation archiving
- [ ] Approve script organization
- [ ] Allocate time for execution
- [ ] Review risk mitigation

---

## Next Steps

1. **User Decision:** Choose src/ strategy
2. **Execute Phase 1:** Safe moves (30 min)
3. **Verify:** Run tests, check functionality
4. **Execute Phase 2:** Handle src/ per decision
5. **Plan Phase 3:** Code cleanup (iterative)

---

**Ready for approval!** 🚀
