"""Unit tests for service category prompt building and context injection."""

import logging
from pathlib import Path

import pytest
import yaml

from research_orchestrator.prompts.context_injector import ResearchContextInjector
from research_orchestrator.prompts.service_category import build_service_category_prompt


def _write_baseline_yaml(tmp_path: Path, services: dict) -> Path:
    """Write a test baseline.yaml with given services dict."""
    baseline = {"company": {"services": services}}
    path = tmp_path / "baseline.yaml"
    path.write_text(yaml.dump(baseline, default_flow_style=False), encoding="utf-8")
    return path


SAMPLE_SERVICES = {
    "security": {
        "name": "Network Security",
        "subcategories": ["EDR", "MDR", "SIEM"],
        "key_suppliers": ["CrowdStrike  # EPP Leader", "Palo Alto Networks"],
        "market_notes": ["Wiz acquired by Google"],
    },
    "customer_experience": {
        "name": "Customer Experience (CX)",
        "subcategories": ["CCaaS", "UCaaS"],
        "key_suppliers": ["NICE", "Genesys", "CrowdStrike  # Also in security"],
        "market_notes": None,
    },
}


class TestResearchContextInjector:
    """Test ResearchContextInjector class."""

    def test_init_stores_path_and_logger(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        logger = logging.getLogger("test")
        injector = ResearchContextInjector(baseline_path=path, logger=logger)
        assert injector.baseline_path == path
        assert injector.logger is logger

    def test_load_categories_returns_dict(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        categories = injector.load_service_categories()
        assert isinstance(categories, dict)
        assert "security" in categories
        assert "customer_experience" in categories

    def test_load_categories_correct_structure(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        categories = injector.load_service_categories()
        security = categories["security"]
        assert security["name"] == "Network Security"
        assert security["subcategories"] == ["EDR", "MDR", "SIEM"]
        assert len(security["key_suppliers"]) == 2
        assert security["market_notes"] == ["Wiz acquired by Google"]

    def test_load_categories_caches_result(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result_1 = injector.load_service_categories()
        result_2 = injector.load_service_categories()
        assert result_1 is result_2
        assert "service_categories" in injector._cache

    def test_load_categories_file_not_found(self, tmp_path):
        injector = ResearchContextInjector(baseline_path=tmp_path / "nonexistent.yaml")
        with pytest.raises(FileNotFoundError):
            injector.load_service_categories()

    def test_load_categories_missing_company_key(self, tmp_path):
        path = tmp_path / "baseline.yaml"
        path.write_text(yaml.dump({"other": "data"}), encoding="utf-8")
        injector = ResearchContextInjector(baseline_path=path)
        with pytest.raises(KeyError, match="company"):
            injector.load_service_categories()

    def test_load_categories_missing_services_key(self, tmp_path):
        path = tmp_path / "baseline.yaml"
        path.write_text(yaml.dump({"company": {"name": "Test"}}), encoding="utf-8")
        injector = ResearchContextInjector(baseline_path=path)
        with pytest.raises(KeyError, match="company.services"):
            injector.load_service_categories()

    def test_get_category_returns_config(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        security = injector.get_service_category("security")
        assert security is not None
        assert security["name"] == "Network Security"

    def test_get_category_unknown_returns_none(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.get_service_category("nonexistent")
        assert result is None

    def test_format_category_includes_name(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_service_category_for_prompt("security")
        assert "## Service Category: Network Security" in result

    def test_format_category_strips_yaml_comments(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_service_category_for_prompt("security")
        assert "CrowdStrike" in result
        assert "# EPP Leader" not in result

    def test_format_category_includes_subcategories(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_service_category_for_prompt("security")
        assert "EDR" in result
        assert "MDR" in result

    def test_format_category_includes_market_notes(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_service_category_for_prompt("security")
        assert "Wiz acquired by Google" in result

    def test_get_all_supplier_names_deduplicates(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        suppliers = injector.get_all_supplier_names()
        # CrowdStrike appears in both categories but should be deduplicated
        assert suppliers.count("CrowdStrike") == 1

    def test_get_all_supplier_names_sorted(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        suppliers = injector.get_all_supplier_names()
        assert suppliers == sorted(suppliers)

    def test_get_all_supplier_names_strips_comments(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        suppliers = injector.get_all_supplier_names()
        for supplier in suppliers:
            assert "#" not in supplier

    def test_format_all_categories_has_header(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_all_categories_for_prompt()
        assert "# UPSTACK Service Categories" in result

    def test_format_all_categories_includes_all(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = injector.format_all_categories_for_prompt()
        assert "Network Security" in result
        assert "Customer Experience (CX)" in result


class TestBuildServiceCategoryPrompt:
    """Test build_service_category_prompt function."""

    def test_returns_nonempty_string(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_category_name(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert "Network Security" in result

    def test_includes_subcategories(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert "EDR" in result
        assert "MDR" in result
        assert "SIEM" in result

    def test_includes_suppliers(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert "CrowdStrike" in result
        assert "Palo Alto Networks" in result

    def test_strips_yaml_comments_from_suppliers(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert "CrowdStrike" in result
        assert "# EPP Leader" not in result

    def test_raises_valueerror_for_unknown_category(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        with pytest.raises(ValueError, match="Unknown service category"):
            build_service_category_prompt("nonexistent", injector)

    def test_error_message_lists_valid_options(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        with pytest.raises(ValueError, match="security"):
            build_service_category_prompt("nonexistent", injector)

    def test_includes_research_methodology(self, tmp_path):
        path = _write_baseline_yaml(tmp_path, SAMPLE_SERVICES)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("security", injector)
        assert "web_search" in result

    def test_handles_empty_subcategories(self, tmp_path):
        services = {
            "empty_sub": {
                "name": "Empty Subcats",
                "subcategories": [],
                "key_suppliers": ["Vendor A"],
                "market_notes": None,
            }
        }
        path = _write_baseline_yaml(tmp_path, services)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("empty_sub", injector)
        assert "None specified" in result

    def test_handles_empty_suppliers(self, tmp_path):
        services = {
            "empty_sup": {
                "name": "Empty Suppliers",
                "subcategories": ["Sub A"],
                "key_suppliers": [],
                "market_notes": None,
            }
        }
        path = _write_baseline_yaml(tmp_path, services)
        injector = ResearchContextInjector(baseline_path=path)
        result = build_service_category_prompt("empty_sup", injector)
        assert "None specified" in result
