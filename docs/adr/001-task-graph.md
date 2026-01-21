# Task Graph: ADR-001 Codebase Remediation

**Source ADR**: `docs/adr/001-codebase-remediation.md`
**Guardian Analysis**: `docs/adr/001-guardian-analysis.md`
**Generated**: 2026-01-15

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 13 |
| Total LOC (estimated) | ~650 |
| New Files | 7 |
| Modified Files | 8 |
| Tier | 2 (Standard) |

### Phase Overview

| Phase | Tasks | Priority | Parallelization |
|-------|-------|----------|-----------------|
| Phase 1: Critical Security | 2 | HIGH | Fully parallel |
| Phase 2: Configuration | 4 | MEDIUM | P2-T3/T4 parallel after P2-T2 |
| Phase 3: Code Quality | 4 | MEDIUM | Fully parallel |
| Phase 4: Operations | 3 | LOW | Fully parallel |

---

## Dependency Graph

```
Phase 1 (parallel):
  P1-T1 ─┐
         ├─> Phase 2
  P1-T2 ─┘

Phase 2 (sequential then parallel):
  P2-T1 -> P2-T2 ─┬─> P2-T3 ─┐
                  │          ├─> Phase 3
                  └─> P2-T4 ─┘

Phase 3 (parallel):
  P3-T1 ─┐
  P3-T2 ─┼─> Phase 4
  P3-T3 ─┤
  P3-T4 ─┘

Phase 4 (parallel):
  P4-T1 ─┐
  P4-T2 ─┼─> DONE
  P4-T3 ─┘
```

---

## Phase 1: Critical Security and Reliability

### P1-T1: Fix Bare Exception in StateTracker

**Priority**: HIGH
**Estimated LOC**: ~30
**Dependencies**: None

**Description**: Replace bare `except: pass` with specific `except OSError` to prevent swallowing `KeyboardInterrupt` and `SystemExit`.

**Input Files**:
- `src/research_orchestrator/state/tracker.py`

**Output Files**:
- `src/research_orchestrator/state/tracker.py` (modified)

**Contract Constraints** (from Guardian):
- MUST NOT swallow `KeyboardInterrupt`
- MUST NOT swallow `SystemExit`
- MUST log any caught exception before cleanup
- MUST preserve atomic write behavior (temp file + rename)

**Implementation**:
```python
# Location: tracker.py:107-110
# BEFORE:
try:
    os.unlink(tmp_path)
except:
    pass

# AFTER:
try:
    os.unlink(tmp_path)
except OSError as cleanup_error:
    self.logger.warning(f"Failed to cleanup temp file {tmp_path}: {cleanup_error}")
```

**Verification**:
```bash
# Check no bare except remains
grep -n "except:" src/research_orchestrator/state/tracker.py
# Should return 0 lines

# Run existing tests
pytest src/tests/test_orchestrator_layers.py -v
```

**Acceptance Criteria**:
- [ ] No bare `except:` statements in tracker.py
- [ ] `KeyboardInterrupt` during checkpoint save propagates correctly
- [ ] Cleanup failures are logged at WARNING level

---

### P1-T2: Add Path Traversal Validation

**Priority**: HIGH
**Estimated LOC**: ~50
**Dependencies**: None

**Description**: Add `_validate_output_path()` function to prevent path traversal attacks when reading output files.

**Input Files**:
- `src/research_orchestrator/prompts/context_helpers.py`

**Output Files**:
- `src/research_orchestrator/prompts/context_helpers.py` (modified)

**Contract Constraints** (from Guardian):
- MUST NOT read files outside output directory
- MUST validate path before reading
- MUST return `"Summary not available"` on failure (not raise)
- MUST preserve max_length truncation behavior
- Signature: `def extract_summary(agent_output: Dict[str, Any], max_length: int = 500) -> str`

**Implementation**:
```python
# Add new function before extract_summary()
def _validate_output_path(path: Path, base_dir: Optional[Path] = None) -> bool:
    """Validate that path is within allowed directory (prevents traversal)."""
    if base_dir is None:
        base_dir = Path.cwd() / "outputs"
    try:
        resolved = path.resolve()
        base_resolved = base_dir.resolve()
        return resolved.is_relative_to(base_resolved)
    except (ValueError, RuntimeError):
        return False

# Update extract_summary() to use validation
if 'output_path' in agent_output:
    try:
        output_path = Path(agent_output['output_path'])
        if not _validate_output_path(output_path):
            logger.warning(f"Path traversal attempt blocked: {output_path}")
            return "Summary not available"
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
    except Exception:
        pass
```

**Verification**:
```bash
# Run tests
pytest src/tests/test_context_helpers.py -v

# Manual verification (should fail gracefully)
python -c "
from research_orchestrator.prompts.context_helpers import extract_summary
result = extract_summary({'output_path': '../../etc/passwd'})
assert result == 'Summary not available', f'Got: {result}'
print('Path traversal blocked successfully')
"
```

**Acceptance Criteria**:
- [ ] Path traversal attempts (e.g., `../../etc/passwd`) are rejected
- [ ] Rejected paths are logged at WARNING level
- [ ] Normal output paths still work correctly
- [ ] Function still returns "Summary not available" on any failure

---

## Phase 2: Configuration and Cost Accuracy

### P2-T1: Create Model Constants Module

**Priority**: MEDIUM
**Estimated LOC**: ~40
**Dependencies**: P1-T1, P1-T2

**Description**: Create centralized constants for model names to prevent scattered hardcoding.

**Input Files**: None (new file)

**Output Files**:
- `src/research_orchestrator/utils/constants.py` (new)

**Contract Constraints** (from Guardian):
- Must include: SONNET_4, HAIKU_4, OPUS_4, DEFAULT, HIGH_QUALITY
- Values must match current hardcoded strings exactly

**Implementation**:
```python
# src/research_orchestrator/utils/constants.py
"""Centralized constants for the research orchestrator."""

class Models:
    """Claude model identifiers."""
    SONNET_4 = "claude-sonnet-4-20250514"
    HAIKU_4 = "claude-haiku-4-20250514"
    OPUS_4 = "claude-opus-4-20250514"

    # Semantic aliases
    DEFAULT = HAIKU_4
    HIGH_QUALITY = SONNET_4
    FAST = HAIKU_4

    @classmethod
    def get_pricing(cls, model: str) -> tuple[float, float]:
        """Return (input_price_per_M, output_price_per_M) for model."""
        pricing = {
            cls.HAIKU_4: (0.25, 1.25),
            cls.SONNET_4: (3.0, 15.0),
            cls.OPUS_4: (15.0, 75.0),
        }
        return pricing.get(model, (3.0, 15.0))  # Default to Sonnet pricing
```

**Verification**:
```bash
# Verify module imports correctly
python -c "from research_orchestrator.utils.constants import Models; print(Models.SONNET_4)"
```

**Acceptance Criteria**:
- [ ] Module created at correct path
- [ ] All model constants defined
- [ ] Pricing method returns correct values

---

### P2-T2: Replace Hardcoded Model Names

**Priority**: MEDIUM
**Estimated LOC**: ~30
**Dependencies**: P2-T1

**Description**: Update all hardcoded model name strings to use `Models.*` constants.

**Input Files**:
- `src/research_orchestrator/research_session.py`
- `src/research_orchestrator/utils/config_models.py`
- `src/research_orchestrator/utils/config.py`

**Output Files**:
- Same files (modified)

**Contract Constraints** (from Guardian):
- `research_session.py:27` - default parameter
- `config_models.py:147` - fallback value
- `config.py:65` - default dict value

**Implementation**:
```python
# research_session.py - add import, update default
from research_orchestrator.utils.constants import Models
# Line 27: model: str = "claude-sonnet-4-20250514"
# becomes: model: str = Models.HIGH_QUALITY

# config_models.py - add import, update fallback
from research_orchestrator.utils.constants import Models
# Line 147: return 'claude-haiku-4-20250514'
# becomes: return Models.DEFAULT

# config.py - add import, update default
from research_orchestrator.utils.constants import Models
# Line 65: 'model': 'claude-sonnet-4-20250514'
# becomes: 'model': Models.HIGH_QUALITY
```

**Verification**:
```bash
# No hardcoded model strings should remain
grep -rn "claude-sonnet-4-20250514\|claude-haiku-4-20250514" src/research_orchestrator/ --include="*.py" | grep -v constants.py | grep -v __pycache__
# Should return 0 lines

# Run tests
pytest src/tests/ -v -k "not integration"
```

**Acceptance Criteria**:
- [ ] All model string literals replaced with constants
- [ ] No remaining hardcoded model names (except in constants.py)
- [ ] All existing tests pass

---

### P2-T3: Implement Accurate Cost Estimation

**Priority**: MEDIUM
**Estimated LOC**: ~60
**Dependencies**: P2-T2

**Description**: Replace 40/60 token split assumption with actual input/output tracking and model-specific pricing.

**Input Files**:
- `src/research_orchestrator/research_session.py`

**Output Files**:
- `src/research_orchestrator/research_session.py` (modified)

**Contract Constraints** (from Guardian):
- Result schema MUST preserve `estimated_cost_usd: float`
- MUST use actual `response.usage.input_tokens` and `response.usage.output_tokens`
- MUST support model-specific pricing

**Implementation**:
```python
# Update _estimate_cost to accept actual tokens
def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
    """Calculate actual cost based on token counts and model pricing."""
    from research_orchestrator.utils.constants import Models
    input_price, output_price = Models.get_pricing(self.model)
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    return input_cost + output_cost

# Track tokens separately in instance
self.total_input_tokens = 0
self.total_output_tokens = 0

# Update in _api_call_with_retry after response
self.total_input_tokens += response.usage.input_tokens
self.total_output_tokens += response.usage.output_tokens

# Update result building
'estimated_cost_usd': self._calculate_cost(self.total_input_tokens, self.total_output_tokens)
```

**Verification**:
```bash
# Run unit tests
pytest src/tests/test_research_session.py -v

# Verify cost calculation
python -c "
from research_orchestrator.utils.constants import Models
input_p, output_p = Models.get_pricing(Models.SONNET_4)
cost = (1000 / 1_000_000) * input_p + (2000 / 1_000_000) * output_p
print(f'Cost for 1K input + 2K output on Sonnet: \${cost:.6f}')
assert abs(cost - 0.033) < 0.001
"
```

**Acceptance Criteria**:
- [ ] Cost calculated from actual input/output tokens
- [ ] Model-specific pricing used
- [ ] Result dict still contains `estimated_cost_usd` as float

---

### P2-T4: Add Pydantic Config Schema Validation

**Priority**: MEDIUM
**Estimated LOC**: ~100
**Dependencies**: P2-T2

**Description**: Add Pydantic models for config validation with clear error messages.

**Input Files**:
- `src/research_orchestrator/utils/config_models.py`

**Output Files**:
- `src/research_orchestrator/utils/config_schema.py` (new)
- `src/research_orchestrator/utils/config_models.py` (modified)

**Contract Constraints** (from Guardian):
- Use `.model_dump()` for backward compatibility
- Match current `_validate_config()` defaults
- Config must include: execution.id, verticals, title_clusters

**Implementation**:
```python
# config_schema.py (new)
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from research_orchestrator.utils.constants import Models

class ApiConfig(BaseModel):
    model: str = Models.HIGH_QUALITY
    max_tokens: int = 16000

class BudgetConfig(BaseModel):
    max_searches: int = 500
    max_cost_usd: float = 200.0

class ExecutionSettings(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)

class ExecutionConfig(BaseModel):
    id: str

class ResearchConfig(BaseModel):
    execution: ExecutionConfig
    verticals: List[str] = Field(min_length=1)
    title_clusters: List[str] = Field(min_length=1)
    execution_settings: ExecutionSettings = Field(default_factory=ExecutionSettings)

    @field_validator('verticals', 'title_clusters')
    @classmethod
    def validate_non_empty(cls, v):
        if not v:
            raise ValueError("List cannot be empty")
        return v

# config_models.py - update load_project_config
def load_project_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)

    # Validate with Pydantic
    from research_orchestrator.utils.config_schema import ResearchConfig
    validated = ResearchConfig(**raw_config)
    return validated.model_dump()
```

**Verification**:
```bash
# Test validation rejects invalid config
python -c "
from research_orchestrator.utils.config_schema import ResearchConfig
try:
    ResearchConfig(execution={'id': 'test'}, verticals=[], title_clusters=['a'])
    print('FAIL: Should have rejected empty verticals')
except Exception as e:
    print(f'OK: Rejected invalid config: {e}')
"

# Run tests
pytest src/tests/ -v
```

**Acceptance Criteria**:
- [ ] Invalid configs fail fast with clear Pydantic errors
- [ ] Valid configs load without changes
- [ ] Defaults match existing behavior

---

## Phase 3: Code Quality and Maintainability

### P3-T1: Extract Budget Check Methods

**Priority**: MEDIUM
**Estimated LOC**: ~80
**Dependencies**: P2-T3, P2-T4

**Description**: Extract duplicated budget check logic into reusable methods.

**Input Files**:
- `src/research_orchestrator/orchestrator.py`

**Output Files**:
- `src/research_orchestrator/orchestrator.py` (modified)

**Contract Constraints** (from Guardian):
- Preserve budget dict keys: `max_total_searches`, `max_total_cost_usd`, `current_searches`, `current_cost_usd`
- Raise `BudgetExceededError` with same message format
- Update all 4 locations: lines 406-416, 507-517, 608-618, 726-736

**Implementation**:
```python
# Add new methods to ResearchOrchestrator class
def _update_budget(self, searches: int, cost: float) -> None:
    """Update budget tracking with new usage."""
    self.budget['current_searches'] += searches
    self.budget['current_cost_usd'] += cost

def _check_budget_limits(self) -> None:
    """Check if budget limits exceeded, raise if so."""
    if self.budget['current_searches'] >= self.budget['max_total_searches']:
        raise BudgetExceededError(
            f"Search limit reached: {self.budget['current_searches']}/{self.budget['max_total_searches']}"
        )
    if self.budget['current_cost_usd'] >= self.budget['max_total_cost_usd']:
        raise BudgetExceededError(
            f"Cost limit reached: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}"
        )

# Replace duplicated code in all 4 methods with:
self._update_budget(result['searches_performed'], result['estimated_cost_usd'])
self._check_budget_limits()
```

**Verification**:
```bash
# Count budget check occurrences (should be 4 calls to _check_budget_limits)
grep -n "_check_budget_limits" src/research_orchestrator/orchestrator.py | wc -l
# Should be 4+1 (4 calls + 1 definition)

# No duplicated budget logic
grep -n "current_searches.*>=" src/research_orchestrator/orchestrator.py | wc -l
# Should be 1 (only in _check_budget_limits)

# Run tests
pytest src/tests/test_orchestrator_layers.py -v
```

**Acceptance Criteria**:
- [ ] Single `_update_budget()` method handles all budget updates
- [ ] Single `_check_budget_limits()` method handles all limit checks
- [ ] All 4 agent execution methods use extracted methods
- [ ] Tests pass

---

### P3-T2: Implement Resume Functionality

**Priority**: MEDIUM
**Estimated LOC**: ~40
**Dependencies**: P2-T3, P2-T4

**Description**: Implement `--resume <execution_id> --config <path>` to resume interrupted research.

**Input Files**:
- `src/run_research.py`

**Output Files**:
- `src/run_research.py` (modified)

**Contract Constraints** (from Guardian):
- Currently exits with message at lines 131-136
- Must accept `--resume <execution_id>` with required `--config`
- Pass execution_id to orchestrator

**Implementation**:
```python
# Update argument handling in main()
if args.resume:
    if not args.config:
        print("Error: --config is required when using --resume")
        sys.exit(1)
    print(f"Resuming execution: {args.resume}")
    # Load config and pass resume ID to orchestrator
    config = load_config(args.config)
    config['resume_execution_id'] = args.resume
    orchestrator = ResearchOrchestrator(config)
    # StateTracker will detect existing checkpoint and resume
    await orchestrator.run()
```

**Verification**:
```bash
# Test resume requires config
python src/run_research.py --resume test-123 2>&1 | grep -q "config is required"

# Test with valid args (dry run)
python src/run_research.py --resume test-123 --config configs/example.yaml --dry-run
```

**Acceptance Criteria**:
- [ ] `--resume` without `--config` prints helpful error
- [ ] `--resume` with `--config` passes execution ID to orchestrator
- [ ] StateTracker loads existing checkpoint when resuming

---

### P3-T3: Externalize VERTICALS to YAML

**Priority**: MEDIUM
**Estimated LOC**: ~60
**Dependencies**: P2-T3, P2-T4

**Description**: Move hardcoded VERTICALS dict to YAML config with fallback.

**Input Files**:
- `src/research_orchestrator/prompts/vertical.py`

**Output Files**:
- `build/config/verticals.yaml` (new)
- `src/research_orchestrator/prompts/vertical.py` (modified)

**Contract Constraints** (from Guardian):
- TypedDict: `VerticalConfig` with name, description, key_regulations, key_challenges
- Keys: healthcare, financial_services, manufacturing, retail, technology
- Must fall back to hardcoded dict if YAML missing

**Implementation**:
```yaml
# build/config/verticals.yaml
healthcare:
  name: Healthcare
  description: Healthcare organizations including hospitals, clinics, and health systems
  key_regulations: HIPAA, HITECH, FDA regulations
  key_challenges: Data privacy, interoperability, patient engagement

financial_services:
  name: Financial Services
  description: Banks, insurance companies, and investment firms
  key_regulations: SOX, PCI-DSS, GDPR, Basel III
  key_challenges: Regulatory compliance, fraud prevention, digital transformation
# ... etc
```

```python
# vertical.py - update loading
import yaml
from pathlib import Path

_HARDCODED_VERTICALS = { ... }  # Keep as fallback

def _load_verticals() -> Dict[str, VerticalConfig]:
    yaml_path = Path(__file__).parent.parent.parent.parent / "build" / "config" / "verticals.yaml"
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load verticals.yaml, using defaults: {e}")
    return _HARDCODED_VERTICALS

VERTICALS = _load_verticals()
```

**Verification**:
```bash
# Verify YAML loads
python -c "
from research_orchestrator.prompts.vertical import VERTICALS
print(f'Loaded {len(VERTICALS)} verticals')
assert 'healthcare' in VERTICALS
"

# Run tests
pytest src/tests/ -v -k vertical
```

**Acceptance Criteria**:
- [ ] YAML file created with all 5 verticals
- [ ] Module loads from YAML when available
- [ ] Falls back to hardcoded dict if YAML missing
- [ ] New verticals addable via YAML without code changes

---

### P3-T4: Externalize TITLE_CLUSTERS to YAML

**Priority**: MEDIUM
**Estimated LOC**: ~60
**Dependencies**: P2-T3, P2-T4

**Description**: Move hardcoded TITLE_CLUSTERS dict to YAML config with fallback.

**Input Files**:
- `src/research_orchestrator/prompts/title.py`

**Output Files**:
- `build/config/title_clusters.yaml` (new)
- `src/research_orchestrator/prompts/title.py` (modified)

**Contract Constraints** (from Guardian):
- TypedDict: `TitleClusterConfig` with name, titles, decision_authority, key_focus
- Keys: cfo_cluster, cio_cto_cluster, vp_it_operations, procurement, business_unit

**Implementation**: Same pattern as P3-T3

**Verification**:
```bash
# Verify YAML loads
python -c "
from research_orchestrator.prompts.title import TITLE_CLUSTERS
print(f'Loaded {len(TITLE_CLUSTERS)} title clusters')
assert 'cfo_cluster' in TITLE_CLUSTERS
"
```

**Acceptance Criteria**:
- [ ] YAML file created with all 5 title clusters
- [ ] Module loads from YAML when available
- [ ] Falls back to hardcoded dict if YAML missing

---

## Phase 4: Operational Excellence

### P4-T1: Add .gitignore Patterns

**Priority**: LOW
**Estimated LOC**: ~20
**Dependencies**: P3-T1, P3-T2, P3-T3, P3-T4

**Description**: Add patterns to prevent accidental commit of sensitive files.

**Input Files**:
- `.gitignore` (may not exist)

**Output Files**:
- `.gitignore` (created or modified)

**Implementation**:
```gitignore
# Environment and credentials
.env
.env.local
.env.*.local
*.key
*.pem
credentials*.json

# Execution artifacts
checkpoints/
outputs/
logs/

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
```

**Verification**:
```bash
# Verify patterns work
echo "test" > .env.test
git status --porcelain | grep -q ".env.test" && echo "FAIL: .env.test should be ignored" || echo "OK"
rm .env.test
```

**Acceptance Criteria**:
- [ ] `.env*` files ignored
- [ ] `checkpoints/` and `outputs/` directories ignored
- [ ] Common Python artifacts ignored

---

### P4-T2: Create Circuit Breaker Module

**Priority**: LOW
**Estimated LOC**: ~100
**Dependencies**: P3-T1, P3-T2, P3-T3, P3-T4

**Description**: Add circuit breaker to prevent cascade failures during API issues.

**Input Files**:
- `src/research_orchestrator/research_session.py`

**Output Files**:
- `src/research_orchestrator/utils/circuit_breaker.py` (new)
- `src/research_orchestrator/research_session.py` (modified)

**Contract Constraints** (from Guardian):
- Use logger: `logging.getLogger('research_orchestrator')`
- Format: `f"[CircuitBreaker] {service_name}: {message}"`
- Integrate with `ResearchSession._api_call_with_retry()`
- Conservative thresholds: 5 failures, 60s timeout

**Implementation**:
```python
# circuit_breaker.py
import time
import logging
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED
        self.logger = logging.getLogger('research_orchestrator')

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.logger.info(f"[CircuitBreaker] {self.service_name}: Circuit closed")

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"[CircuitBreaker] {self.service_name}: Circuit opened after {self.failure_count} failures"
            )

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.logger.info(f"[CircuitBreaker] {self.service_name}: Circuit half-open, testing")
                return True
            return False
        return True  # HALF_OPEN

    def raise_if_open(self) -> None:
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker open for {self.service_name}"
            )

class CircuitBreakerOpenError(Exception):
    pass
```

**Verification**:
```bash
# Unit test circuit breaker
python -c "
from research_orchestrator.utils.circuit_breaker import CircuitBreaker, CircuitState

cb = CircuitBreaker('test', failure_threshold=3)
assert cb.state == CircuitState.CLOSED

for _ in range(3):
    cb.record_failure()

assert cb.state == CircuitState.OPEN
print('Circuit breaker works correctly')
"
```

**Acceptance Criteria**:
- [ ] Circuit breaker trips after 5 consecutive failures
- [ ] Circuit recovers after 60s timeout
- [ ] Integrated with ResearchSession API calls
- [ ] State changes logged

---

### P4-T3: Add Test Coverage

**Priority**: LOW
**Estimated LOC**: ~150
**Dependencies**: P3-T1, P3-T2, P3-T3, P3-T4

**Description**: Add tests for Layer 1, config inheritance, and budget errors.

**Input Files**:
- Existing test files for patterns

**Output Files**:
- `src/tests/test_layer_1.py` (new)
- `src/tests/test_config_inheritance.py` (new)
- `src/tests/test_budget_errors.py` (new)

**Contract Constraints** (from Guardian):
- Follow existing `@pytest.fixture` pattern
- Use `@pytest.mark.asyncio` for async tests
- Mock result dict must include all required fields

**Implementation**: Follow patterns from `test_orchestrator_layers.py`

**Verification**:
```bash
# Run new tests
pytest src/tests/test_layer_1.py src/tests/test_config_inheritance.py src/tests/test_budget_errors.py -v

# Check coverage
pytest --cov=research_orchestrator src/tests/ --cov-report=term-missing
```

**Acceptance Criteria**:
- [ ] Layer 1 execution tested
- [ ] Config inheritance tested
- [ ] Budget exceeded scenarios tested
- [ ] All new tests pass

---

## Execution Order (Recommended)

### Wave 1 (Parallel)
- P1-T1: Fix bare except
- P1-T2: Add path validation

### Wave 2 (Sequential)
- P2-T1: Create constants module
- P2-T2: Replace hardcoded models

### Wave 3 (Parallel)
- P2-T3: Accurate cost estimation
- P2-T4: Pydantic config validation

### Wave 4 (Parallel)
- P3-T1: Extract budget methods
- P3-T2: Resume functionality
- P3-T3: Externalize verticals
- P3-T4: Externalize title clusters

### Wave 5 (Parallel)
- P4-T1: Add .gitignore
- P4-T2: Circuit breaker
- P4-T3: Test coverage

---

## Files Summary

### New Files (7)
| File | Task |
|------|------|
| `src/research_orchestrator/utils/constants.py` | P2-T1 |
| `src/research_orchestrator/utils/config_schema.py` | P2-T4 |
| `src/research_orchestrator/utils/circuit_breaker.py` | P4-T2 |
| `build/config/verticals.yaml` | P3-T3 |
| `build/config/title_clusters.yaml` | P3-T4 |
| `src/tests/test_layer_1.py` | P4-T3 |
| `src/tests/test_config_inheritance.py` | P4-T3 |
| `src/tests/test_budget_errors.py` | P4-T3 |

### Modified Files (8)
| File | Tasks |
|------|-------|
| `src/research_orchestrator/state/tracker.py` | P1-T1 |
| `src/research_orchestrator/prompts/context_helpers.py` | P1-T2 |
| `src/research_orchestrator/research_session.py` | P2-T2, P2-T3, P4-T2 |
| `src/research_orchestrator/utils/config_models.py` | P2-T2, P2-T4 |
| `src/research_orchestrator/utils/config.py` | P2-T2 |
| `src/research_orchestrator/orchestrator.py` | P3-T1 |
| `src/run_research.py` | P3-T2 |
| `src/research_orchestrator/prompts/vertical.py` | P3-T3 |
| `src/research_orchestrator/prompts/title.py` | P3-T4 |
| `.gitignore` | P4-T1 |
