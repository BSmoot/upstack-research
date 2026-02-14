"""Unit tests for validation prompt building functions."""

import pytest

from research_orchestrator.prompts.validation import (
    build_validation_prompt,
    build_batch_validation_prompt,
)


class TestBuildValidationPrompt:
    """Test build_validation_prompt function."""

    def test_includes_playbook_content(self):
        result = build_validation_prompt(
            playbook_content="Test playbook about healthcare security",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "Test playbook about healthcare security" in result

    def test_includes_vertical_name(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "Healthcare" in result

    def test_includes_title_name(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "CIO" in result

    def test_includes_service_category_when_provided(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            service_category_name="Security",
        )
        assert "Security" in result

    def test_service_category_defaults_to_na(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "N/A" in result

    def test_includes_completeness_dimension(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "COMPLETENESS" in result
        assert "20 points" in result

    def test_includes_specificity_dimension(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "SPECIFICITY" in result
        assert "20 points" in result

    def test_includes_actionability_dimension(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "ACTIONABILITY" in result
        assert "20 points" in result

    def test_includes_research_grounding_dimension(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "RESEARCH GROUNDING" in result
        assert "20 points" in result

    def test_includes_brand_alignment_dimension(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "BRAND & MODEL ALIGNMENT" in result
        assert "20 points" in result

    def test_includes_approved_threshold(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "APPROVED" in result
        assert "80+" in result

    def test_includes_needs_revision_threshold(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "NEEDS_REVISION" in result
        assert "60-79" in result

    def test_includes_rejected_threshold(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "REJECTED" in result
        assert "<60" in result

    def test_includes_deliverable_sections(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "VALIDATION SUMMARY" in result
        assert "DIMENSION SCORES" in result
        assert "CRITICAL ISSUES" in result
        assert "IMPROVEMENT RECOMMENDATIONS" in result
        assert "STRENGTHS" in result
        assert "VERDICT" in result

    def test_handles_empty_playbook_content(self):
        result = build_validation_prompt(
            playbook_content="",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert isinstance(result, str)
        assert "COMPLETENESS" in result

    def test_handles_special_characters_in_content(self):
        """Content with curly braces and backticks should not break formatting."""
        content = "Playbook with {curly braces} and `backticks` and ```code blocks```"
        # This should not raise - curly braces that aren't template vars
        # would cause KeyError with str.format(), but the content is inserted
        # as a pre-formatted value, not as a template
        result = build_validation_prompt(
            playbook_content=content,
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert content in result


class TestBuildValidationPromptBrandContext:
    """Test build_validation_prompt with brand context parameter."""

    def test_brand_context_included_when_provided(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            brand_context="**Company**: TestCorp\n**Model**: Vendor-reimbursed"
        )
        assert "TestCorp" in result
        assert "Vendor-reimbursed" in result
        assert "Company context for alignment checking" in result

    def test_default_scoring_when_no_brand_context(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "16/20" in result
        assert "No company context provided" in result

    def test_dimension_scores_table_has_five_rows(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert "/20" in result
        assert "Brand & Model Alignment" in result
        # Check all 5 dimension headers
        assert "Completeness" in result
        assert "Specificity" in result
        assert "Actionability" in result
        assert "Research Grounding" in result
        assert "Brand & Model Alignment" in result

    def test_backward_compatible_without_brand_context(self):
        """Test that prompt works without brand_context (default empty string)."""
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert isinstance(result, str)
        assert "BRAND & MODEL ALIGNMENT" in result


class TestBuildValidationPromptAudit:
    """Test build_validation_prompt with proof_point_audit parameter."""

    def test_audit_included_when_provided(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            proof_point_audit="### VERIFIED CLAIMS\n- [VERIFIED] 99.8% retention"
        )
        assert "QUANTITATIVE CLAIM CROSS-CHECK" in result
        assert "99.8% retention" in result

    def test_audit_section_contains_fabricated_stats_deliverable(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            proof_point_audit="### VERIFIED CLAIMS\n- [VERIFIED] 99.8% retention"
        )
        assert "Fabricated Statistics Found:" in result

    def test_audit_section_contains_caution_claims_deliverable(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            proof_point_audit="### CAUTION CLAIMS\n- [CAUTION] 76-day timeline"
        )
        assert "CAUTION Claims Used Without Qualification:" in result

    def test_backward_compatible_without_audit(self):
        """Prompt works without proof_point_audit (default empty string)."""
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
        )
        assert isinstance(result, str)
        assert "QUANTITATIVE CLAIM CROSS-CHECK" not in result
        assert "BRAND & MODEL ALIGNMENT" in result

    def test_audit_and_brand_context_coexist(self):
        result = build_validation_prompt(
            playbook_content="content",
            vertical_name="Healthcare",
            title_name="CIO",
            brand_context="**Company**: TestCorp",
            proof_point_audit="### VERIFIED CLAIMS\n- [VERIFIED] test stat"
        )
        assert "TestCorp" in result
        assert "QUANTITATIVE CLAIM CROSS-CHECK" in result
        assert "test stat" in result


class TestBuildBatchValidationPrompt:
    """Test build_batch_validation_prompt function."""

    def test_includes_total_count(self):
        result = build_batch_validation_prompt(
            playbook_summaries=[],
            total_playbooks=3,
        )
        assert "Total Playbooks Validated: 3" in result

    def test_includes_playbook_names(self):
        summaries = [
            {"name": "healthcare_cio_security", "status": "APPROVED", "score": 85},
            {"name": "legal_cfo_network", "status": "NEEDS_REVISION", "score": 72},
        ]
        result = build_batch_validation_prompt(summaries, total_playbooks=2)
        assert "healthcare_cio_security" in result
        assert "legal_cfo_network" in result

    def test_includes_playbook_scores(self):
        summaries = [
            {"name": "test_playbook", "status": "APPROVED", "score": 85},
        ]
        result = build_batch_validation_prompt(summaries, total_playbooks=1)
        assert "85/100" in result

    def test_includes_playbook_status(self):
        summaries = [
            {"name": "test_playbook", "status": "APPROVED", "score": 85},
            {"name": "test_playbook_2", "status": "REJECTED", "score": 45},
        ]
        result = build_batch_validation_prompt(summaries, total_playbooks=2)
        assert "APPROVED" in result
        assert "REJECTED" in result

    def test_handles_empty_list(self):
        result = build_batch_validation_prompt(
            playbook_summaries=[],
            total_playbooks=0,
        )
        assert isinstance(result, str)
        assert "Total Playbooks Validated: 0" in result

    def test_includes_aggregate_sections(self):
        summaries = [
            {"name": "test", "status": "APPROVED", "score": 90},
        ]
        result = build_batch_validation_prompt(summaries, total_playbooks=1)
        assert "Aggregate Statistics" in result
        assert "Common Issues" in result
