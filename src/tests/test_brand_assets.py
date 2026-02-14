"""Unit tests for BrandAssetsLoader."""

import pytest
import tempfile
import yaml
from pathlib import Path

from research_orchestrator.utils.brand_assets import BrandAssetsLoader


@pytest.fixture
def sample_assets_data():
    """Return sample brand assets data for testing."""
    return {
        "methodology": {
            "name": "UPSTACK Advisory Framework",
            "tagline": "End-to-end technology advisory",
            "steps": ["Discovery", "Evaluation", "Procurement"],
            "description": "A comprehensive advisory framework."
        },
        "proof_points": {
            "general": [
                "Advisory at no cost to the buyer",
                "Access to 300+ suppliers"
            ],
            "by_service_category": {
                "security": [
                    {"point": "50+ security vendors evaluated", "use_when": "vendor selection"},
                    {"point": "Compliance-first methodology", "use_when": "compliance"}
                ],
                "network": [
                    {"point": "SD-WAN assessments across 100+ providers", "use_when": "network modernization"}
                ]
            },
            "by_vertical": {
                "healthcare": [
                    {"point": "HIPAA-compliant evaluation framework", "use_when": "healthcare compliance"},
                    {"point": "EHR integration experience", "use_when": "healthcare IT"}
                ],
                "financial_services": [
                    {"point": "SOX and PCI-DSS aligned criteria", "use_when": "financial compliance"}
                ]
            }
        },
        "case_studies": [
            {
                "id": "cs_healthcare_security_01",
                "headline": "Health System Security Consolidation",
                "vertical": "healthcare",
                "service_categories": ["security"],
                "situation": "Managing 8 security vendors",
                "approach": "Comprehensive security assessment",
                "outcome": "Consolidated to 3 platforms",
                "metrics": ["30% cost reduction"]
            },
            {
                "id": "cs_finserv_network_01",
                "headline": "Investment Firm Network Modernization",
                "vertical": "financial_services",
                "service_categories": ["network", "security"],
                "situation": "Supporting remote workforce",
                "approach": "SD-WAN and SASE evaluation",
                "outcome": "Deployed integrated solution",
                "metrics": ["40% latency improvement"]
            }
        ],
        "positioning_lines": {
            "vendor_neutral_intro": "UPSTACK serves as an objective technology advisor.",
            "trust_model_explanation": "Advisory at no cost to buyers.",
            "advisory_vs_broker": "Unlike brokers, UPSTACK provides end-to-end advisory.",
            "advisory_vs_consultant": "Unlike consultants, UPSTACK remains engaged.",
            "engagement_model": "Dedicated advisor from assessment through optimization."
        },
        "credentials": {
            "certifications": ["CISSP", "CCNP"],
            "partnerships": ["300+ technology vendors"],
            "by_vertical": {
                "healthcare": ["HIPAA compliance expertise"],
                "financial_services": ["SOX evaluation expertise"]
            }
        },
        "metadata": {
            "updated": "2026-02-08",
            "version": "1.0"
        }
    }


@pytest.fixture
def assets_file(sample_assets_data, tmp_path):
    """Create a temporary brand assets YAML file."""
    file_path = tmp_path / "brand-assets.yaml"
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_assets_data, f, default_flow_style=False)
    return file_path


@pytest.fixture
def loader(assets_file, tmp_path):
    """Create a BrandAssetsLoader with test data."""
    return BrandAssetsLoader(
        config_dir=tmp_path,
        file_path="brand-assets.yaml"
    )


class TestLoadAssets:
    """Test BrandAssetsLoader.load() method."""

    def test_load_assets(self, loader, sample_assets_data):
        result = loader.load()
        assert result is not None
        assert 'methodology' in result
        assert result['methodology']['name'] == sample_assets_data['methodology']['name']

    def test_load_caches_result(self, loader):
        result1 = loader.load()
        result2 = loader.load()
        assert result1 is result2

    def test_missing_file_returns_empty_dict(self, tmp_path):
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="nonexistent.yaml"
        )
        result = loader.load()
        assert result == {}

    def test_invalid_yaml_raises(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{invalid: yaml: [}", encoding='utf-8')
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="bad.yaml"
        )
        with pytest.raises(yaml.YAMLError):
            loader.load()


class TestFormatForPromptFiltering:
    """Test format_for_prompt filtering behavior."""

    def test_format_for_prompt_filters_by_vertical(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data, vertical="healthcare")

        # Should include healthcare proof points
        assert "HIPAA-compliant evaluation framework" in result
        assert "EHR integration experience" in result

        # Should NOT include financial_services proof points
        assert "SOX and PCI-DSS aligned criteria" not in result

    def test_format_for_prompt_filters_by_service_category(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data, service_category="security")

        # Should include security proof points
        assert "50+ security vendors evaluated" in result
        assert "Compliance-first methodology" in result

        # Should NOT include network-only proof points
        assert "SD-WAN assessments across 100+ providers" not in result

    def test_format_for_prompt_combined_filter(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(
            data, vertical="healthcare", service_category="security"
        )

        # Should include both healthcare and security points
        assert "HIPAA-compliant evaluation framework" in result
        assert "50+ security vendors evaluated" in result

        # Should include general proof points
        assert "Advisory at no cost to the buyer" in result

    def test_format_for_prompt_always_includes_methodology(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data, vertical="healthcare")
        assert "UPSTACK Advisory Framework" in result
        assert "Discovery" in result

    def test_format_for_prompt_always_includes_positioning(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert "objective technology advisor" in result

    def test_format_for_prompt_no_filter_includes_general_only(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data)

        # General proof points should be present
        assert "Advisory at no cost to the buyer" in result
        assert "300+ suppliers" in result

    def test_format_for_prompt_filters_credentials_by_vertical(self, loader, sample_assets_data):
        data = loader.load()
        result = loader.format_for_prompt(data, vertical="healthcare")

        # Should include healthcare-specific credentials
        assert "HIPAA compliance expertise" in result

        # Should NOT include financial_services credentials
        assert "SOX evaluation expertise" not in result


class TestGetCaseStudies:
    """Test case study filtering."""

    def test_get_all_case_studies(self, loader):
        loader.load()
        studies = loader.get_case_studies()
        assert len(studies) == 2

    def test_get_case_studies_by_vertical(self, loader):
        loader.load()
        studies = loader.get_case_studies(vertical="healthcare")
        assert len(studies) == 1
        assert studies[0]['id'] == "cs_healthcare_security_01"

    def test_get_case_studies_by_service_category(self, loader):
        loader.load()
        studies = loader.get_case_studies(service_category="security")
        assert len(studies) == 2  # Both studies include security

    def test_get_case_studies_combined_filter(self, loader):
        loader.load()
        studies = loader.get_case_studies(
            vertical="financial_services", service_category="network"
        )
        assert len(studies) == 1
        assert studies[0]['id'] == "cs_finserv_network_01"

    def test_get_case_studies_no_match(self, loader):
        loader.load()
        studies = loader.get_case_studies(vertical="nonexistent")
        assert len(studies) == 0

    def test_get_case_studies_empty_assets(self, tmp_path):
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("{}", encoding='utf-8')
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="empty.yaml")
        studies = loader.get_case_studies()
        assert studies == []


class TestGetProofPoints:
    """Test proof point filtering."""

    def test_general_points_always_included(self, loader):
        loader.load()
        points = loader.get_proof_points()
        assert "Advisory at no cost to the buyer" in points
        assert "Access to 300+ suppliers" in points

    def test_service_category_points_added(self, loader):
        loader.load()
        points = loader.get_proof_points(service_category="security")
        assert "50+ security vendors evaluated" in points
        assert len(points) > 2  # General + security

    def test_vertical_points_added(self, loader):
        loader.load()
        points = loader.get_proof_points(vertical="healthcare")
        assert "HIPAA-compliant evaluation framework" in points

    def test_combined_filter(self, loader):
        loader.load()
        points = loader.get_proof_points(
            service_category="security", vertical="healthcare"
        )
        assert "50+ security vendors evaluated" in points
        assert "HIPAA-compliant evaluation framework" in points
        assert "Advisory at no cost to the buyer" in points


class TestFormatCompactProofPoints:
    """Test BrandAssetsLoader.format_compact_proof_points() method."""

    @pytest.fixture
    def verified_assets_data(self):
        """Return brand assets with status-tagged proof points."""
        return {
            "methodology": {
                "name": "Advisory Framework",
                "steps": ["Step 1", "Step 2"],
            },
            "proof_points": {
                "general": [
                    {"point": "Verified general point", "status": "✅ VERIFIED"},
                    {"point": "Caution general point", "status": "⚠️ CAUTION — small sample size"},
                    {"point": "Gap point", "status": "🔲 GAP"},
                    {"point": "Another verified point", "status": "✅ VERIFIED — details"},
                ],
                "by_service_category": {
                    "security": [
                        {"point": "Verified security point", "status": "✅ VERIFIED"},
                        {"point": "Unverified security point", "status": "⚠️ CAUTION — limited data"},
                    ]
                },
                "by_vertical": {
                    "healthcare": [
                        {"point": "Verified healthcare point", "status": "✅ VERIFIED"},
                    ]
                },
            },
            "positioning_lines": {
                "engagement_model": "Dedicated advisor from start to finish.",
                "trust_model_explanation": "No cost to buyers.",
                "vendor_neutral_intro": "Objective advisory.",
            },
        }

    @pytest.fixture
    def verified_loader(self, verified_assets_data, tmp_path):
        """Create a loader with verified assets data."""
        file_path = tmp_path / "verified-assets.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(verified_assets_data, f, default_flow_style=False)
        return BrandAssetsLoader(config_dir=tmp_path, file_path="verified-assets.yaml")

    def test_filters_to_verified_only(self, verified_loader):
        """Only VERIFIED proof points in the verified section, CAUTION separate."""
        result = verified_loader.format_compact_proof_points()
        assert "Verified general point" in result
        assert "Another verified point" in result
        # CAUTION items should NOT appear in the verified bullet list
        assert "- Caution general point\n" not in result
        assert "Gap point" not in result

    def test_caution_section_appears_separately(self, verified_loader):
        """CAUTION items should appear in a separate warning section."""
        result = verified_loader.format_compact_proof_points()
        assert "## CAUTION" in result
        assert "Do Not Use Without Qualification" in result
        assert "REQUIRED QUALIFIER:" in result
        assert "Caution general point" in result

    def test_respects_max_points(self, verified_loader):
        """Should limit to max_points."""
        result = verified_loader.format_compact_proof_points(max_points=1)
        assert "Verified general point" in result
        # Only 1 point allowed, so "Another verified" should not appear
        assert "Another verified point" not in result

    def test_filters_by_service_category(self, verified_loader):
        """Should include service-category-specific verified points."""
        result = verified_loader.format_compact_proof_points(service_category="security")
        assert "Verified security point" in result
        # CAUTION items appear in the CAUTION section, not the verified section
        verified_section = result.split("## CAUTION")[0]
        assert "Unverified security point" not in verified_section
        # But they DO appear in the CAUTION section
        assert "Unverified security point" in result

    def test_filters_by_vertical(self, verified_loader):
        """Should include vertical-specific verified points."""
        result = verified_loader.format_compact_proof_points(vertical="healthcare")
        assert "Verified healthcare point" in result

    def test_includes_positioning_lines(self, verified_loader):
        """Should include engagement model and trust model positioning."""
        result = verified_loader.format_compact_proof_points()
        assert "Engagement Model" in result
        assert "Trust Model" in result
        assert "Dedicated advisor" in result

    def test_excludes_vendor_neutral_intro(self, verified_loader):
        """Should NOT include vendor_neutral_intro (only engagement + trust)."""
        result = verified_loader.format_compact_proof_points()
        assert "Objective advisory" not in result

    def test_returns_empty_when_no_verified_points(self, tmp_path):
        """Should return empty string when no VERIFIED points exist."""
        data = {
            "proof_points": {
                "general": [
                    {"point": "Unverified only", "status": "⚠️ CAUTION"},
                ]
            }
        }
        file_path = tmp_path / "no-verified.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="no-verified.yaml")
        result = loader.format_compact_proof_points()
        assert result == ""

    def test_returns_empty_for_missing_file(self, tmp_path):
        """Should return empty string when file doesn't exist."""
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="nonexistent.yaml")
        result = loader.format_compact_proof_points()
        assert result == ""


class TestMissingFileHandling:
    """Test graceful degradation when files are missing."""

    def test_missing_file_load_returns_empty(self, tmp_path):
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="does_not_exist.yaml"
        )
        result = loader.load()
        assert result == {}

    def test_missing_file_format_for_prompt_returns_empty(self, tmp_path):
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="does_not_exist.yaml"
        )
        data = loader.load()
        result = loader.format_for_prompt(data)
        assert result == ""

    def test_missing_file_get_case_studies_returns_empty(self, tmp_path):
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="does_not_exist.yaml"
        )
        studies = loader.get_case_studies()
        assert studies == []

    def test_missing_file_get_proof_points_returns_empty(self, tmp_path):
        loader = BrandAssetsLoader(
            config_dir=tmp_path,
            file_path="does_not_exist.yaml"
        )
        points = loader.get_proof_points()
        assert points == []


class TestFormatProofPointAudit:
    """Test BrandAssetsLoader.format_proof_point_audit() method."""

    @pytest.fixture
    def audit_assets_data(self):
        """Return brand assets with mixed-status proof points, case studies, and unverified claims."""
        return {
            "proof_points": {
                "general": [
                    {"point": "99.8% retention rate", "status": "✅ VERIFIED"},
                    {"point": "76-day implementation", "status": "⚠️ CAUTION — based on 2% of projects"},
                    {"point": "Gap metric", "status": "🔲 GAP"},
                ],
                "by_service_category": {
                    "security": [
                        {"point": "Verified security stat", "status": "✅ VERIFIED"},
                        {"point": "35% cost reduction", "status": "⚠️ CAUTION — weighted average across categories"},
                    ]
                },
                "by_vertical": {
                    "healthcare": [
                        {"point": "Healthcare verified point", "status": "✅ VERIFIED"},
                    ]
                },
            },
            "case_studies": [
                {
                    "id": "cs_001",
                    "headline": "Test Case Study",
                    "vertical": "healthcare",
                    "service_categories": ["security"],
                    "metrics": ["$45K savings", "6-week deployment"],
                },
            ],
            "unverified_claims": [
                {"id": "UV-001", "claim": "40+ financial institutions", "status": "UNVERIFIED"},
                {"id": "UV-002", "claim": "200+ years combined experience", "status": "UNVERIFIED"},
            ],
        }

    @pytest.fixture
    def audit_loader(self, audit_assets_data, tmp_path):
        """Create a loader with audit test data."""
        file_path = tmp_path / "audit-assets.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(audit_assets_data, f, default_flow_style=False)
        return BrandAssetsLoader(config_dir=tmp_path, file_path="audit-assets.yaml")

    def test_verified_section_present(self, audit_loader):
        """Audit should include a VERIFIED CLAIMS section."""
        result = audit_loader.format_proof_point_audit()
        assert "### VERIFIED CLAIMS" in result
        assert "[VERIFIED] 99.8% retention rate" in result

    def test_caution_section_with_qualifiers(self, audit_loader):
        """Audit should include CAUTION claims with their qualifier text."""
        result = audit_loader.format_proof_point_audit()
        assert "### CAUTION CLAIMS" in result
        assert "[CAUTION] 76-day implementation" in result
        assert "QUALIFIER:" in result
        assert "2% of projects" in result

    def test_unverified_section_present(self, audit_loader):
        """Audit should include UNVERIFIED CLAIMS section."""
        result = audit_loader.format_proof_point_audit()
        assert "### UNVERIFIED CLAIMS" in result
        assert "[UNVERIFIED] 40+ financial institutions" in result
        assert "[UNVERIFIED] 200+ years combined experience" in result

    def test_case_study_metrics_present(self, audit_loader):
        """Audit should include case study metrics when filtered."""
        result = audit_loader.format_proof_point_audit(
            vertical="healthcare", service_category="security"
        )
        assert "### VERIFIED CASE STUDY METRICS" in result
        assert "Test Case Study" in result
        assert "$45K savings" in result

    def test_critical_instruction_present(self, audit_loader):
        """Audit should include the critical fabrication warning."""
        result = audit_loader.format_proof_point_audit()
        assert "### CRITICAL INSTRUCTION" in result
        assert "FABRICATED" in result

    def test_filters_by_service_category(self, audit_loader):
        """Should include category-specific points when filtered."""
        result = audit_loader.format_proof_point_audit(service_category="security")
        assert "Verified security stat" in result
        assert "35% cost reduction" in result

    def test_filters_by_vertical(self, audit_loader):
        """Should include vertical-specific points when filtered."""
        result = audit_loader.format_proof_point_audit(vertical="healthcare")
        assert "Healthcare verified point" in result

    def test_returns_empty_for_missing_file(self, tmp_path):
        """Should return empty string when file doesn't exist."""
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="nonexistent.yaml")
        result = loader.format_proof_point_audit()
        assert result == ""

    def test_returns_empty_for_empty_file(self, tmp_path):
        """Should return empty string when assets are empty."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("{}", encoding='utf-8')
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="empty.yaml")
        result = loader.format_proof_point_audit()
        assert result == ""


class TestCautionInFormatForPrompt:
    """Test that format_for_prompt includes CAUTION warnings."""

    @pytest.fixture
    def caution_assets_data(self):
        """Return brand assets with CAUTION-flagged proof points."""
        return {
            "proof_points": {
                "general": [
                    {"point": "Verified point", "status": "✅ VERIFIED"},
                    {"point": "Caution point", "status": "⚠️ CAUTION — small sample size"},
                ],
            },
        }

    @pytest.fixture
    def caution_loader(self, caution_assets_data, tmp_path):
        file_path = tmp_path / "caution-assets.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(caution_assets_data, f, default_flow_style=False)
        return BrandAssetsLoader(config_dir=tmp_path, file_path="caution-assets.yaml")

    def test_format_for_prompt_includes_caution_section(self, caution_loader):
        """format_for_prompt should include CAUTION warning section."""
        data = caution_loader.load()
        result = caution_loader.format_for_prompt(data)
        assert "CAUTION" in result
        assert "Do Not Use Without Qualification" in result
        assert "Caution point" in result
        assert "REQUIRED QUALIFIER:" in result

    def test_format_for_prompt_no_caution_when_none_exist(self, tmp_path):
        """format_for_prompt should not include CAUTION section when no CAUTION items."""
        data = {
            "proof_points": {
                "general": [
                    {"point": "Only verified", "status": "✅ VERIFIED"},
                ],
            },
        }
        file_path = tmp_path / "no-caution.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
        loader = BrandAssetsLoader(config_dir=tmp_path, file_path="no-caution.yaml")
        result = loader.format_for_prompt(loader.load())
        assert "Do Not Use Without Qualification" not in result
