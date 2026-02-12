"""Brand assets loader for brand enrichment."""

import yaml
import logging
from pathlib import Path
from typing import Any, Optional


class BrandAssetsLoader:
    """
    Loads and manages brand assets for enrichment.

    Handles:
    - Methodology descriptions and steps
    - Proof points (general, by service category, by vertical)
    - Case studies (filterable by vertical and service category)
    - Positioning lines
    - Credentials and certifications
    """

    def __init__(
        self,
        config_dir: Path,
        file_path: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize brand assets loader.

        Args:
            config_dir: Directory where project config resides (for relative paths)
            file_path: Path to brand assets YAML file (relative to config_dir)
            logger: Optional logger instance
        """
        self.config_dir = Path(config_dir)
        self.file_path = file_path
        self.logger = logger or logging.getLogger(__name__)

        # Cache loaded assets
        self._cache: Optional[dict[str, Any]] = None

    def load(self) -> dict[str, Any]:
        """
        Load brand assets from YAML file.

        Returns:
            Dictionary with all brand assets data

        Raises:
            yaml.YAMLError: If YAML parsing fails
        """
        if self._cache is not None:
            return self._cache

        full_path = self.config_dir / self.file_path

        if not full_path.exists():
            self.logger.warning(f"Brand assets file not found: {full_path}")
            return {}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                documents = list(yaml.safe_load_all(f))

            # Merge all YAML documents into a single dict
            merged: dict[str, Any] = {}
            for doc in documents:
                if isinstance(doc, dict):
                    merged.update(doc)

            self._cache = merged
            self.logger.info(f"Loaded brand assets from {full_path}")
            return self._cache

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse brand assets YAML from {full_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load brand assets from {full_path}: {e}")
            raise

    def get_case_studies(
        self,
        vertical: Optional[str] = None,
        service_category: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get case studies filtered by vertical and/or service category.

        Args:
            vertical: Optional vertical to filter by (e.g., 'healthcare')
            service_category: Optional service category to filter by (e.g., 'security')

        Returns:
            List of matching case study dictionaries
        """
        assets = self.load()
        case_studies = assets.get('case_studies', [])

        if not case_studies:
            return []

        filtered = []
        for study in case_studies:
            if not isinstance(study, dict):
                continue

            matches_vertical = (
                vertical is None
                or study.get('vertical', '').lower() == vertical.lower()
            )
            matches_category = (
                service_category is None
                or service_category.lower() in [
                    sc.lower() for sc in study.get('service_categories', [])
                ]
            )

            if matches_vertical and matches_category:
                filtered.append(study)

        return filtered

    def get_proof_points(
        self,
        service_category: Optional[str] = None,
        vertical: Optional[str] = None
    ) -> list[str]:
        """
        Get proof points filtered by service category and/or vertical.

        Always includes general proof points. Adds category/vertical-specific
        points when filters match.

        Args:
            service_category: Optional service category to filter by
            vertical: Optional vertical to filter by

        Returns:
            List of proof point strings
        """
        assets = self.load()
        proof_points_data = assets.get('proof_points', {})

        # Always include general proof points
        points = list(proof_points_data.get('general', []))

        # Add service category proof points
        if service_category:
            by_category = proof_points_data.get('by_service_category', {})
            category_points = by_category.get(service_category, [])
            for item in category_points:
                if isinstance(item, dict):
                    points.append(item.get('point', ''))
                elif isinstance(item, str):
                    points.append(item)

        # Add vertical proof points
        if vertical:
            by_vertical = proof_points_data.get('by_vertical', {})
            vertical_points = by_vertical.get(vertical, [])
            for item in vertical_points:
                if isinstance(item, dict):
                    points.append(item.get('point', ''))
                elif isinstance(item, str):
                    points.append(item)

        return [p for p in points if p]

    def format_compact_proof_points(
        self,
        vertical: Optional[str] = None,
        service_category: Optional[str] = None,
        max_points: int = 8
    ) -> str:
        """
        Format a compact set of VERIFIED proof points and positioning lines.

        Filters proof points to only those with status containing 'VERIFIED',
        limits output to max_points, and appends key positioning lines.
        Does NOT include full case studies, credentials, or methodology steps.

        Args:
            vertical: Optional vertical for filtering
            service_category: Optional service category for filtering
            max_points: Maximum number of proof points to include (default 8)

        Returns:
            Compact formatted string for prompt injection
        """
        assets = self.load()
        if not assets:
            return ""

        lines = ["## Verified Proof Points", ""]

        # Collect all candidate proof points (dicts with point + status)
        candidates: list[dict[str, Any]] = []
        proof_points_data = assets.get('proof_points', {})

        # General proof points
        for item in proof_points_data.get('general', []):
            if isinstance(item, dict):
                candidates.append(item)

        # Service-category-specific proof points
        if service_category:
            by_cat = proof_points_data.get('by_service_category', {})
            for item in by_cat.get(service_category, []):
                if isinstance(item, dict):
                    candidates.append(item)

        # Vertical-specific proof points
        if vertical:
            by_vert = proof_points_data.get('by_vertical', {})
            for item in by_vert.get(vertical, []):
                if isinstance(item, dict):
                    candidates.append(item)

        # Filter to VERIFIED only
        verified = [
            c for c in candidates
            if 'VERIFIED' in str(c.get('status', ''))
        ]

        # Limit to max_points
        for item in verified[:max_points]:
            point_text = item.get('point', '')
            if point_text:
                lines.append(f"- {point_text}")

        if len(lines) <= 2:
            # No verified points found
            return ""

        # Add positioning lines (compact)
        positioning = assets.get('positioning_lines', {})
        if positioning:
            lines.append("")
            lines.append("## Key Positioning")
            label_map = {
                'engagement_model': 'Engagement Model',
                'trust_model_explanation': 'Trust Model',
            }
            for key, label in label_map.items():
                value = positioning.get(key, '')
                if value:
                    lines.append(f"**{label}:** {value.strip()}")

        return "\n".join(lines)

    def get_language_standards(self) -> dict[str, Any]:
        """
        Get language standards from brand assets.

        Returns:
            Dictionary with required_terms, prohibited_terms, and positioning_guidance.
            Empty dict if no language standards defined.
        """
        assets = self.load()
        return assets.get('language_standards', {})

    def get_unverified_claims(self) -> list[dict[str, Any]]:
        """
        Get list of unverified claims that must not appear in outputs.

        Returns:
            List of unverified claim dictionaries with id, claim, status.
        """
        assets = self.load()
        return assets.get('unverified_claims', [])

    def get_buyer_intelligence(self) -> dict[str, Any]:
        """
        Get buyer intelligence data points.

        Returns:
            Dictionary with buying_committee, ai_procurement_adoption,
            customer_expansion, and market_drivers sections.
        """
        assets = self.load()
        return assets.get('buyer_intelligence', {})

    def get_vertical_intelligence(
        self,
        vertical: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get vertical intelligence data filtered by vertical.

        Args:
            vertical: Vertical key (e.g., 'financial_services')

        Returns:
            Vertical-specific intelligence dict, or all verticals if no filter.
        """
        assets = self.load()
        all_verticals = assets.get('vertical_intelligence', {})
        if vertical and vertical in all_verticals:
            return {vertical: all_verticals[vertical]}
        return all_verticals

    def format_for_prompt(
        self,
        context: dict[str, Any],
        vertical: Optional[str] = None,
        service_category: Optional[str] = None,
        title_cluster: Optional[str] = None
    ) -> str:
        """
        Format relevant brand assets for inclusion in enrichment prompt.

        Produces a filtered, focused subset of assets based on the playbook's
        vertical, service category, and title cluster. Does NOT dump the entire
        assets file.

        Args:
            context: Full brand assets dictionary (from load())
            vertical: Optional vertical for filtering
            service_category: Optional service category for filtering
            title_cluster: Optional title cluster for filtering

        Returns:
            Formatted string for prompt injection
        """
        sections = []

        # Language standards (always included — highest priority)
        language_standards = context.get('language_standards', {})
        if language_standards:
            sections.append(self._format_language_standards(language_standards))

        # Methodology (always included)
        methodology = context.get('methodology', {})
        if methodology:
            sections.append(self._format_methodology(methodology))

        # Filtered proof points
        proof_points = self.get_proof_points(
            service_category=service_category,
            vertical=vertical
        )
        if proof_points:
            sections.append(self._format_proof_points(proof_points))

        # Filtered case studies
        case_studies = self.get_case_studies(
            vertical=vertical,
            service_category=service_category
        )
        if case_studies:
            sections.append(self._format_case_studies(case_studies))

        # Positioning lines (always included)
        positioning = context.get('positioning_lines', {})
        if positioning:
            sections.append(self._format_positioning(positioning))

        # Filtered credentials
        credentials = context.get('credentials', {})
        if credentials:
            sections.append(self._format_credentials(credentials, vertical=vertical))

        # Buyer intelligence (always included)
        buyer_intel = context.get('buyer_intelligence', {})
        if buyer_intel:
            sections.append(self._format_buyer_intelligence(buyer_intel))

        # Vertical intelligence (filtered)
        vertical_intel = context.get('vertical_intelligence', {})
        if vertical and vertical in vertical_intel:
            sections.append(
                self._format_vertical_intelligence(vertical, vertical_intel[vertical])
            )

        # Unverified claims (always included as warning)
        unverified = context.get('unverified_claims', [])
        if unverified:
            sections.append(self._format_unverified_claims(unverified))

        # Filter out empty sections
        sections = [s for s in sections if s and s.strip()]

        return "\n\n".join(sections)

    def _format_methodology(self, methodology: dict[str, Any]) -> str:
        """Format methodology section."""
        lines = ["## UPSTACK Methodology", ""]

        name = methodology.get('name', '')
        if name:
            lines.append(f"**{name}**")

        tagline = methodology.get('tagline', '')
        if tagline:
            lines.append(f"*{tagline}*")

        description = methodology.get('description', '')
        if description:
            lines.append(f"\n{description.strip()}")

        steps = methodology.get('steps', [])
        if steps:
            lines.append("\n**Process Steps:**")
            for i, step in enumerate(steps, 1):
                lines.append(f"{i}. {step}")

        return "\n".join(lines)

    def _format_proof_points(self, proof_points: list[str]) -> str:
        """Format proof points section."""
        lines = ["## Proof Points", ""]
        for point in proof_points:
            lines.append(f"- {point}")
        return "\n".join(lines)

    def _format_case_studies(self, case_studies: list[dict[str, Any]]) -> str:
        """Format case studies section."""
        lines = ["## Relevant Case Studies", ""]

        for study in case_studies:
            headline = study.get('headline', 'Case Study')
            lines.append(f"### {headline}")

            situation = study.get('situation', '')
            if situation:
                lines.append(f"**Situation:** {situation.strip()}")

            approach = study.get('approach', '')
            if approach:
                lines.append(f"**Approach:** {approach.strip()}")

            outcome = study.get('outcome', '')
            if outcome:
                lines.append(f"**Outcome:** {outcome.strip()}")

            metrics = study.get('metrics', [])
            if metrics:
                lines.append("**Key Metrics:**")
                for metric in metrics:
                    lines.append(f"- {metric}")

            lines.append("")

        return "\n".join(lines)

    def _format_positioning(self, positioning: dict[str, str]) -> str:
        """Format positioning lines section."""
        lines = ["## Positioning Lines", ""]

        label_map = {
            'vendor_neutral_intro': 'Vendor-Neutral Introduction',
            'trust_model_explanation': 'Trust Model Explanation',
            'advisory_vs_broker': 'Advisory vs. Broker',
            'advisory_vs_consultant': 'Advisory vs. Consultant',
            'engagement_model': 'Engagement Model',
        }

        for key, label in label_map.items():
            value = positioning.get(key, '')
            if value:
                lines.append(f"**{label}:** {value.strip()}")
                lines.append("")

        return "\n".join(lines)

    def _format_credentials(
        self,
        credentials: dict[str, Any],
        vertical: Optional[str] = None
    ) -> str:
        """Format credentials section, filtered by vertical."""
        lines = ["## Credentials & Partnerships", ""]

        # General certifications
        certs = credentials.get('certifications', [])
        if certs:
            lines.append("**Certifications:**")
            for cert in certs:
                lines.append(f"- {cert}")
            lines.append("")

        # Partnerships
        partnerships = credentials.get('partnerships', [])
        if partnerships:
            lines.append("**Partnerships:**")
            for partner in partnerships:
                lines.append(f"- {partner}")
            lines.append("")

        # Vertical-specific credentials
        if vertical:
            by_vertical = credentials.get('by_vertical', {})
            vertical_creds = by_vertical.get(vertical, [])
            if vertical_creds:
                vertical_label = vertical.replace('_', ' ').title()
                lines.append(f"**{vertical_label}-Specific Credentials:**")
                for cred in vertical_creds:
                    lines.append(f"- {cred}")
                lines.append("")

        return "\n".join(lines)

    def _format_language_standards(self, standards: dict[str, Any]) -> str:
        """Format language standards for prompt injection."""
        lines = ["## LANGUAGE STANDARDS (MANDATORY)", ""]

        # Required terms
        required = standards.get('required_terms', {})
        if required:
            lines.append("**Required Terminology:**")
            if 'company_descriptor' in required:
                lines.append(f"- Company descriptor: \"{required['company_descriptor']}\"")
            if 'cost_model' in required:
                lines.append(f"- Cost language: \"{required['cost_model']}\"")
            if 'funding_model' in required:
                lines.append(f"- Funding model: \"{required['funding_model']}\"")
            if 'revenue_model' in required:
                lines.append(f"- Revenue model: \"{required['revenue_model']}\"")
            if 'revenue_model_note' in required:
                lines.append(f"  Note: {required['revenue_model_note'].strip()}")
            lines.append("")

        # Prohibited terms
        prohibited = standards.get('prohibited_terms', [])
        if prohibited:
            lines.append("**Prohibited Terms (flag and replace):**")
            for item in prohibited:
                if isinstance(item, dict):
                    term = item.get('term', '')
                    replacement = item.get('use_instead', 'N/A')
                    reason = item.get('reason', '')
                    if replacement:
                        lines.append(f"- NEVER use \"{term}\" → use \"{replacement}\" ({reason})")
                    else:
                        lines.append(f"- NEVER use \"{term}\" ({reason})")
            lines.append("")

        # Positioning guidance
        guidance = standards.get('positioning_guidance', {})
        if guidance:
            lines.append("**Positioning Guidance:**")
            if 'category_first' in guidance:
                lines.append(f"- Category-first approach: {guidance['category_first'].strip()}")
            if 'cost_language' in guidance:
                lines.append(f"- Cost messaging: {guidance['cost_language'].strip()}")

        return "\n".join(lines)

    def _format_buyer_intelligence(self, buyer_intel: dict[str, Any]) -> str:
        """Format buyer intelligence data points for prompt injection."""
        lines = ["## Buyer Intelligence (Citable Data)", ""]

        section_labels = {
            'buying_committee': 'Buying Committee',
            'ai_procurement_adoption': 'AI in Procurement',
            'customer_expansion': 'Customer Expansion',
            'market_drivers': 'Market Drivers',
        }

        for section_key, label in section_labels.items():
            items = buyer_intel.get(section_key, [])
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    if isinstance(item, dict):
                        point = item.get('point', '')
                        source = item.get('source', '')
                        if point:
                            lines.append(f"- {point} (Source: {source})")
                lines.append("")

        return "\n".join(lines)

    def _format_vertical_intelligence(
        self,
        vertical: str,
        intel: dict[str, Any]
    ) -> str:
        """Format vertical-specific intelligence for prompt injection."""
        vertical_label = vertical.replace('_', ' ').title()
        lines = [f"## {vertical_label} Vertical Intelligence", ""]

        # Regulatory frameworks
        frameworks = intel.get('regulatory_frameworks', [])
        if frameworks:
            lines.append("**Regulatory Frameworks:**")
            for fw in frameworks:
                if isinstance(fw, dict):
                    name = fw.get('framework', '')
                    relevance = fw.get('relevance', '')
                    lines.append(f"- **{name}**: {relevance}")
            lines.append("")

        # Spending intensity
        spending = intel.get('spending_intensity', {})
        if spending:
            lines.append("**IT Spending Intensity:**")
            pct = spending.get('it_spend_as_revenue_pct', '')
            vs_other = spending.get('vs_other_industries', '')
            if pct:
                lines.append(f"- IT spend as % of revenue: {pct}")
            if vs_other:
                lines.append(f"- Compared to other industries: {vs_other}")
            lines.append("")

        # Structural alignment
        alignment = intel.get('structural_alignment', '')
        if alignment:
            lines.append(f"**Strategic Alignment:** {alignment.strip()}")

        return "\n".join(lines)

    def _format_unverified_claims(self, claims: list[dict[str, Any]]) -> str:
        """Format unverified claims as warnings for prompt injection."""
        lines = [
            "## UNVERIFIED CLAIMS — DO NOT USE",
            "",
            "The following claims were found in research outputs but are NOT verified.",
            "Do NOT include these in any output. Flag them if they appear in source material.",
            ""
        ]

        for claim in claims:
            if isinstance(claim, dict):
                claim_id = claim.get('id', '')
                claim_text = claim.get('claim', '')
                status = claim.get('status', '')
                lines.append(f"- [{claim_id}] {status}: \"{claim_text}\"")

        return "\n".join(lines)
