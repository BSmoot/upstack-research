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
        "decision_making": {
            "buying_process": "Committee-based evaluation",
            "key_stakeholders": ["CTO", "CISO", "VP of Infrastructure"],
            "budget_cycle": "Fiscal year starts July 1",
            "evaluation_triggers": ["M&A integration", "Digital transformation"],
            "confidence": "inferred",
            "sources": ["Earnings call Q3 2025", "LinkedIn"]
        },
        "whitespace": {
            "missing_capabilities": ["No unified observability", "No SD-WAN"],
            "underserved_areas": ["Network monitoring"],
            "expansion_signals": ["RFP for SD-WAN evaluation"],
            "confidence": "inferred",
            "sources": ["Job postings", "RFP database"]
        },
        "upcoming_needs": {
            "announced_projects": ["15-clinic integration"],
            "inferred_needs": ["Security stack consolidation"],
            "budget_indicators": ["Board-approved transformation budget"],
            "timeline_signals": ["18-month integration deadline"],
            "confidence": "inferred",
            "sources": ["Press release", "Earnings call"]
        },
        "internal_champions": [
            {
                "name": "Jane Smith",
                "title": "VP of Infrastructure",
                "relationship_status": "warm",
                "influence_level": "influencer",
                "notes": "Met at conference"
            }
        ],
        "north_star": {
            "strategic_initiatives": ["Digital-first patient experience"],
            "thought_leadership": ["CTO article on cloud migration"],
            "industry_positioning": ["Technology-forward health system"],
            "transformation_signals": ["Board-level digital mandate"],
            "confidence": "confirmed",
            "sources": ["Healthcare IT News", "HIMSS 2025"]
        },
        "research_metadata": {
            "researched_at": "2026-02-14T00:00:00Z",
            "agent_model": "test",
            "searches_performed": 35,
            "categories_researched": ["company_profile_stack", "north_star_signals"],
            "manual_sections": ["champion_goals", "internal_champions"]
        },
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


class TestFormatDecisionMaking:
    """Test _format_decision_making formatter."""

    def test_includes_buying_process(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Committee-based evaluation" in result

    def test_includes_stakeholders(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "CTO" in result
        assert "CISO" in result

    def test_includes_budget_cycle(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Fiscal year starts July 1" in result

    def test_includes_evaluation_triggers(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "M&A integration" in result

    def test_includes_confidence(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "inferred" in result

    def test_includes_decision_making_header(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## Decision Making" in result

    def test_empty_decision_making_returns_empty(self, loader):
        result = loader._format_decision_making({})
        # Empty dict should produce just the header with no content
        assert "## Decision Making" in result


class TestFormatWhitespace:
    """Test _format_whitespace formatter."""

    def test_includes_missing_capabilities(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "No unified observability" in result

    def test_includes_underserved_areas(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Network monitoring" in result

    def test_includes_expansion_signals(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "RFP for SD-WAN evaluation" in result

    def test_includes_whitespace_header(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## Whitespace & Portfolio Gaps" in result


class TestFormatUpcomingNeeds:
    """Test _format_upcoming_needs formatter."""

    def test_includes_announced_projects(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "15-clinic integration" in result

    def test_includes_inferred_needs(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Security stack consolidation" in result

    def test_includes_budget_indicators(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Board-approved transformation budget" in result

    def test_includes_timeline_signals(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "18-month integration deadline" in result

    def test_includes_upcoming_needs_header(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## Upcoming Needs & Projects" in result


class TestFormatNorthStar:
    """Test _format_north_star formatter."""

    def test_includes_strategic_initiatives(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Digital-first patient experience" in result

    def test_includes_thought_leadership(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "CTO article on cloud migration" in result

    def test_includes_industry_positioning(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Technology-forward health system" in result

    def test_includes_transformation_signals(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Board-level digital mandate" in result

    def test_includes_north_star_header(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## North-Star Signals & Thought Leadership" in result

    def test_includes_confirmed_confidence(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "confirmed" in result

    def test_includes_sources(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Healthcare IT News" in result


class TestFormatChampions:
    """Test _format_champions formatter."""

    def test_includes_champion_name(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "Jane Smith" in result

    def test_includes_champion_title(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "VP of Infrastructure" in result

    def test_includes_relationship_status(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "warm" in result

    def test_empty_champions_returns_empty(self, loader):
        """Champions with no name or title should produce empty string."""
        result = loader._format_champions([{"name": "", "title": ""}])
        assert result == ""

    def test_no_champions_returns_empty(self, loader):
        result = loader._format_champions([])
        assert result == ""


class TestFormatResearchMetadata:
    """Test _format_research_metadata formatter."""

    def test_includes_researched_at(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "2026-02-14" in result

    def test_includes_searches_performed(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "35" in result

    def test_includes_categories_researched(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "company_profile_stack" in result

    def test_includes_research_metadata_header(self, loader):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "## Research Metadata" in result


class TestStructuredSources:
    """Test structured source formatting with URLs."""

    def test_format_sources_with_url(self, loader):
        sources = [
            {"description": "Salesforce case study", "url": "https://salesforce.com/case", "date": "2025-07"}
        ]
        result = loader._format_sources_list(sources)
        assert len(result) == 1
        assert "[Salesforce case study](https://salesforce.com/case)" in result[0]
        assert "(2025-07)" in result[0]

    def test_format_sources_without_url(self, loader):
        sources = [
            {"description": "Earnings call Q3 2025", "url": "", "date": "2025-10"}
        ]
        result = loader._format_sources_list(sources)
        assert "Earnings call Q3 2025" in result[0]
        assert "[" not in result[0]  # No markdown link

    def test_format_sources_plain_string(self, loader):
        sources = ["LinkedIn executive profiles (2025)"]
        result = loader._format_sources_list(sources)
        assert "LinkedIn executive profiles (2025)" in result[0]

    def test_format_sources_mixed(self, loader):
        sources = [
            {"description": "Press release", "url": "https://example.com/pr", "date": "2025-12"},
            "Manual source note",
        ]
        result = loader._format_sources_list(sources)
        assert len(result) == 2
        assert "https://example.com/pr" in result[0]
        assert "Manual source note" in result[1]

    def test_pain_signal_with_source_url(self, tmp_path):
        import yaml
        data = {
            "pain_signals": [
                {
                    "signal": "Hiring CISO",
                    "source": "LinkedIn job posting",
                    "source_url": "https://linkedin.com/jobs/123",
                    "date": "2026-01",
                    "relevance": "Security expansion",
                    "confidence": "confirmed",
                }
            ]
        }
        file_path = tmp_path / "sourced.yaml"
        with open(file_path, "w") as f:
            yaml.dump(data, f)
        loader = TargetContextLoader(config_dir=tmp_path, file_path="sourced.yaml")
        result = loader.format_for_prompt(loader.load())
        assert "[LinkedIn job posting](https://linkedin.com/jobs/123)" in result
        assert "Confidence: confirmed" in result

    def test_recent_event_with_source_url(self, tmp_path):
        import yaml
        data = {
            "recent_events": [
                {
                    "event": "New CTO hired",
                    "date": "2025-10",
                    "source": "Press release",
                    "source_url": "https://example.com/press/cto",
                    "relevance": "Stack reassessment",
                }
            ]
        }
        file_path = tmp_path / "events.yaml"
        with open(file_path, "w") as f:
            yaml.dump(data, f)
        loader = TargetContextLoader(config_dir=tmp_path, file_path="events.yaml")
        result = loader.format_for_prompt(loader.load())
        assert "[Press release](https://example.com/press/cto)" in result

    def test_category_sources_render_urls(self, tmp_path):
        import yaml
        data = {
            "north_star": {
                "strategic_initiatives": ["Go digital"],
                "sources": [
                    {"description": "HIMSS keynote", "url": "https://himss.org/talk", "date": "2025"},
                    "Company blog post",
                ],
            }
        }
        file_path = tmp_path / "urls.yaml"
        with open(file_path, "w") as f:
            yaml.dump(data, f)
        loader = TargetContextLoader(config_dir=tmp_path, file_path="urls.yaml")
        result = loader.format_for_prompt(loader.load())
        assert "[HIMSS keynote](https://himss.org/talk)" in result
        assert "Company blog post" in result


class TestBackwardCompatibility:
    """Test that old YAML files without new sections still work."""

    def test_old_format_loads_and_formats(self, tmp_path):
        """YAML without new sections should format without errors."""
        old_data = {
            "company": {
                "name": "Old Corp",
                "slug": "old_corp",
                "industry": "Finance",
            },
            "known_stack": {"crm": "Salesforce"},
            "pain_signals": [],
            "compliance": ["SOX"],
            "recent_events": [],
            "engagement_history": ["Initial call completed"],
        }
        file_path = tmp_path / "old_format.yaml"
        import yaml
        with open(file_path, 'w') as f:
            yaml.dump(old_data, f)

        loader = TargetContextLoader(config_dir=tmp_path, file_path="old_format.yaml")
        data = loader.load()
        result = loader.format_for_prompt(data)

        assert "Old Corp" in result
        assert "Salesforce" in result
        assert "## Decision Making" not in result
        assert "## Whitespace" not in result
        assert "## Upcoming Needs" not in result
        assert "## North-Star" not in result

    def test_partial_new_sections(self, tmp_path):
        """YAML with some but not all new sections should work."""
        partial_data = {
            "company": {"name": "Partial Corp"},
            "north_star": {
                "strategic_initiatives": ["Go digital"],
                "confidence": "speculative",
            },
        }
        import yaml
        file_path = tmp_path / "partial.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(partial_data, f)

        loader = TargetContextLoader(config_dir=tmp_path, file_path="partial.yaml")
        data = loader.load()
        result = loader.format_for_prompt(data)

        assert "Partial Corp" in result
        assert "Go digital" in result
        assert "## Decision Making" not in result


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
