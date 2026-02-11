"""Unit tests for BrandContextLoader.format_company_context()."""

import pytest
import yaml
from pathlib import Path

from research_orchestrator.utils.brand_context import BrandContextLoader


@pytest.fixture
def sample_baseline_data():
    """Return sample baseline data for testing."""
    return {
        "company": {
            "name": "TestCorp",
            "description": "Technology advisory services"
        },
        "tagline": "Expert advisory at no cost",
        "business_model": {
            "compensation": "vendor_reimbursed",
            "engagement_type": "ongoing_advisory",
            "description": "Advisory model funded by vendor commissions",
            "value_proposition": {
                "primary": "Optimize IT through expert advisory",
                "dimensions": ["Cost savings", "Risk reduction", "Speed"]
            },
            "trust_model": {
                "vendor_agnostic": "Recommend from all vendors",
                "transparency": "Disclose compensation upfront"
            },
            "differentiation": {
                "primary": "End-to-end lifecycle management"
            }
        },
        "competitive_landscape": {
            "primary_competition": "direct_vendor_sales",
            "secondary_competition": "other_technology_advisors"
        },
        "writing_standards": {
            "tone": "Professional but approachable"
        },
        "glossary": {
            "terms": {"TSD": "Technology Services Distributor"}
        }
    }


@pytest.fixture
def baseline_loader(sample_baseline_data, tmp_path):
    """Create a BrandContextLoader with test baseline data."""
    file_path = tmp_path / "baseline.yaml"
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_baseline_data, f, default_flow_style=False)
    return BrandContextLoader(
        config_dir=tmp_path,
        context_files={"baseline": "baseline.yaml"}
    )


class TestFormatCompanyContext:
    """Test BrandContextLoader.format_company_context() method."""

    def test_includes_company_name(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "TestCorp" in result

    def test_includes_business_model(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "Vendor Reimbursed" in result
        assert "Ongoing Advisory" in result

    def test_includes_value_proposition(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "Optimize IT through expert advisory" in result
        assert "Cost savings" in result

    def test_includes_trust_model(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "Vendor Agnostic" in result
        assert "Recommend from all vendors" in result

    def test_includes_differentiation(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "End-to-end lifecycle management" in result

    def test_includes_competitive_landscape(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "direct vendor sales" in result
        assert "other technology advisors" in result

    def test_excludes_writing_standards(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "Writing Standards" not in result
        assert "Professional but approachable" not in result

    def test_excludes_glossary(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert "Glossary" not in result
        assert "TSD" not in result

    def test_returns_empty_when_no_baseline(self, tmp_path):
        """Should return empty string when no baseline context loaded."""
        loader = BrandContextLoader(
            config_dir=tmp_path,
            context_files={"writing_standards": "nonexistent.yaml"}
        )
        ctx = loader.load_all()
        result = loader.format_company_context(ctx)
        assert result == ""

    def test_starts_with_company_context_header(self, baseline_loader):
        ctx = baseline_loader.load_all()
        result = baseline_loader.format_company_context(ctx)
        assert result.startswith("## Company Context")
