"""Unit tests for _merge_target_research logic in orchestrator."""

import pytest
import yaml
import logging
from pathlib import Path
from unittest.mock import MagicMock

from research_orchestrator.orchestrator import ResearchOrchestrator


class FakeOrchestrator:
    """Minimal stand-in with just the attributes _merge_target_research needs."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.logger = logging.getLogger("test_merge")

    # Bind the real method
    _merge_target_research = ResearchOrchestrator._merge_target_research


@pytest.fixture
def tmp_config(tmp_path):
    """Create a fake config file so config_path.parent resolves."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("dummy: true", encoding="utf-8")
    return config_file


@pytest.fixture
def orch(tmp_config):
    return FakeOrchestrator(config_path=tmp_config)


@pytest.fixture
def existing_target(tmp_path):
    """Write a pre-existing target YAML with manual sections."""
    data = {
        "company": {"name": "Old Name", "slug": "old"},
        "known_stack": {"ehr": "Cerner"},
        "champion_goals": [{"contact": "Alice", "role": "VP"}],
        "internal_champions": [{"name": "Bob", "title": "CTO"}],
        "engagement_history": ["Call completed 2026-01"],
        "notes": "Important manual notes",
    }
    target_file = tmp_path / "target.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)
    return target_file


# ---------------------------------------------------------------------------
# YAML extraction
# ---------------------------------------------------------------------------


class TestYamlExtraction:
    """Test YAML extraction from various deliverable formats."""

    def test_extracts_from_yaml_fenced_block(self, orch, tmp_path):
        target_file = tmp_path / "target.yaml"
        deliverables = (
            "Here are the results:\n\n"
            "```yaml\n"
            "company:\n"
            "  name: Acme\n"
            "known_stack:\n"
            "  ehr: Epic\n"
            "```\n\n"
            "End of results."
        )
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        assert target_file.exists()
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Acme"
        assert result["known_stack"]["ehr"] == "Epic"

    def test_extracts_from_yml_fenced_block(self, orch, tmp_path):
        deliverables = "```yml\ncompany:\n  name: Test\n```"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "target.yaml"
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Test"

    def test_handles_raw_yaml_without_fences(self, orch, tmp_path):
        deliverables = "company:\n  name: Raw Corp\nknown_stack:\n  crm: Salesforce\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "target.yaml"
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Raw Corp"

    def test_handles_empty_deliverables(self, orch, tmp_path):
        target_config = {"target_file": "target.yaml"}
        # Should log warning, not crash
        orch._merge_target_research("", target_config)
        assert not (tmp_path / "target.yaml").exists()

    def test_handles_none_deliverables(self, orch, tmp_path):
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(None, target_config)
        assert not (tmp_path / "target.yaml").exists()

    def test_handles_malformed_yaml(self, orch, tmp_path, existing_target):
        deliverables = "```yaml\n{{invalid: yaml: [}\n```"
        target_config = {"target_file": "target.yaml"}
        # Should warn, not crash, existing file untouched
        orch._merge_target_research(deliverables, target_config)
        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Old Name"

    def test_handles_non_dict_yaml(self, orch, tmp_path, existing_target):
        deliverables = "```yaml\n- just\n- a\n- list\n```"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)
        # Existing file should be untouched
        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Old Name"


# ---------------------------------------------------------------------------
# Merge behavior
# ---------------------------------------------------------------------------


class TestMergeBehavior:
    """Test that research data merges correctly with existing data."""

    def test_research_overwrites_agent_searchable_fields(self, orch, tmp_path, existing_target):
        deliverables = (
            "company:\n"
            "  name: Updated Name\n"
            "  slug: updated\n"
            "known_stack:\n"
            "  ehr: Epic\n"
            "  cloud:\n"
            "    - AWS\n"
        )
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Updated Name"
        assert result["known_stack"]["ehr"] == "Epic"  # Overwritten from Cerner

    def test_preserves_champion_goals(self, orch, tmp_path, existing_target):
        deliverables = "company:\n  name: New Name\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["champion_goals"][0]["contact"] == "Alice"

    def test_preserves_internal_champions(self, orch, tmp_path, existing_target):
        deliverables = "company:\n  name: New Name\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["internal_champions"][0]["name"] == "Bob"

    def test_preserves_engagement_history(self, orch, tmp_path, existing_target):
        deliverables = "company:\n  name: New Name\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert "Call completed 2026-01" in result["engagement_history"]

    def test_preserves_notes(self, orch, tmp_path, existing_target):
        deliverables = "company:\n  name: New Name\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert result["notes"] == "Important manual notes"

    def test_adds_new_sections(self, orch, tmp_path, existing_target):
        deliverables = (
            "company:\n  name: New Name\n"
            "whitespace:\n"
            "  missing_capabilities:\n"
            "    - No SD-WAN\n"
            "  confidence: inferred\n"
        )
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        result = yaml.safe_load(existing_target.read_text(encoding="utf-8"))
        assert "No SD-WAN" in result["whitespace"]["missing_capabilities"]

    def test_creates_target_file_if_missing(self, orch, tmp_path):
        deliverables = "company:\n  name: Brand New Target\n"
        target_config = {"target_file": "new_target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "new_target.yaml"
        assert target_file.exists()
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert result["company"]["name"] == "Brand New Target"

    def test_no_target_file_configured_skips(self, orch, tmp_path):
        deliverables = "company:\n  name: Test\n"
        target_config = {}
        # Should not crash
        orch._merge_target_research(deliverables, target_config)


# ---------------------------------------------------------------------------
# Research metadata
# ---------------------------------------------------------------------------


class TestResearchMetadata:
    """Test that research metadata is always added to merged output."""

    def test_adds_research_metadata(self, orch, tmp_path):
        deliverables = "company:\n  name: Test\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "target.yaml"
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert "research_metadata" in result
        assert "researched_at" in result["research_metadata"]
        assert "categories_researched" in result["research_metadata"]
        assert "manual_sections" in result["research_metadata"]

    def test_metadata_categories_are_correct(self, orch, tmp_path):
        deliverables = "company:\n  name: Test\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "target.yaml"
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        expected = [
            "company_profile_stack", "problems_decision_making",
            "whitespace_gaps", "upcoming_needs", "north_star_signals"
        ]
        assert result["research_metadata"]["categories_researched"] == expected

    def test_metadata_manual_sections_are_correct(self, orch, tmp_path):
        deliverables = "company:\n  name: Test\n"
        target_config = {"target_file": "target.yaml"}
        orch._merge_target_research(deliverables, target_config)

        target_file = tmp_path / "target.yaml"
        result = yaml.safe_load(target_file.read_text(encoding="utf-8"))
        assert result["research_metadata"]["manual_sections"] == [
            "champion_goals", "internal_champions"
        ]
