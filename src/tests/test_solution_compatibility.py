"""Unit tests for solution compatibility corpus prompt builder."""

import pytest

from research_orchestrator.prompts.solution_compatibility import (
    build_solution_compatibility_prompt,
    SOLUTION_COMPATIBILITY_PROMPT,
)


class TestBuildSolutionCompatibilityPrompt:
    """Test build_solution_compatibility_prompt function."""

    def test_includes_technology_stack(self):
        stack = {
            "network": "Cisco Meraki",
            "security": ["CrowdStrike", "Palo Alto Networks"],
        }
        result = build_solution_compatibility_prompt(
            target_stack=stack,
            service_categories=["security"],
        )
        assert "Cisco Meraki" in result
        assert "CrowdStrike" in result
        assert "Palo Alto Networks" in result

    def test_formats_list_values(self):
        stack = {"cloud": ["AWS", "Azure", "GCP"]}
        result = build_solution_compatibility_prompt(
            target_stack=stack,
            service_categories=["cloud"],
        )
        assert "AWS, Azure, GCP" in result

    def test_formats_string_values(self):
        stack = {"ehr": "Epic"}
        result = build_solution_compatibility_prompt(
            target_stack=stack,
            service_categories=["healthcare_it"],
        )
        assert "Epic" in result

    def test_includes_service_categories(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco"},
            service_categories=["security", "cloud", "network"],
        )
        assert "Security" in result
        assert "Cloud" in result
        assert "Network" in result

    def test_empty_stack_produces_valid_prompt(self):
        result = build_solution_compatibility_prompt(
            target_stack={},
            service_categories=["security"],
        )
        assert "No specific technology stack provided" in result
        assert "compatible_with:" in result

    def test_empty_categories_produces_valid_prompt(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco"},
            service_categories=[],
        )
        assert "No specific service categories provided" in result

    def test_includes_company_context_when_provided(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco"},
            service_categories=["network"],
            company_context="We are a technology advisory firm.",
        )
        assert "We are a technology advisory firm" in result
        assert "Advisory Context" in result

    def test_excludes_company_context_when_empty(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco"},
            service_categories=["network"],
        )
        assert "Advisory Context" not in result

    def test_includes_compatibility_structure(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco Meraki"},
            service_categories=["network"],
        )
        assert "compatible_with:" in result
        assert "conflicts_with:" in result
        assert "requires_middleware:" in result

    def test_includes_ecosystem_section(self):
        result = build_solution_compatibility_prompt(
            target_stack={"cloud": "AWS"},
            service_categories=["cloud"],
        )
        assert "platform_ecosystems:" in result

    def test_includes_lock_in_section(self):
        result = build_solution_compatibility_prompt(
            target_stack={"cloud": "AWS"},
            service_categories=["cloud"],
        )
        assert "vendor_lock_in_risks:" in result

    def test_includes_confidence_tagging(self):
        result = build_solution_compatibility_prompt(
            target_stack={"network": "Cisco"},
            service_categories=["network"],
        )
        assert "confirmed" in result
        assert "inferred" in result
        assert "speculative" in result

    def test_category_label_formatting(self):
        """Short category keys should be uppercased, longer ones title-cased."""
        stack = {
            "ehr": "Epic",
            "customer_experience": "Salesforce",
        }
        result = build_solution_compatibility_prompt(
            target_stack=stack,
            service_categories=[],
        )
        assert "EHR" in result
        assert "Customer Experience" in result

    def test_full_stack_produces_complete_prompt(self):
        stack = {
            "ehr": "Epic",
            "crm": "Salesforce Health Cloud",
            "cloud": ["AWS", "Azure"],
            "network": "Cisco Meraki",
            "security": ["CrowdStrike", "Palo Alto Networks"],
            "communications": "Microsoft Teams",
        }
        result = build_solution_compatibility_prompt(
            target_stack=stack,
            service_categories=["security", "cloud", "network"],
            company_context="Technology advisory firm",
        )
        assert "Epic" in result
        assert "Salesforce Health Cloud" in result
        assert "Cisco Meraki" in result
        assert "Technology advisory firm" in result


class TestSolutionCompatibilityPromptTemplate:
    """Test the template string itself."""

    def test_template_has_required_placeholders(self):
        assert "{target_stack_section}" in SOLUTION_COMPATIBILITY_PROMPT
        assert "{service_categories_section}" in SOLUTION_COMPATIBILITY_PROMPT
        assert "{company_context_section}" in SOLUTION_COMPATIBILITY_PROMPT
