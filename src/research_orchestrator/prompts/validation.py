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

### 1. COMPLETENESS (20 points)

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
- 20 points: All sections present with substantive content
- 16 points: All sections present, some thin
- 12 points: 1-2 sections missing or very thin
- 8 points: 3+ sections missing
- 4 points: Major structural gaps

### 2. SPECIFICITY (20 points)

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
- 20 points: Highly specific throughout
- 16 points: Mostly specific with minor generic sections
- 12 points: Mixed specific/generic content
- 8 points: Mostly generic with some specificity
- 4 points: Almost entirely generic

### 3. ACTIONABILITY (20 points)

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
- 20 points: Ready for immediate use
- 16 points: Minor customization needed
- 12 points: Moderate work required to operationalize
- 8 points: Significant gaps in actionable content
- 4 points: Framework only, not actionable

### 4. RESEARCH GROUNDING (20 points)

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
- 20 points: Thoroughly grounded in research
- 16 points: Well-grounded with minor unsupported claims
- 12 points: Some grounding but gaps
- 8 points: Weakly grounded
- 4 points: Little connection to research

### 5. BRAND & MODEL ALIGNMENT (20 points)

{brand_context_section}

{proof_point_audit_section}

Check that the playbook accurately represents the company's business model, uses verified proof points, maintains brand positioning, and follows language standards:

**Alignment Indicators:**
- Business model description is accurate (compensation model, engagement type)
- Proof points and statistics are verified, not invented
- Value proposition language aligns with company positioning
- No invented pricing tiers, fees, or team structures
- Recommendations extend existing engagement model rather than inventing new ones
- Language Standards are followed (required terms used, prohibited terms absent)
- No claims from the UNVERIFIED CLAIMS list appear in the playbook

**Red Flags (AUTOMATIC DEDUCTIONS):**
- Uses prohibited terms (e.g., "independent advisor", "strategic technology audit", "outcome-based pricing", "not commission-based") → deduct 2 points per instance
- Contains claims matching UNVERIFIED CLAIMS list (e.g., "40+ financial institutions", "100% regulatory approval rate", unqualified "35% cost reduction" for specific verticals) → deduct 4 points per instance
- Invented statistics or proof points not from company data → deduct 4 points per instance
- Incorrect business model description (e.g., suggesting fees when service is vendor-reimbursed) → deduct 4 points
- Recommending "outcome-based pricing", "vendor certification programs", or other models incompatible with commission-based structure → deduct 4 points

**Additional Red Flags (deduct points):**
- Recommending organizational structures that contradict existing team composition
- Language that conflicts with brand positioning guidelines
- Missing champion enablement content (playbook only addresses 1:1 BDR outreach, not 25-person buying committees)

**Scoring:**
- 20 points: Fully aligned with company model, verified data, and language standards
- 16 points: Mostly aligned with minor language/terminology issues
- 12 points: Some alignment issues requiring correction
- 8 points: Significant model or brand misalignment, or unverified claims present
- 4 points: Fundamentally misrepresents the company

**Default (no brand context provided):** Award 12/20 — cannot assess language standards or proof point verification without company context.

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
| Completeness | /20 | [Brief assessment] |
| Specificity | /20 | [Brief assessment] |
| Actionability | /20 | [Brief assessment] |
| Research Grounding | /20 | [Brief assessment] |
| Brand & Model Alignment | /20 | [Brief assessment] |

### 3. LANGUAGE & CLAIM AUDIT

**Prohibited Terms Found:**
- [List each prohibited term found, with location in document]

**Unverified Claims Found:**
- [List each claim matching the UNVERIFIED CLAIMS list, with location]

**Language Standards Compliance:** [PASS / FAIL — list specific violations]

**Fabricated Statistics Found:**
- [List every quantitative claim in the playbook that does NOT appear in the Proof Point Audit reference above. If none, write NONE.]

**CAUTION Claims Used Without Qualification:**
- [List every CAUTION-flagged claim used in the playbook without its required qualifier. If none, write NONE.]

### 4. CRITICAL ISSUES (if any)

List any issues that MUST be fixed before the playbook is production-ready:
- [Issue 1]: [Specific problem and location]
- [Issue 2]: [Specific problem and location]

### 5. IMPROVEMENT RECOMMENDATIONS

List specific, actionable improvements (prioritized):
1. [High priority]: [Specific recommendation]
2. [Medium priority]: [Specific recommendation]
3. [Low priority]: [Specific recommendation]

### 6. STRENGTHS

Note what the playbook does well:
- [Strength 1]
- [Strength 2]

### 7. VERDICT

**IMPORTANT**: If the Language & Claim Audit (Section 3) found prohibited terms or
unverified claims, the playbook CANNOT be APPROVED regardless of total score.
Status must be NEEDS_REVISION at minimum until language compliance is achieved.

**Status**: [APPROVED | NEEDS_REVISION | REJECTED]

- **APPROVED** (80+ points, AND language audit PASS): Ready for production use
- **NEEDS_REVISION** (60-79 points, OR language audit FAIL): Specific issues must be addressed
- **REJECTED** (<60 points): Fundamental problems require regeneration

**Rationale**: [1-2 sentences explaining the verdict]

---

Begin validation now. Be rigorous but fair.
"""


def build_validation_prompt(
    playbook_content: str,
    vertical_name: str,
    title_name: str,
    service_category_name: str | None = None,
    brand_context: str = "",
    proof_point_audit: str = ""
) -> str:
    """
    Build validation prompt for a specific playbook.

    Args:
        playbook_content: Full markdown content of the playbook
        vertical_name: Display name of the vertical (e.g., "Healthcare")
        title_name: Display name of the title cluster (e.g., "CFO")
        service_category_name: Optional service category name for 3D playbooks
        brand_context: Optional pre-formatted brand/company context string
        proof_point_audit: Optional proof point audit for cross-checking claims

    Returns:
        Formatted validation prompt ready for execution
    """
    sc_name = service_category_name or "N/A"

    if brand_context:
        brand_section = (
            f"**Company context for alignment checking:**\n\n{brand_context}"
        )
    else:
        brand_section = (
            "No company context provided. Use default scoring (16/20) for this dimension."
        )

    if proof_point_audit:
        audit_section = (
            f"**QUANTITATIVE CLAIM CROSS-CHECK (MANDATORY):**\n\n{proof_point_audit}"
        )
    else:
        audit_section = ""

    return VALIDATION_PROMPT.format(
        playbook_content=playbook_content,
        vertical_name=vertical_name,
        title_name=title_name,
        service_category_name=sc_name,
        brand_context_section=brand_section,
        proof_point_audit_section=audit_section
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
