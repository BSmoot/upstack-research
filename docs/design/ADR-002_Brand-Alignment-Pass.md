# Architecture Decision Record: Brand Alignment Pass

**ADR ID**: ADR-002
**Title**: Brand Alignment Pass for Research Outputs
**Status**: Proposed
**Date**: 2026-01-25
**Authors**: apex-architect, apex-guardian

---

## Context

The research orchestrator produces multi-layer research outputs (horizontal research, vertical research, title research, and playbooks) for a vendor-neutral technology advisory firm. While the research quality is high, outputs do not consistently reflect brand positioning, writing standards, or audience preferences defined in the company's shared context files.

Four brand context files exist but are not currently used:
- `research-manager/context/baseline.yaml` - Company facts, services, value proposition, trust model (217 lines, ~10KB)
- `research-manager/context/writing-standards.yaml` - Tone, voice, LLM patterns to avoid (114 lines, ~4KB)
- `research-manager/context/audience-personas.yaml` - Role profiles, communication preferences (466 lines, ~17KB)
- `research-manager/context/glossary.yaml` - Industry terminology definitions (1043 lines, ~35KB)

**Problem Statement**: Research outputs may use inconsistent terminology, violate writing standards (e.g., LLM patterns like "Additionally, Furthermore, Moreover"), or miss opportunities to align with company positioning. Without brand alignment, outputs require manual review and editing before use.

**Design Constraint**: Brand alignment should be a **FINAL pass** rather than modifying research prompts. This preserves the general research capabilities and avoids biasing research toward company positioning during the discovery phase.

---

## Decision

Implement a **Brand Alignment Pass** as a new post-processing stage that runs after playbook generation. This stage:

1. **Loads brand context** from configurable YAML files at orchestrator initialization
2. **Runs a BrandAlignmentAgent** on each final playbook output (not intermediate layer outputs)
3. **Produces aligned versions** saved alongside original outputs (e.g., `playbook_healthcare_cfo.aligned.md`)
4. **Is configurable** per-project via config YAML with ability to:
   - Enable/disable the pass
   - Specify which context files to load
   - Override context file paths for different brand contexts

### Architecture

```
Layer 1 → Layer 2 → Layer 3 → Playbooks → [NEW] Brand Alignment Pass
                                              ↓
                               playbook_vertical_title.md
                               playbook_vertical_title.aligned.md
```

---

## Implementation Specification

### 1. Configuration Schema Addition

Add to `build/config/defaults.yaml`:

```yaml
brand_alignment:
  enabled: true

  # Context files to load (relative to config file or absolute)
  context_files:
    baseline: "../../../research-manager/context/baseline.yaml"
    writing_standards: "../../../research-manager/context/writing-standards.yaml"
    audience_personas: "../../../research-manager/context/audience-personas.yaml"
    glossary: "../../../research-manager/context/glossary.yaml"

  # Which outputs to align (default: playbooks only)
  align_targets:
    - "playbooks"  # Only final outputs

  # Model for alignment pass (smaller model sufficient since no research needed)
  model: "claude-haiku-4-5-20251001"

  # Output behavior
  output:
    suffix: ".aligned"  # Creates playbook_x_y.aligned.md alongside original
    replace_original: false  # If true, overwrites instead of creating new file
```

### 2. Brand Context Loader Module

New file: `src/research_orchestrator/utils/brand_context.py`

```python
"""
Brand context loading and caching utilities.
Loads YAML context files once and provides formatted context for prompts.
"""

from pathlib import Path
from typing import Dict, Any
import yaml

class BrandContextLoader:
    """Loads and caches brand context files for injection into alignment prompts."""

    def __init__(self, config: Dict[str, Any], base_path: Path):
        self.config = config.get('brand_alignment', {})
        self.base_path = base_path
        self._context_cache: Dict[str, Dict] = {}

    def load_all_context(self) -> Dict[str, Dict]:
        """Load all configured context files. Caches on first call."""
        if self._context_cache:
            return self._context_cache

        context_files = self.config.get('context_files', {})
        for key, rel_path in context_files.items():
            full_path = (self.base_path / rel_path).resolve()
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    self._context_cache[key] = yaml.safe_load(f)

        return self._context_cache

    def format_for_prompt(self, max_tokens: int = 8000) -> str:
        """Format loaded context for inclusion in alignment prompt."""
        context = self.load_all_context()

        sections = []

        # Baseline (always include - critical brand facts)
        if 'baseline' in context:
            sections.append(self._format_baseline(context['baseline']))

        # Writing standards (always include - defines output quality)
        if 'writing_standards' in context:
            sections.append(self._format_writing_standards(context['writing_standards']))

        # Audience personas (summary only - full file too large)
        if 'audience_personas' in context:
            sections.append(self._format_personas_summary(context['audience_personas']))

        # Glossary (only key terms, not full 1000+ line file)
        if 'glossary' in context:
            sections.append(self._format_glossary_highlights(context['glossary']))

        return "\n\n---\n\n".join(sections)
```

### 3. Brand Alignment Agent Prompt

New file: `src/research_orchestrator/prompts/brand_alignment.py`

```python
BRAND_ALIGNMENT_PROMPT = """
You are the Brand Alignment Agent.

MISSION: Review and refine the research output below to ensure it aligns with company brand guidelines, writing standards, and audience expectations while preserving all substantive research content.

{brand_context}

---

ORIGINAL RESEARCH OUTPUT:

{original_content}

---

YOUR ALIGNMENT TASK:

1. WRITING STANDARDS COMPLIANCE
   - Remove LLM patterns: "Additionally", "Furthermore", "Moreover", "It's important to note"
   - Apply natural writing: vary sentence length, use contractions, prefer "And/But/So"
   - Ensure density without terseness - every sentence adds value
   - Check for em-dash overuse (max 1 per paragraph)

2. TERMINOLOGY ALIGNMENT
   - Use correct industry terminology per glossary
   - Ensure company name and services are referenced correctly
   - Apply vertical/title-specific language where appropriate

3. AUDIENCE FIT
   - Verify content respects audience expertise (never patronizing)
   - Check that proof points and metrics match what this audience finds credible
   - Ensure structure follows preferred format (Executive Summary first, scannable)

4. BRAND VOICE
   - Professional but conversational
   - Direct and evidence-based
   - Peer-to-peer, not vendor-to-customer
   - Include both benefits AND limitations/risks

5. VALUE PROPOSITION ALIGNMENT
   - Ensure messaging aligns with company positioning
   - Trust model language is consistent (vendor-neutral, vendor-reimbursed)
   - Service descriptions match baseline definitions

CRITICAL CONSTRAINTS:
- DO NOT remove or significantly alter research findings, data, or conclusions
- DO NOT add claims not supported by the original research
- DO NOT change the document structure unless it violates audience preferences
- DO preserve all source citations and confidence assessments
- DO maintain the original depth and specificity

DELIVERABLE:
Produce the aligned version of the document. Output ONLY the refined document with no preamble.
"""
```

### 4. Orchestrator Integration

Modify `src/research_orchestrator/orchestrator.py`:

```python
# In execute_full_research(), after playbook generation:

async def execute_full_research(self):
    # ... existing layer execution ...

    # Integration: Generate Playbooks
    await self.generate_playbooks_parallel()

    # NEW: Brand Alignment Pass (if enabled)
    if self.config.get('brand_alignment', {}).get('enabled', False):
        self.logger.info("\n" + "=" * 80)
        self.logger.info("BRAND ALIGNMENT: Aligning Playbooks")
        self.logger.info("=" * 80)
        await self.execute_brand_alignment()

    # Final summary
    self._print_execution_summary()
```

---

## Why Only Playbooks (Not All Outputs)

The decision to align only final playbooks (not Layer 1-3 outputs) is intentional:

- **Research Integrity**: Layer 1-3 outputs are research artifacts. Aligning them could introduce bias or remove important nuances discovered during research.
- **Efficiency**: Running alignment on all outputs would add significant cost/time. Playbooks are the customer-facing deliverables that need brand consistency.
- **Future Extensibility**: The `align_targets` config allows enabling alignment for other layers if needed.

---

## Consequences

### Positive
- Research outputs will consistently reflect brand positioning without manual editing
- Writing quality improved (LLM patterns removed)
- Terminology consistency across all playbooks
- Configurable per-project for different brand contexts
- Original outputs preserved for comparison/audit

### Negative
- Additional processing time (~30-60 seconds per playbook)
- Additional cost (~$0.50-1.00 per playbook with Haiku)
- Context files must be maintained and kept in sync with company positioning
- Aligned outputs may occasionally lose nuance from aggressive editing

### Risks
| Risk | Mitigation |
|------|------------|
| Context file staleness | Add version/updated timestamp to config, warn if files older than 90 days |
| Over-alignment | Explicit constraint in prompt to preserve research substance |
| Large context files | `format_for_prompt()` summarizes relevant portions, not full injection |

---

## Guardian Analysis: Integration Contracts

### Critical Constraints Identified

1. **State Tracker Updates Required**
   - Add `'brand_alignment'` to state initialization (tracker.py line 77)
   - Add `'brand_alignment'` to `is_agent_complete()` search list (line 123)
   - Add `initialize_brand_alignment()` method

2. **Layer Enumeration Hardcoding**
   - Multiple places hardcode layer names that must be updated
   - `StateTracker.is_agent_complete()`, `get_agent_output()`, `get_context_for_agent()`

3. **Output Directory Structure**
   - Add `'brand_alignment'` to directory creation loop (orchestrator.py line 123)

4. **Config Schema**
   - Add `BrandAlignmentConfig` Pydantic model
   - Add `after_playbooks` to `ReviewGatesConfig`

### Gaps to Address

| Gap | Required Action |
|-----|-----------------|
| No review gate after playbooks | Add `after_playbooks: bool = False` to ReviewGatesConfig |
| Brand context loader missing | Create `utils/brand_context.py` |
| Alignment agent doesn't use ResearchSession | Create new `_execute_alignment_agent()` pattern |
| Aligned output naming | Use `.aligned.md` suffix pattern |

---

## Files to Create

- `src/research_orchestrator/utils/brand_context.py` - Context loader and formatter
- `src/research_orchestrator/prompts/brand_alignment.py` - Alignment prompt template

## Files to Modify

- `src/research_orchestrator/orchestrator.py` - Add brand alignment stage
- `src/research_orchestrator/state/tracker.py` - Add brand_alignment layer support
- `src/research_orchestrator/prompts/__init__.py` - Export brand alignment prompt
- `build/config/defaults.yaml` - Add brand_alignment config section
- `src/research_orchestrator/utils/config_schema.py` - Add validation models

---

## Migration

No migration needed. Feature is additive and disabled by default until explicitly enabled in config.

---

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Inject brand context into all research prompts | Would bias research toward company positioning |
| Prompt-level brand instructions only | Wouldn't leverage existing detailed brand context files |
| Post-process all layers | Intermediate research artifacts should remain unbiased |
| Human review instead of automated | Adds manual step to every research run |
