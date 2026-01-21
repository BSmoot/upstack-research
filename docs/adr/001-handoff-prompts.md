# Handoff Prompts: ADR-001 Implementation

Use these prompts in separate Claude Code sessions to implement the remediation tasks using apex agents.

**Prerequisites**: Each session assumes the ADR documents exist:
- `docs/adr/001-codebase-remediation.md`
- `docs/adr/001-guardian-analysis.md`
- `docs/adr/001-task-graph.md`

---

## Session 1: Phase 1 - Critical Security and Reliability

**Estimated scope**: ~80 LOC, 2 tasks

```
Implement Phase 1 of ADR-001 (Critical Security and Reliability) using apex agents.

## Context
Read these documents first:
- docs/adr/001-codebase-remediation.md (the ADR)
- docs/adr/001-guardian-analysis.md (contract constraints)
- docs/adr/001-task-graph.md (task specifications for P1-T1, P1-T2)

## Tasks to Implement

### P1-T1: Fix Bare Exception in StateTracker
- File: src/research_orchestrator/state/tracker.py:107-110
- Replace bare `except: pass` with `except OSError as cleanup_error:`
- Add warning log for cleanup failures
- MUST NOT swallow KeyboardInterrupt or SystemExit

### P1-T2: Add Path Traversal Validation
- File: src/research_orchestrator/prompts/context_helpers.py:119-127
- Add `_validate_output_path()` function
- Validate paths before file reads
- Log WARNING for blocked traversal attempts
- Return "Summary not available" on validation failure (don't raise)

## Workflow
1. Launch apex-developer agents in parallel for P1-T1 and P1-T2
2. Collect both designs
3. Use apex-integrator to validate and write all changes
4. Run verification commands from task graph

## Verification Required
```bash
# P1-T1: No bare except remaining
grep -n "except:" src/research_orchestrator/state/tracker.py

# P1-T2: Path traversal blocked
python -c "
from research_orchestrator.prompts.context_helpers import extract_summary
result = extract_summary({'output_path': '../../etc/passwd'})
assert result == 'Summary not available', f'Got: {result}'
print('Path traversal blocked successfully')
"

# Run tests
pytest src/tests/ -v -x
```

## Acceptance Criteria
- [ ] No bare `except:` in tracker.py
- [ ] KeyboardInterrupt propagates during checkpoint save
- [ ] Path traversal attempts rejected and logged
- [ ] All existing tests pass
```

---

## Session 2: Phase 2 - Configuration and Cost Accuracy

**Estimated scope**: ~230 LOC, 4 tasks

```
Implement Phase 2 of ADR-001 (Configuration and Cost Accuracy) using apex agents.

## Context
Read these documents first:
- docs/adr/001-codebase-remediation.md (the ADR)
- docs/adr/001-guardian-analysis.md (contract constraints)
- docs/adr/001-task-graph.md (task specifications for P2-T1 through P2-T4)

## Tasks to Implement (in order)

### P2-T1: Create Model Constants Module (FIRST)
- Create: src/research_orchestrator/utils/constants.py
- Define Models class with SONNET_4, HAIKU_4, OPUS_4, DEFAULT, HIGH_QUALITY
- Add get_pricing() class method for model-specific costs

### P2-T2: Replace Hardcoded Model Names (after P2-T1)
- Update: research_session.py:27, config_models.py:147, config.py:65
- Import and use Models.* constants
- No hardcoded model strings should remain (except in constants.py)

### P2-T3: Implement Accurate Cost Estimation (after P2-T2)
- Update: src/research_orchestrator/research_session.py
- Track input_tokens and output_tokens separately (from response.usage)
- Use Models.get_pricing() for model-specific costs
- Replace _estimate_cost() with _calculate_cost(input_tokens, output_tokens)

### P2-T4: Add Pydantic Config Validation (after P2-T2, parallel with P2-T3)
- Create: src/research_orchestrator/utils/config_schema.py
- Define ResearchConfig Pydantic model matching current defaults
- Update config_models.py to validate on load
- Use .model_dump() for backward compatibility

## Workflow
1. P2-T1 and P2-T2 must be sequential (dependency)
2. Launch apex-developer for P2-T1
3. Integrate P2-T1, then launch apex-developer for P2-T2
4. Integrate P2-T2, then launch apex-developers for P2-T3 and P2-T4 in parallel
5. Use apex-integrator to write P2-T3 and P2-T4 together

## Verification Required
```bash
# No hardcoded model strings
grep -rn "claude-sonnet-4-20250514\|claude-haiku-4-20250514" src/research_orchestrator/ --include="*.py" | grep -v constants.py | grep -v __pycache__

# Constants module works
python -c "from research_orchestrator.utils.constants import Models; print(Models.SONNET_4)"

# Config validation rejects invalid
python -c "
from research_orchestrator.utils.config_schema import ResearchConfig
try:
    ResearchConfig(execution={'id': 'test'}, verticals=[], title_clusters=['a'])
    print('FAIL: Should have rejected empty verticals')
except Exception as e:
    print(f'OK: Rejected invalid config')
"

# Run tests
pytest src/tests/ -v -x
```

## Acceptance Criteria
- [ ] Models class created with all constants
- [ ] No hardcoded model names outside constants.py
- [ ] Cost calculated from actual input/output tokens
- [ ] Invalid configs fail fast with Pydantic errors
- [ ] All tests pass
```

---

## Session 3: Phase 3 - Code Quality and Maintainability

**Estimated scope**: ~240 LOC, 4 tasks

```
Implement Phase 3 of ADR-001 (Code Quality and Maintainability) using apex agents.

## Context
Read these documents first:
- docs/adr/001-codebase-remediation.md (the ADR)
- docs/adr/001-guardian-analysis.md (contract constraints)
- docs/adr/001-task-graph.md (task specifications for P3-T1 through P3-T4)

## Tasks to Implement (all parallelizable)

### P3-T1: Extract Budget Check Methods
- File: src/research_orchestrator/orchestrator.py
- Create _update_budget(searches, cost) method
- Create _check_budget_limits() method that raises BudgetExceededError
- Replace duplicated code at lines 406-416, 507-517, 608-618, 726-736
- Preserve exact budget dict keys and error message format

### P3-T2: Implement Resume Functionality
- File: src/run_research.py:131-136
- Accept --resume <execution_id> with required --config
- Pass resume_execution_id to orchestrator config
- Print helpful error if --resume used without --config

### P3-T3: Externalize VERTICALS to YAML
- Create: build/config/verticals.yaml
- Update: src/research_orchestrator/prompts/vertical.py
- Load from YAML with fallback to hardcoded dict
- Match VerticalConfig TypedDict schema exactly

### P3-T4: Externalize TITLE_CLUSTERS to YAML
- Create: build/config/title_clusters.yaml
- Update: src/research_orchestrator/prompts/title.py
- Load from YAML with fallback to hardcoded dict
- Match TitleClusterConfig TypedDict schema exactly

## Workflow
1. Launch apex-developer agents for all 4 tasks in parallel
2. Collect all 4 designs
3. Use apex-integrator to validate and write all changes together

## Verification Required
```bash
# P3-T1: Single budget check method
grep -n "_check_budget_limits" src/research_orchestrator/orchestrator.py | wc -l
# Should be 5 (1 definition + 4 calls)

# P3-T2: Resume requires config
python src/run_research.py --resume test-123 2>&1 | grep -q "config is required" && echo "OK" || echo "FAIL"

# P3-T3: Verticals load from YAML
python -c "
from research_orchestrator.prompts.vertical import VERTICALS
print(f'Loaded {len(VERTICALS)} verticals')
assert 'healthcare' in VERTICALS
"

# P3-T4: Title clusters load from YAML
python -c "
from research_orchestrator.prompts.title import TITLE_CLUSTERS
print(f'Loaded {len(TITLE_CLUSTERS)} title clusters')
assert 'cfo_cluster' in TITLE_CLUSTERS
"

# Run tests
pytest src/tests/ -v -x
```

## Acceptance Criteria
- [ ] Budget logic deduplicated to 2 methods
- [ ] --resume with --config works correctly
- [ ] Verticals loadable from YAML (with fallback)
- [ ] Title clusters loadable from YAML (with fallback)
- [ ] All tests pass
```

---

## Session 4: Phase 4 - Operational Excellence

**Estimated scope**: ~270 LOC, 3 tasks

```
Implement Phase 4 of ADR-001 (Operational Excellence) using apex agents.

## Context
Read these documents first:
- docs/adr/001-codebase-remediation.md (the ADR)
- docs/adr/001-guardian-analysis.md (contract constraints)
- docs/adr/001-task-graph.md (task specifications for P4-T1 through P4-T3)

## Tasks to Implement (all parallelizable)

### P4-T1: Add .gitignore Patterns
- Create/update: .gitignore
- Add patterns for: .env*, credentials, checkpoints/, outputs/, logs/
- Add standard Python patterns: __pycache__, *.pyc, .pytest_cache/

### P4-T2: Create Circuit Breaker Module
- Create: src/research_orchestrator/utils/circuit_breaker.py
- Implement CircuitBreaker class with CLOSED/OPEN/HALF_OPEN states
- Thresholds: 5 failures to open, 60s recovery timeout
- Use logger 'research_orchestrator' with format "[CircuitBreaker] {service}: {msg}"
- Integrate with ResearchSession._api_call_with_retry()

### P4-T3: Add Test Coverage
- Create: src/tests/test_layer_1.py (Layer 1 execution)
- Create: src/tests/test_config_inheritance.py (config extends keyword)
- Create: src/tests/test_budget_errors.py (BudgetExceededError scenarios)
- Follow existing @pytest.fixture patterns from test_orchestrator_layers.py
- Use @pytest.mark.asyncio for async tests

## Workflow
1. Launch apex-developer agents for all 3 tasks in parallel
2. Collect all designs
3. Use apex-integrator to validate and write all changes together

## Verification Required
```bash
# P4-T1: .gitignore works
touch .env.test
git status --porcelain | grep -q ".env.test" && echo "FAIL" || echo "OK: .env.test ignored"
rm -f .env.test

# P4-T2: Circuit breaker functions
python -c "
from research_orchestrator.utils.circuit_breaker import CircuitBreaker, CircuitState

cb = CircuitBreaker('test', failure_threshold=3)
assert cb.state == CircuitState.CLOSED

for _ in range(3):
    cb.record_failure()

assert cb.state == CircuitState.OPEN
print('Circuit breaker works correctly')
"

# P4-T3: New tests pass
pytest src/tests/test_layer_1.py src/tests/test_config_inheritance.py src/tests/test_budget_errors.py -v

# All tests pass
pytest src/tests/ -v
```

## Acceptance Criteria
- [ ] .gitignore prevents committing sensitive files
- [ ] Circuit breaker trips after 5 failures, recovers after 60s
- [ ] Circuit breaker integrated with API retry logic
- [ ] New tests cover Layer 1, config inheritance, budget errors
- [ ] All tests pass

## Final Verification (after all phases)
Run completion gate checks from CLAUDE.md:
```bash
git diff --name-only HEAD
git diff --name-only HEAD | xargs grep -l "Math.random()" 2>/dev/null
git diff --name-only HEAD | xargs grep -l "as any" 2>/dev/null
git diff --name-only HEAD | xargs grep -l "eval(" 2>/dev/null
git diff --name-only HEAD | xargs grep -l "except:" 2>/dev/null
pytest src/tests/ -v
```
```

---

## Quick Reference

| Session | Phase | Tasks | Est. LOC | Key Files |
|---------|-------|-------|----------|-----------|
| 1 | Critical Security | P1-T1, P1-T2 | ~80 | tracker.py, context_helpers.py |
| 2 | Configuration | P2-T1 → P2-T4 | ~230 | constants.py (new), config_schema.py (new), research_session.py |
| 3 | Code Quality | P3-T1 → P3-T4 | ~240 | orchestrator.py, run_research.py, verticals.yaml (new) |
| 4 | Operations | P4-T1 → P4-T3 | ~270 | circuit_breaker.py (new), .gitignore, test files (new) |

## Notes

- Each session is independent after Phase 1 completes
- Commit after each session with descriptive message
- Run `pytest src/tests/ -v` before ending each session
- If any verification fails, fix before moving to next session
