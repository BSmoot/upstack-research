"""Unit tests for target research prompt builder."""

import pytest

from research_orchestrator.prompts.target_research import (
    build_target_research_prompt,
    TARGET_RESEARCH_PROMPT_TEMPLATE,
)


class TestBuildTargetResearchPrompt:
    """Test build_target_research_prompt function."""

    def test_includes_company_name(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Acme Health" in result

    def test_includes_industry(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Healthcare" in result

    def test_includes_size_when_provided(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
            company_size="5,000-10,000 employees",
        )
        assert "5,000-10,000 employees" in result

    def test_includes_location_when_provided(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
            company_location="Chicago, IL",
        )
        assert "Chicago, IL" in result

    def test_defaults_unknown_for_missing_size(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Unknown" in result

    def test_includes_known_context_when_provided(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
            known_context="They use Epic for EHR and AWS for cloud.",
        )
        assert "They use Epic for EHR" in result
        assert "Pre-Existing Intelligence" in result

    def test_excludes_known_context_when_empty(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Pre-Existing Intelligence" not in result

    def test_includes_company_context_when_provided(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
            company_context="We are a technology advisory firm.",
        )
        assert "We are a technology advisory firm" in result
        assert "Our Company Context" in result

    def test_excludes_company_context_when_empty(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Our Company Context" not in result

    def test_includes_all_five_research_categories(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Category 4: Company Profile & Technology Stack" in result
        assert "Category 1: Problems & Decision Making" in result
        assert "Category 3: Whitespace & Portfolio Gaps" in result
        assert "Category 5: Upcoming Needs & Projects" in result
        assert "Category 8: North-Star Signals & Thought Leadership" in result

    def test_includes_confidence_tagging_instructions(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "confirmed" in result
        assert "inferred" in result
        assert "speculative" in result

    def test_includes_yaml_output_format(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "known_stack:" in result
        assert "decision_making:" in result
        assert "whitespace:" in result
        assert "upcoming_needs:" in result
        assert "north_star:" in result

    def test_includes_max_searches(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
            max_searches=30,
        )
        assert "30" in result

    def test_default_max_searches_is_40(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "40" in result

    def test_generates_company_slug(self):
        result = build_target_research_prompt(
            company_name="Acme Health System",
            company_industry="Healthcare",
        )
        assert "acme_health_system" in result

    def test_minimal_seed_produces_valid_prompt(self):
        """With just a name, prompt should still be valid."""
        result = build_target_research_prompt(
            company_name="Acme",
            company_industry="",
        )
        assert "Acme" in result
        assert "Category 4" in result
        assert "Category 1" in result

    def test_full_seed_produces_complete_prompt(self):
        result = build_target_research_prompt(
            company_name="Acme Health System",
            company_industry="Healthcare",
            company_size="10,000+ employees",
            company_location="Chicago, IL",
            known_context="Uses Epic EHR, AWS cloud",
            company_context="Technology advisory firm",
            max_searches=50,
        )
        assert "Acme Health System" in result
        assert "Healthcare" in result
        assert "10,000+ employees" in result
        assert "Chicago, IL" in result
        assert "Epic EHR" in result
        assert "Technology advisory firm" in result
        assert "50" in result

    def test_excludes_manual_categories(self):
        result = build_target_research_prompt(
            company_name="Acme Health",
            company_industry="Healthcare",
        )
        assert "Do NOT research Categories 2" in result
        assert "manual_sections" in result


class TestTargetResearchPromptTemplate:
    """Test the template string itself."""

    def test_template_has_required_placeholders(self):
        assert "{company_name}" in TARGET_RESEARCH_PROMPT_TEMPLATE
        assert "{company_industry}" in TARGET_RESEARCH_PROMPT_TEMPLATE
        assert "{company_size}" in TARGET_RESEARCH_PROMPT_TEMPLATE
        assert "{company_location}" in TARGET_RESEARCH_PROMPT_TEMPLATE
        assert "{max_searches}" in TARGET_RESEARCH_PROMPT_TEMPLATE
