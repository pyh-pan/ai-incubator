# Remote Fixes V2 Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Selectively port the useful fixes from the remote v1.2 line into the current v2 incubator without restoring fixed user-visible framework flows.

**Architecture:** Keep `ai_service.py` as the lightweight provider/client boundary and keep `incubator_orchestrator.py` as the v2 intelligence coordinator. Add a small internal question strategy module that supplies concrete fallback questions, duplicate detection, and titles based on current thinking mode rather than exposed framework names.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, React/Vite/Vitest.

---

### Task 1: Preserve v2 Product Direction

**Files:**
- Create: `docs/superpowers/plans/2026-04-26-remote-fixes-v2-fusion.md`

- [x] **Step 1: Document the fusion rule**

Keep current v2 as source of truth. Do not restore `framework_service`, framework migrations, old React Flow pages, SettingsPage provider flows, or `CLAUDE.md`.

### Task 2: Add Internal Question Strategy

**Files:**
- Create: `backend/app/services/question_strategy.py`
- Test: `backend/tests/test_question_strategy.py`

- [x] **Step 1: Write tests for concrete, non-framework fallback questions**

Cover mode-based fallback, keyword anchoring, duplicate normalization, and rejection of generic followups such as "还有什么补充".

- [x] **Step 2: Implement the strategy**

Expose `build_fallback_turn(content, mode, context)` and `normalize_question(question)`. Use private mode templates (`clarify`, `challenge`, `validate`, `diverge`, `converge`) instead of visible framework names.

### Task 3: Harden V2 Orchestrator

**Files:**
- Modify: `backend/app/services/incubator_orchestrator.py`
- Test: `backend/tests/test_incubator_orchestrator.py`

- [x] **Step 1: Route AI-unavailable fallback through question strategy**

Replace the generic mock question with a concrete mode-aware fallback.

- [x] **Step 2: Guard invalid AI output**

If the configured AI returns invalid JSON, schema-invalid content, or duplicate/generic questions, return the same safe fallback instead of raising.

### Task 4: Verify Integration

**Commands:**
- `DATABASE_URL=sqlite:///./baseline_test.db .venv/bin/python -m pytest -q -o addopts=''`
- `npm run lint`
- `npm test -- --run`
- `npm run build`

- [x] **Step 1: Run backend tests**
- [x] **Step 2: Run frontend lint/tests/build**
- [x] **Step 3: Review diff and keep only v2-compatible changes**
