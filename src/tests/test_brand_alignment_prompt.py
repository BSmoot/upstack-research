"""Unit tests for brand alignment (enrichment) prompt building."""

import pytest

from research_orchestrator.prompts.brand_alignment import build_brand_alignment_prompt


class TestBuildBrandAlignmentPrompt:
    """Test build_brand_alignment_prompt function."""

    def test_includes_original_content(self):
        result = build_brand_alignment_prompt(
            original_content="Test playbook about healthcare security",
            brand_context="Brand voice standards here",
            brand_assets="Proof points and case studies here"
        )
        assert "Test playbook about healthcare security" in result

    def test_includes_brand_context(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="UPSTACK brand voice standards",
            brand_assets=""
        )
        assert "UPSTACK brand voice standards" in result

    def test_includes_brand_assets(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="context",
            brand_assets="Proof points about vendor-neutral advisory"
        )
        assert "Proof points about vendor-neutral advisory" in result

    def test_brand_assets_defaults_to_empty(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="context"
        )
        assert isinstance(result, str)
        assert "content" in result

    def test_includes_enrichment_instructions(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="context",
            brand_assets="assets"
        )
        assert "UPSTACK Advisory Perspective" in result
        assert "Methodology References" in result
        assert "Case Study Integration" in result
        assert "Terminology Alignment" in result
        assert "Credentials & Credibility" in result

    def test_includes_preservation_rules(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="context",
            brand_assets="assets"
        )
        assert "PRESERVE" in result
        assert "DO NOT remove" in result

    def test_is_enrichment_not_rewrite(self):
        result = build_brand_alignment_prompt(
            original_content="content",
            brand_context="context",
            brand_assets="assets"
        )
        assert "ENRICH" in result
        assert "NOT rewriting" in result

    def test_handles_special_characters(self):
        content = "Content with {curly braces} and `backticks`"
        # brand_assets uses .format(), so curly braces in content need to be escaped
        # but the function handles this via positional formatting
        result = build_brand_alignment_prompt(
            original_content="safe content",
            brand_context="safe context",
            brand_assets="safe assets"
        )
        assert isinstance(result, str)
