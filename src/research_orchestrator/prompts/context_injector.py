"""Research context loader for service categories and baseline data."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .types import ServiceCategoryConfig, ServiceCategoriesDict


class ResearchContextInjector:
    """
    Loads and manages research context from baseline.yaml.

    Handles:
    - Service categories with subcategories and key suppliers
    - Market notes and intelligence
    - Dynamic extraction of supplier names across categories

    Follows BrandContextLoader pattern with caching and error handling.
    """

    def __init__(
        self,
        baseline_path: Path,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize research context injector.

        Args:
            baseline_path: Path to baseline.yaml file
            logger: Optional logger instance
        """
        self.baseline_path = Path(baseline_path)
        self.logger = logger or logging.getLogger(__name__)

        # Cache loaded context
        self._cache: Dict[str, Any] = {}

    def load_service_categories(self) -> ServiceCategoriesDict:
        """
        Load service categories from baseline.yaml.

        Returns:
            Dictionary mapping category keys to ServiceCategoryConfig objects.
            Example: {"security": {"name": "Network Security", ...}}

        Raises:
            FileNotFoundError: If baseline.yaml doesn't exist
            yaml.YAMLError: If YAML is malformed
            KeyError: If expected structure is missing
        """
        # Check cache first
        if 'service_categories' in self._cache:
            return self._cache['service_categories']

        if not self.baseline_path.exists():
            self.logger.warning(
                'Baseline file not found: %s',
                str(self.baseline_path)
            )
            raise FileNotFoundError(f"Baseline file not found: {self.baseline_path}")

        try:
            with open(self.baseline_path, 'r', encoding='utf-8') as f:
                baseline_data = yaml.safe_load(f)

            # Extract service categories from baseline structure
            # Expected path: company.services.<category_key>
            if 'company' not in baseline_data:
                raise KeyError("Missing 'company' key in baseline.yaml")

            if 'services' not in baseline_data['company']:
                raise KeyError("Missing 'company.services' key in baseline.yaml")

            raw_services = baseline_data['company']['services']

            # Transform to ServiceCategoriesDict structure
            service_categories: ServiceCategoriesDict = {}

            for category_key, category_data in raw_services.items():
                service_categories[category_key] = ServiceCategoryConfig(
                    name=category_data['name'],
                    subcategories=category_data.get('subcategories', []),
                    key_suppliers=category_data.get('key_suppliers', []),
                    market_notes=category_data.get('market_notes')
                )

            # Cache for future use
            self._cache['service_categories'] = service_categories

            self.logger.info(
                'Loaded %d service categories from %s',
                len(service_categories),
                str(self.baseline_path)
            )

            return service_categories

        except yaml.YAMLError as e:
            self.logger.error(
                'Failed to parse baseline YAML: %s - %s',
                str(self.baseline_path),
                str(e)
            )
            raise
        except Exception as e:
            self.logger.error(
                'Failed to load service categories: %s - %s',
                str(self.baseline_path),
                str(e)
            )
            raise

    def get_service_category(self, key: str) -> Optional[ServiceCategoryConfig]:
        """
        Get single service category by key.

        Args:
            key: Category key (e.g., 'security', 'customer_experience')

        Returns:
            ServiceCategoryConfig or None if not found
        """
        categories = self.load_service_categories()
        return categories.get(key)

    def format_service_category_for_prompt(self, category_key: str) -> str:
        """
        Format service category data for prompt injection.

        Args:
            category_key: Category key to format

        Returns:
            Formatted markdown string for prompt injection
        """
        category = self.get_service_category(category_key)

        if not category:
            self.logger.warning(
                'Service category not found: %s',
                category_key
            )
            return f"# Service Category: {category_key}\n\n*Category not found in baseline*"

        lines = [f"## Service Category: {category['name']}", ""]

        # Subcategories
        if category['subcategories']:
            lines.append("**Subcategories**:")
            for subcat in category['subcategories']:
                lines.append(f"- {subcat}")
            lines.append("")

        # Key suppliers
        if category['key_suppliers']:
            lines.append("**Key Suppliers**:")
            for supplier in category['key_suppliers']:
                # Suppliers may have inline comments in YAML - strip them
                supplier_clean = supplier.split('#')[0].strip()
                lines.append(f"- {supplier_clean}")
            lines.append("")

        # Market notes
        if category.get('market_notes'):
            lines.append("**Market Intelligence**:")
            for note in category['market_notes']:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)

    def get_all_supplier_names(self) -> List[str]:
        """
        Extract all key_suppliers across all categories.

        Useful for competitive research where you need a complete
        list of suppliers to analyze.

        Returns:
            Deduplicated list of supplier names sorted alphabetically.
            Inline YAML comments are stripped.
        """
        categories = self.load_service_categories()

        suppliers = set()
        for category_data in categories.values():
            for supplier in category_data.get('key_suppliers', []):
                # Strip inline YAML comments (e.g., "CrowdStrike  # EPP/EDR Leader")
                supplier_clean = supplier.split('#')[0].strip()
                if supplier_clean:
                    suppliers.add(supplier_clean)

        supplier_list = sorted(list(suppliers))

        self.logger.info(
            'Extracted %d unique supplier names',
            len(supplier_list)
        )

        return supplier_list

    def format_all_categories_for_prompt(self) -> str:
        """
        Format all service categories for prompt injection.

        Returns:
            Formatted markdown with all categories
        """
        categories = self.load_service_categories()

        sections = []
        for category_key in sorted(categories.keys()):
            section = self.format_service_category_for_prompt(category_key)
            sections.append(section)

        header = [
            "# UPSTACK Service Categories",
            "",
            "The following service categories represent UPSTACK's advisory focus areas.",
            "All suppliers and market intelligence are dynamically loaded from baseline.yaml.",
            ""
        ]

        return "\n".join(header) + "\n\n".join(sections)
