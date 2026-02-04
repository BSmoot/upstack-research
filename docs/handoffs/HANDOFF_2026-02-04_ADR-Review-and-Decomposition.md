# Handoff: ADR Review and Task Decomposition

**Date**: 2026-02-04
**From**: Architecture design session
**To**: Implementation planning session
**Status**: Ready for Guardian review → Task decomposition

---

## Session Objective

1. **Review ADR-002** with `apex-guardian` for final validation
2. **Decompose into tasks** with `apex-task-decomposer`

---

## Project Context

**Repository**: `C:\Users\bsmoo\projects\upstack-research`

This is an AI-powered market research system for UPSTACK (infrastructure technology advisory firm). It uses Claude agents with web search to produce structured research across multiple layers.

### Current Architecture
```
Layer 1 (Horizontal) → Layer 2 (Vertical/Industry) → Layer 3 (Title/Persona) → Playbooks → Brand Alignment
```

### Proposed Architecture (ADR-002)
```
Layer 0 (Service Category) → Layer 1 (Enhanced) → Layer 2 (Enhanced) → Layer 3 → 3D Playbooks → Validation → Brand Alignment
```

---

## Key Files to Read

### ADR (Primary Focus)
```
docs/adr/002-research-system-enhancement.md
```

### Supporting Context
```
research-manager/context/baseline.yaml          # Updated with key_suppliers (2026-02-04)
src/research_orchestrator/orchestrator.py       # Main coordination logic
src/research_orchestrator/state/tracker.py      # Checkpoint/resume
src/research_orchestrator/prompts/horizontal.py # Layer 1 prompts
src/research_orchestrator/prompts/vertical.py   # Layer 2 prompts
src/research_orchestrator/prompts/playbook.py   # Playbook generation
src/research_orchestrator/prompts/context_helpers.py  # Layer handoff functions
```

---

## ADR-002 Summary: 6 Major Changes

| # | Change | Description | Status |
|---|--------|-------------|--------|
| 1 | **Layer 0: Service Category Research** | New layer researching how buyers discover/evaluate Security, CX, Network, etc. | Design complete |
| 2 | **Enhanced Search Terms** | Buyer-centric terms, expanded information sources | Design complete |
| 3 | **Supplier Competition** | Research direct vendor sales as PRIMARY competition | Design complete |
| 4 | **Context Injection** | Auto-inject baseline.yaml, writing-standards.yaml into prompts | Design complete |
| 5 | **3D Playbooks** | Vertical × Title × Service Category | Design complete |
| 6 | **Validation Agent** | Quality gate before production | Design complete |

---

## Decisions Made in Prior Session

### 1. Dynamic Configuration (No Hardcoding)
- All suppliers loaded from `baseline.yaml` key_suppliers
- Research DISCOVERS buyer triggers, evaluation criteria, market pressures
- Config only provides factual seed data (supplier names)

### 2. Layer Handoffs Defined
```
Layer 0 → Layer 1: format_layer_0_context_for_layer_1()
Layer 1 → Layer 2: format_layer_1_context_for_vertical() [existing]
Layer 2 → Layer 3: format_layer_2_context_for_title() [existing]
All → Playbooks: Full context integration
```

### 3. Selective Update Capability
- Existing: `--layer`, `--agents`, `--resume`
- Needed: `--layer 0`, `--force`, `--verticals`, `--service-categories`

### 4. Output Structure
```
outputs/{execution_id}/
├── layer_0/          # NEW
├── layer_1/
├── layer_2/
├── layer_3/
├── playbooks/
├── validation/       # NEW
└── brand_alignment/
```

### 5. baseline.yaml Updated
- All 6 service categories now have `key_suppliers` (45 total suppliers)
- Added `market_notes` for procurement context
- Version 2.3, updated 2026-02-04

---

## Guardian Review Focus Areas

When running `apex-guardian`, validate:

1. **Contract Completeness**
   - Are all new interfaces fully specified?
   - Do Layer 0 contracts match existing layer patterns?

2. **Backward Compatibility**
   - Will existing checkpoints work with new layer_0?
   - Will existing configs work without service_categories?

3. **Integration Points**
   - Is context_injector integration with _get_agent_prompt() safe?
   - Are all new context helper functions specified?

4. **Gaps**
   - Any missing contracts the ADR doesn't address?
   - Any implementation details that need clarification?

---

## Task Decomposition Scope

After Guardian approval, decompose into phases:

### Phase 1: Foundation
- Context injection mechanism
- Enhanced search terms in prompts
- Supplier competition in competitive prompt

### Phase 2: Layer 0
- service_category.py prompts
- StateTracker layer_0 support
- Orchestrator execute_layer_0_parallel()
- CLI --layer 0 support

### Phase 3: Enhanced Prompts
- Market pressures in vertical prompts
- Information source requirements
- Layer 0 context formatting

### Phase 4: 3D Playbooks
- build_playbook_prompt_3d()
- priority_service_categories config
- Playbook generation for V × T × SC

### Phase 5: Validation
- validation.py prompts
- Validation agent execution
- Pass/fail criteria
- Review gate integration

### Phase 6: Selective Updates
- --force flag
- --verticals, --titles, --service-categories filters
- Output versioning

---

## Commands for This Session

### Step 1: Guardian Review
```
Use apex-guardian to review docs/adr/002-research-system-enhancement.md

Focus on:
- Contract completeness
- Integration safety
- Backward compatibility
- Missing specifications
```

### Step 2: Task Decomposition
```
Use apex-task-decomposer to decompose ADR-002 into executable tasks

Input: docs/adr/002-research-system-enhancement.md
Output: Task graph with dependencies, acceptance criteria
```

---

## Success Criteria

- [ ] Guardian confirms no blocking issues
- [ ] All gaps identified have resolution paths
- [ ] Task graph covers all 6 major changes
- [ ] Tasks have clear acceptance criteria
- [ ] Dependencies between tasks are explicit
- [ ] Estimated effort/cost per phase documented

---

## Notes from Prior Session

1. **Wiz acquisition**: Factor Google Cloud acquisition risk into CSPM evaluations
2. **VMware/VeloCloud excluded**: Post-Broadcom acquisition issues make it risky
3. **Cisco CCaaS**: Gartner 2025 Niche Player rating disputed - evaluate independently
4. **CentersquareDC**: Cyxtera + Evoque rebrand under Brookfield

---

## Prompt for New Session

Copy and paste this to start the new session:

```
I'm continuing work on the upstack-research system enhancement.

Repository: C:\Users\bsmoo\projects\upstack-research

Please:

1. First, read the handoff document:
   docs/handoffs/HANDOFF_2026-02-04_ADR-Review-and-Decomposition.md

2. Then read the ADR:
   docs/adr/002-research-system-enhancement.md

3. Run apex-guardian to validate the ADR against existing codebase contracts. Focus on:
   - Contract completeness for new components
   - Integration safety (especially context_injector)
   - Backward compatibility with existing checkpoints/configs
   - Any gaps that need resolution before implementation

4. After guardian approval, run apex-task-decomposer to break the ADR into executable implementation tasks with:
   - Clear task boundaries
   - Dependencies between tasks
   - Acceptance criteria for each task
   - Phased implementation approach

The goal is to have a complete task graph ready for implementation.
```
