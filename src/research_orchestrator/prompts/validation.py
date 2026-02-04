# research_orchestrator/prompts/validation.py
"""
Validation Agent: Quality Gate for Research Outputs

Assesses playbook completeness, accuracy, and actionability before
outputs are considered production-ready.
"""

from typing import Any
from pathlib import Path

from .context_helpers import extract_summary


VALIDATION_PROMPT = """
You are the Research Validation Agent.

MISSION: Assess the quality of the generated playbook and provide a validation report with specific, actionable feedback.

PLAYBOOK TO VALIDATE:
{playbook_content}

PLAYBOOK METADATA:
- Vertical: {vertical_name}
- Title: {title_name}
- Service Category: {service_category_name}

---

## VALIDATION CRITERIA

Evaluate the playbook against these quality dimensions:

### 1. COMPLETENESS (25 points)

Check that ALL required sections are present and substantive:

**Required Sections:**
- [ ] Executive Summary (clear value proposition, key pain points)
- [ ] Target Profile (vertical context, title context, combined profile)
- [ ] Messaging Framework (value proposition, key messages, proof points)
- [ ] Outbound Sequence (multi-touch campaign with specific copy)
- [ ] Objection Handling (at least 3 objections with responses)
- [ ] Timing & Triggers (best timing, trigger events)
- [ ] Implementation Checklist (content assets, sales enablement)
- [ ] Research Integration Notes (Layer 0/1/2/3 sources)

**Scoring:**
- 25 points: All sections present with substantive content
- 20 points: All sections present, some thin
- 15 points: 1-2 sections missing or very thin
- 10 points: 3+ sections missing
- 5 points: Major structural gaps

### 2. SPECIFICITY (25 points)

Check that content is specific to the V × T × SC combination, not generic:

**Specificity Indicators:**
- Uses {vertical_name}-specific terminology and regulations
- Addresses {title_name}-specific pain points and decision authority
- References {service_category_name} vendors by name
- Includes {service_category_name}-specific evaluation criteria
- Email/LinkedIn copy mentions vertical context, not generic B2B language

**Red Flags (deduct points):**
- Generic "technology solutions" language
- No mention of specific vendors
- Pain points could apply to any vertical
- Messaging lacks role-specific framing

**Scoring:**
- 25 points: Highly specific throughout
- 20 points: Mostly specific with minor generic sections
- 15 points: Mixed specific/generic content
- 10 points: Mostly generic with some specificity
- 5 points: Almost entirely generic

### 3. ACTIONABILITY (25 points)

Check that the playbook can be immediately used by sales/marketing:

**Actionability Indicators:**
- Email subject lines and body copy are ready to use
- LinkedIn messages are complete, not templates
- Discovery questions are specific and insightful
- Objection responses include specific proof points
- Implementation checklist has concrete items

**Red Flags (deduct points):**
- "[Insert specific example here]" placeholders
- "Customize for your situation" instructions
- Vague action items like "create relevant content"
- Missing outreach channel details

**Scoring:**
- 25 points: Ready for immediate use
- 20 points: Minor customization needed
- 15 points: Moderate work required to operationalize
- 10 points: Significant gaps in actionable content
- 5 points: Framework only, not actionable

### 4. RESEARCH GROUNDING (25 points)

Check that recommendations are grounded in research from prior layers:

**Grounding Indicators:**
- Research Integration Notes section cites specific findings
- Pain points traced back to Layer 2/3 research
- Vendor positioning based on Layer 0/1 competitive analysis
- Messaging language derived from Layer 1 buyer journey research
- Trigger events based on Layer 2 vertical research

**Red Flags (deduct points):**
- Recommendations with no research backing
- Contradicts findings from prior layers
- Makes claims not supported by research
- Generic "best practices" not from research

**Scoring:**
- 25 points: Thoroughly grounded in research
- 20 points: Well-grounded with minor unsupported claims
- 15 points: Some grounding but gaps
- 10 points: Weakly grounded
- 5 points: Little connection to research

---

## DELIVERABLES

Provide a structured validation report:

### 1. VALIDATION SUMMARY

```
PLAYBOOK: {vertical_name} × {title_name} × {service_category_name}
OVERALL SCORE: [X/100]
STATUS: [APPROVED | NEEDS_REVISION | REJECTED]
```

### 2. DIMENSION SCORES

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Completeness | /25 | [Brief assessment] |
| Specificity | /25 | [Brief assessment] |
| Actionability | /25 | [Brief assessment] |
| Research Grounding | /25 | [Brief assessment] |

### 3. CRITICAL ISSUES (if any)

List any issues that MUST be fixed before the playbook is production-ready:
- [Issue 1]: [Specific problem and location]
- [Issue 2]: [Specific problem and location]

### 4. IMPROVEMENT RECOMMENDATIONS

List specific, actionable improvements (prioritized):
1. [High priority]: [Specific recommendation]
2. [Medium priority]: [Specific recommendation]
3. [Low priority]: [Specific recommendation]

### 5. STRENGTHS

Note what the playbook does well:
- [Strength 1]
- [Strength 2]

### 6. VERDICT

**Status**: [APPROVED | NEEDS_REVISION | REJECTED]

- **APPROVED** (80+ points): Ready for production use
- **NEEDS_REVISION** (60-79 points): Specific issues must be addressed
- **REJECTED** (<60 points): Fundamental problems require regeneration

**Rationale**: [1-2 sentences explaining the verdict]

---

Begin validation now. Be rigorous but fair.
"""


def build_validation_prompt(
    playbook_content: str,
    vertical_name: str,
    title_name: str,
    service_category_name: str | None = None
) -> str:
    """
    Build validation prompt for a specific playbook.

    Args:
        playbook_content: Full markdown content of the playbook
        vertical_name: Display name of the vertical (e.g., "Healthcare")
        title_name: Display name of the title cluster (e.g., "CFO")
        service_category_name: Optional service category name for 3D playbooks

    Returns:
        Formatted validation prompt ready for execution
    """
    sc_name = service_category_name or "N/A"

    return VALIDATION_PROMPT.format(
        playbook_content=playbook_content,
        vertical_name=vertical_name,
        title_name=title_name,
        service_category_name=sc_name
    )


def build_batch_validation_prompt(
    playbook_summaries: list[dict[str, Any]],
    total_playbooks: int
) -> str:
    """
    Build a batch validation summary prompt for multiple playbooks.

    Args:
        playbook_summaries: List of dicts with playbook metadata and validation results
        total_playbooks: Total number of playbooks validated

    Returns:
        Formatted batch summary prompt
    """
    summary_lines = []
    for pb in playbook_summaries:
        summary_lines.append(
            f"- {pb.get('name', 'Unknown')}: {pb.get('status', 'N/A')} "
            f"({pb.get('score', 0)}/100)"
        )

    return f"""
## BATCH VALIDATION SUMMARY

Total Playbooks Validated: {total_playbooks}

### Individual Results:
{chr(10).join(summary_lines)}

### Aggregate Statistics:
- Approved: [count]
- Needs Revision: [count]
- Rejected: [count]
- Average Score: [X/100]

### Common Issues Across Playbooks:
[List patterns of issues that appear in multiple playbooks]

### Recommendations for System Improvement:
[If issues are systemic, recommend prompt or process improvements]
"""
