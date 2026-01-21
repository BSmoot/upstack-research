# ADR-001: Research Orchestrator Codebase Remediation

**Title**: Systematic Remediation of Technical Debt and Security Issues

**Status**: Proposed

**Date**: 2026-01-15

---

## Context

A codebase assessment of the Research Orchestrator identified 11 issues across security, reliability, maintainability, and operational concerns. The codebase is a Python-based multi-layer research orchestration system that coordinates Claude API calls for market research generation.

**Current State**:
- Production-ready core architecture with async execution, checkpointing, and budget tracking
- Well-structured layer dependency management (Layer 1 -> 2 -> 3 -> Playbooks)
- Several latent issues that could cause problems at scale or in edge cases

**Business Drivers**:
- Prevent silent failures during long-running research sessions
- Ensure security compliance for file operations
- Reduce maintenance burden from duplicated code
- Enable accurate cost forecasting for budget-conscious deployments

---

## Decision

Remediate all 11 identified issues in **four logical phases**, grouping related fixes to minimize churn and maximize cohesion. Each phase is independently deployable and testable.

### Phase 1: Critical Security and Reliability (High Priority)
**Estimated Effort**: Small

| Issue | Location | Fix |
|-------|----------|-----|
| Bare `except: pass` | `state/tracker.py:108-110` | Catch `OSError` specifically, log warning |
| Missing path validation | `context_helpers.py:121-125` | Add `_validate_output_path()` with traversal check |

### Phase 2: Configuration and Cost Accuracy (Medium Priority)
**Estimated Effort**: Medium

| Issue | Location | Fix |
|-------|----------|-----|
| Hardcoded model names | `research_session.py:27`, `config_models.py:147`, `config.py:65` | Create `utils/constants.py` with `Models` class |
| Inaccurate cost estimation | `research_session.py:331-347` | Track input/output tokens separately, model-specific pricing |
| No config schema validation | `config_models.py:38-39` | Add Pydantic models in `config_schema.py` |

### Phase 3: Code Quality and Maintainability (Medium Priority)
**Estimated Effort**: Medium

| Issue | Location | Fix |
|-------|----------|-----|
| Duplicate budget check logic | `orchestrator.py` (4 places) | Extract `_update_budget()` and `_check_budget_limits()` |
| Incomplete resume functionality | `run_research.py:131-136` | Implement checkpoint lookup, require `--config` for now |
| Hardcoded verticals/titles | `vertical.py:15-46`, `title.py:18-49` | Externalize to `build/config/*.yaml` with fallback |

### Phase 4: Operational Excellence (Low Priority)
**Estimated Effort**: Medium

| Issue | Location | Fix |
|-------|----------|-----|
| Missing .gitignore patterns | `.gitignore` | Add credential and local config patterns |
| No circuit breaker | N/A (new) | Create `utils/circuit_breaker.py` |
| Test coverage gaps | `tests/` | Add `test_layer_1.py`, `test_config_inheritance.py`, `test_budget_errors.py` |

---

## Rationale

**Why this grouping?**

1. **Phase 1** addresses issues that could cause data loss (`KeyboardInterrupt` swallowed) or security vulnerabilities (path traversal). These must be fixed first.

2. **Phase 2** improves operational accuracy. Incorrect cost estimates lead to budget overruns; invalid configs cause confusing runtime errors.

3. **Phase 3** reduces technical debt. Duplicated code increases bug surface area; incomplete features confuse users.

4. **Phase 4** hardens production operations. Circuit breakers prevent cascade failures; tests catch regressions.

**Why ONE approach instead of options?**

- All issues are well-understood with clear solutions
- No significant trade-offs between alternatives
- Phased delivery allows early value realization

---

## Consequences

### Positive
- Silent failure during shutdown prevented
- Path traversal attacks blocked
- Single source of truth for model names
- Cost estimates within 5% of actual billing
- 75% reduction in duplicated budget check code
- Users can resume interrupted research
- New verticals addable without code changes
- Cascade failures prevented by circuit breaker

### Negative
- Pydantic dependency adds ~500KB
- Existing configs may need minor updates for strict validation

### Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing configs | Validate production configs before merge |
| Circuit breaker false positives | Conservative thresholds (5 failures, 60s timeout) |
| Path validation too restrictive | Configurable base directory |

---

## Implementation Notes

### Key File Changes

**Phase 1**:
- `src/research_orchestrator/state/tracker.py` - Fix bare except
- `src/research_orchestrator/prompts/context_helpers.py` - Add path validation

**Phase 2**:
- `src/research_orchestrator/utils/constants.py` (new) - Model constants
- `src/research_orchestrator/utils/config_schema.py` (new) - Pydantic models
- `src/research_orchestrator/research_session.py` - Accurate cost tracking

**Phase 3**:
- `src/research_orchestrator/orchestrator.py` - Extract budget methods
- `src/run_research.py` - Implement resume
- `build/config/verticals.yaml` (new) - Externalized data
- `build/config/title_clusters.yaml` (new) - Externalized data

**Phase 4**:
- `.gitignore` - Additional patterns
- `src/research_orchestrator/utils/circuit_breaker.py` (new)
- `src/tests/test_layer_1.py` (new)
- `src/tests/test_config_inheritance.py` (new)
- `src/tests/test_budget_errors.py` (new)

### Backward Compatibility

- All existing configs continue to work (Pydantic uses defaults)
- YAML verticals fall back to hardcoded if file missing
- Resume requires `--config` flag (config path stored in checkpoint in future)

### Dependencies to Add
```
pydantic>=2.0
```

---

## Acceptance Criteria

### Phase 1
- [ ] `KeyboardInterrupt` during checkpoint save propagates correctly
- [ ] Path traversal attempts (e.g., `../../etc/passwd`) are rejected and logged
- [ ] Unit tests verify both fixes

### Phase 2
- [ ] All model name literals replaced with `Models.*` constants
- [ ] Cost estimates track input/output tokens separately
- [ ] Invalid configs fail fast with clear Pydantic validation errors

### Phase 3
- [ ] Single `_update_budget()` method used in all 4 agent execution methods
- [ ] `--resume <id> --config <path>` works correctly
- [ ] New verticals addable via YAML without code changes

### Phase 4
- [ ] No credential files can be accidentally committed
- [ ] Circuit breaker trips after 5 consecutive API failures
- [ ] Test coverage includes Layer 1, config inheritance, and budget errors

---

## Alternatives Considered

1. **Minimal fixes only (Phase 1)**: Rejected - medium-priority issues cause real operational pain

2. **Full architectural rewrite**: Rejected - current architecture is sound; issues are localized

3. **External configuration service**: Rejected - adds operational complexity unnecessary at current scale

---

## Confidence

**Level**: High

All issues verified with file:line references. Solutions follow established Python patterns (Pydantic for validation, circuit breaker for resilience). No novel approaches required.
