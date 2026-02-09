"""Target company context loader for target alignment."""

import yaml
import logging
from pathlib import Path
from typing import Any, Optional


class TargetContextLoader:
    """
    Loads and manages target company context for personalization.

    Handles:
    - Company profile (name, industry, size)
    - Known technology stack
    - Observable pain signals
    - Compliance requirements
    - Recent events and engagement history
    """

    def __init__(
        self,
        config_dir: Path,
        file_path: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize target context loader.

        Args:
            config_dir: Directory where project config resides (for relative paths)
            file_path: Path to target company YAML file (relative to config_dir)
            logger: Optional logger instance
        """
        self.config_dir = Path(config_dir)
        self.file_path = file_path
        self.logger = logger or logging.getLogger(__name__)

        # Cache loaded context
        self._cache: Optional[dict[str, Any]] = None

    def load(self, target_slug: Optional[str] = None) -> dict[str, Any]:
        """
        Load target company context from YAML file.

        Args:
            target_slug: Optional slug to validate against loaded data.
                If provided, logs a warning if it doesn't match the file's slug.

        Returns:
            Dictionary with target company data

        Raises:
            yaml.YAMLError: If YAML parsing fails
        """
        if self._cache is not None:
            return self._cache

        full_path = self.config_dir / self.file_path

        if not full_path.exists():
            self.logger.warning(f"Target context file not found: {full_path}")
            return {}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            self._cache = content or {}
            self.logger.info(f"Loaded target context from {full_path}")

            # Validate slug if provided
            if target_slug:
                file_slug = self._cache.get('company', {}).get('slug', '')
                if file_slug and file_slug != target_slug:
                    self.logger.warning(
                        f"Target slug mismatch: expected '{target_slug}', "
                        f"file contains '{file_slug}'"
                    )

            return self._cache

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse target context YAML from {full_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load target context from {full_path}: {e}")
            raise

    def format_for_prompt(self, context: dict[str, Any]) -> str:
        """
        Format target company context for inclusion in alignment prompt.

        Args:
            context: Target company context dictionary (from load())

        Returns:
            Formatted string for prompt injection
        """
        sections = []

        # Company overview
        company = context.get('company', {})
        if company:
            sections.append(self._format_company(company))

        # Known technology stack
        known_stack = context.get('known_stack', {})
        if known_stack:
            sections.append(self._format_stack(known_stack))

        # Pain signals
        pain_signals = context.get('pain_signals', [])
        if pain_signals:
            sections.append(self._format_pain_signals(pain_signals))

        # Compliance requirements
        compliance = context.get('compliance', [])
        if compliance:
            sections.append(self._format_compliance(compliance))

        # Recent events
        recent_events = context.get('recent_events', [])
        if recent_events:
            sections.append(self._format_events(recent_events))

        # Engagement history
        engagement = context.get('engagement_history', [])
        if engagement:
            sections.append(self._format_engagement(engagement))

        # Filter out empty sections
        sections = [s for s in sections if s and s.strip()]

        return "\n\n".join(sections)

    def _format_company(self, company: dict[str, Any]) -> str:
        """Format company overview section."""
        lines = ["## Company Overview", ""]

        name = company.get('name', '')
        if name:
            lines.append(f"**Company:** {name}")

        industry = company.get('industry', '')
        sub_industry = company.get('sub_industry', '')
        if industry:
            industry_str = f"{industry} — {sub_industry}" if sub_industry else industry
            lines.append(f"**Industry:** {industry_str}")

        size = company.get('size', '')
        if size:
            lines.append(f"**Size:** {size}")

        revenue = company.get('revenue', '')
        if revenue:
            lines.append(f"**Revenue:** {revenue}")

        headquarters = company.get('headquarters', '')
        if headquarters:
            lines.append(f"**Headquarters:** {headquarters}")

        return "\n".join(lines)

    def _format_stack(self, stack: dict[str, Any]) -> str:
        """Format known technology stack section."""
        lines = ["## Known Technology Stack", ""]

        for tech_type, value in stack.items():
            label = tech_type.upper() if len(tech_type) <= 4 else tech_type.replace('_', ' ').title()
            if isinstance(value, list):
                lines.append(f"**{label}:** {', '.join(value)}")
            elif value:
                lines.append(f"**{label}:** {value}")

        return "\n".join(lines)

    def _format_pain_signals(self, signals: list[dict[str, Any]]) -> str:
        """Format pain signals section."""
        lines = ["## Observable Pain Signals", ""]

        for signal in signals:
            if not isinstance(signal, dict):
                continue
            signal_text = signal.get('signal', '')
            source = signal.get('source', '')
            date = signal.get('date', '')
            relevance = signal.get('relevance', '')

            if signal_text:
                lines.append(f"- **{signal_text}**")
                if source or date:
                    lines.append(f"  Source: {source} ({date})" if date else f"  Source: {source}")
                if relevance:
                    lines.append(f"  Relevance: {relevance}")
                lines.append("")

        return "\n".join(lines)

    def _format_compliance(self, compliance: list[str]) -> str:
        """Format compliance requirements section."""
        lines = ["## Compliance Requirements", ""]
        for req in compliance:
            lines.append(f"- {req}")
        return "\n".join(lines)

    def _format_events(self, events: list[dict[str, Any]]) -> str:
        """Format recent events section."""
        lines = ["## Recent Events", ""]

        for event in events:
            if not isinstance(event, dict):
                continue
            event_text = event.get('event', '')
            date = event.get('date', '')
            relevance = event.get('relevance', '')

            if event_text:
                lines.append(f"- **{event_text}** ({date})" if date else f"- **{event_text}**")
                if relevance:
                    lines.append(f"  Relevance: {relevance}")
                lines.append("")

        return "\n".join(lines)

    def _format_engagement(self, engagement: list[str]) -> str:
        """Format engagement history section."""
        lines = ["## Engagement History", ""]
        for item in engagement:
            lines.append(f"- {item}")
        return "\n".join(lines)
