"""Brand alignment prompt for aligning research outputs with brand context."""

BRAND_ALIGNMENT_PROMPT = """You are a brand alignment specialist. Your task is to review and align the following research output with our brand context.

# Brand Context

{brand_context}

# Original Content to Align

{original_content}

# Your Task

Review the original content and rewrite it to align with our brand context while preserving:
- All factual information and research findings
- The original structure and organization
- Key insights and recommendations

Apply brand alignment by:
1. Adjusting tone and voice to match brand standards
2. Using preferred terminology from the glossary
3. Ensuring messaging aligns with brand positioning
4. Formatting according to writing standards
5. Tailoring language for target audience personas

# Output Requirements

Return the aligned content in the same format as the original (markdown).

DO NOT:
- Change factual claims or research findings
- Remove important details or insights
- Add new research that wasn't in the original
- Alter the core structure

DO:
- Refine language and phrasing for brand consistency
- Replace generic terms with brand-specific terminology
- Adjust tone to match brand voice
- Ensure formatting matches brand standards

Begin the aligned content below:

---
"""


def build_brand_alignment_prompt(original_content: str, brand_context: str) -> str:
    """
    Build brand alignment prompt with original content and brand context.

    Args:
        original_content: Original research output to align
        brand_context: Formatted brand context string

    Returns:
        Complete brand alignment prompt
    """
    return BRAND_ALIGNMENT_PROMPT.format(
        brand_context=brand_context,
        original_content=original_content
    )
