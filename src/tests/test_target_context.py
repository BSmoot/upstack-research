"""Unit tests for TargetContextLoader."""

import pytest
import yaml
from pathlib import Path

from research_orchestrator.utils.target_context import TargetContextLoader


@pytest.fixture
def sample_target_data():
    """Return sample target company data for testing."""
    return {
        "company": {
            "name": "Acme Health System",
            "slug": "acme_health",
            "industry": "Healthcare",
            "sub_industry": "Hospital & Health Systems",
            "size": "5,000-10,000 employees",
            "revenue": "$2B annual revenue",
            "headquarters": "Chicago, IL"
        },
        "known_stack": {
            "ehr": "Epic",
            "crm": "Salesforce Health Cloud",
            "cloud": ["AWS", "Azure"],
            "network": "Cisco Meraki",
            "security": ["CrowdStrike", "Palo Alto Networks"],
            "communications": "Microsoft Teams"
        },
        "pain_signals": [
            {
                "signal": "Hiring for CISO role",
                "source": "job posting",
                "date": "2026-01",
                "relevance": "Security team expansion"
            },
            {
                "signal": "Recent clinic network acquisition",
                "source": "press release",
                "date": "2025-12",
                "relevance": "Integration challenges"
            }
        ],
        "compliance": ["HIPAA", "HITRUST CSF", "SOC 2 Type II"],
        "recent_events": [
            {
                "event": "Acquired Regional Care Partners",
                "date": "2025-12",
                "relevance": "Network consolidation needed"
            },
            {
                "event": "New CTO appointed",
                "date": "2025-10",
                "relevance": "Technology reassessment likely"
            }
        ],
        "engagement_history": ["No prior UPSTACK engagement"],
        "metadata": {
            "updated": "2026-02-08",
            "source": "manual"
        }
    }


@pytest.fixture
def target_file(sample_target_data, tmp_path):
    """Create a temporary target context YAML file."""
    file_path = tmp_path / "acme_health.yaml"
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_target_data, f, default_flow_style=False)
    return file_path


@pytest.fixture
def loader(target_file, tmp_path):
    """Create a TargetContextLoader with test data."""
    return TargetContextLoader(
        config_dir=tmp_path,
        file_path="acme_health.yaml"
    )


class TestLoadTarget:
    """Test TargetContextLoader.load() method."""

    def test_load_target(self, loader, sample_target_data):
        result = loader.load()
        assert result is not None
        assert 'company' in result
        assert result['company']['name'] == "Acme Health System"

    def test_load_caches_result(self, loader):
        result1 = loader.load()
        result2 = loader.load()
        assert result1 is result2

    def test_load_with_matching_slug(self, loader):
        result = loader.load(target_slug="acme_health")
        assert result['company']['slug'] == "acme_health"

    def test_load_with_mismatched_slug_logs_warning(self, loader, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            loader.load(target_slug="wrong_slug")
        assert "mismatch" in caplog.text.lower()

    def test_missing_file_returns_empty_dict(self, tmp_path):
        loader = TargetContextLoader(
            config_dir=tmp_path,
            file_path="nonexistent.yaml"
        )
        result = loader.load()
        assert result == {}

    def test_invalid_yaml_raises(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{invalid: yaml: [}", encoding='utf-8')
        loader = TargetContextLoader(
            config_dir=tmp_path,
            file_path="bad.yaml"
        )
        with pytest.raises(yaml.YAMLError):
            loader.load()


class TestFormatForPrompt:
    """Test format_for_prompt output."""

    def test_includes_company_name(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Acme Health System" in result

    def test_includes_industry(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Healthcare" in result

    def test_includes_known_stack(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Epic" in result
        assert "CrowdStrike" in result

    def test_includes_pain_signals(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Hiring for CISO role" in result
        assert "Security team expansion" in result

    def test_includes_compliance(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "HIPAA" in result
        assert "HITRUST CSF" in result

    def test_includes_recent_events(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Acquired Regional Care Partners" in result
        assert "New CTO appointed" in result

    def test_includes_engagement_history(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "No prior UPSTACK engagement" in result

    def test_empty_context_returns_empty_string(self, loader):
        result = loader.format_for_prompt({})
        assert result == ""

    def test_format_produces_markdown_headers(self, loader, sample_target_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## Company Overview" in result
        assert "## Known Technology Stack" in result
        assert "## Observable Pain Signals" in result
        assert "## Compliance Requirements" in result
        assert "## Recent Events" in result


class TestMissingTargetFile:
    """Test graceful handling of missing target files."""

    def test_missing_file_load(self, tmp_path):
        loader = TargetContextLoader(
            config_dir=tmp_path,
            file_path="missing_target.yaml"
        )
        result = loader.load()
        assert result == {}

    def test_missing_file_format_returns_empty(self, tmp_path):
        loader = TargetContextLoader(
            config_dir=tmp_path,
            file_path="missing_target.yaml"
        )
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert result == ""
