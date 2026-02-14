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

        # Decision making (Category 1 expanded)
        decision_making = context.get('decision_making', {})
        if decision_making:
            sections.append(self._format_decision_making(decision_making))

        # Whitespace / Portfolio Gaps (Category 3)
        whitespace = context.get('whitespace', {})
        if whitespace:
            sections.append(self._format_whitespace(whitespace))

        # Upcoming Needs / Projects (Category 5)
        upcoming_needs = context.get('upcoming_needs', {})
        if upcoming_needs:
            sections.append(self._format_upcoming_needs(upcoming_needs))

        # Internal Champions (Category 7 — manual, formatted if present)
        champions = context.get('internal_champions', [])
        if champions:
            sections.append(self._format_champions(champions))

        # North-Star Signals (Category 8)
        north_star = context.get('north_star', {})
        if north_star:
            sections.append(self._format_north_star(north_star))

        # Research metadata
        research_metadata = context.get('research_metadata', {})
        if research_metadata:
            sections.append(self._format_research_metadata(research_metadata))

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
            source_url = signal.get('source_url', '')
            date = signal.get('date', '')
            relevance = signal.get('relevance', '')
            confidence = signal.get('confidence', '')

            if signal_text:
                lines.append(f"- **{signal_text}**")
                if source and source_url:
                    source_str = f"  Source: [{source}]({source_url})"
                elif source:
                    source_str = f"  Source: {source}"
                else:
                    source_str = ""
                if source_str:
                    lines.append(f"{source_str} ({date})" if date else source_str)
                if relevance:
                    lines.append(f"  Relevance: {relevance}")
                if confidence:
                    lines.append(f"  Confidence: {confidence}")
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
            source = event.get('source', '')
            source_url = event.get('source_url', '')

            if event_text:
                lines.append(f"- **{event_text}** ({date})" if date else f"- **{event_text}**")
                if source and source_url:
                    lines.append(f"  Source: [{source}]({source_url})")
                elif source:
                    lines.append(f"  Source: {source}")
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

    def _format_sources_list(self, sources: list) -> list[str]:
        """
        Format a sources list, handling both structured dicts and plain strings.

        Structured: {"description": "...", "url": "...", "date": "..."}
        Plain string: "Earnings call Q3 2025"

        Returns list of formatted lines.
        """
        lines = []
        for s in sources:
            if isinstance(s, dict):
                desc = s.get('description', '')
                url = s.get('url', '')
                date = s.get('date', '')
                if desc and url:
                    entry = f"- [{desc}]({url})"
                elif desc:
                    entry = f"- {desc}"
                elif url:
                    entry = f"- {url}"
                else:
                    continue
                if date:
                    entry += f" ({date})"
                lines.append(entry)
            elif isinstance(s, str) and s:
                lines.append(f"- {s}")
        return lines

    def _format_decision_making(self, data: dict[str, Any]) -> str:
        """Format decision making section (Category 1 expanded)."""
        lines = ["## Decision Making", ""]

        buying_process = data.get('buying_process', '')
        if buying_process:
            lines.append(f"**Buying Process:** {buying_process}")

        stakeholders = data.get('key_stakeholders', [])
        if stakeholders:
            lines.append("**Key Stakeholders:**")
            for s in stakeholders:
                lines.append(f"- {s}")

        budget_cycle = data.get('budget_cycle', '')
        if budget_cycle:
            lines.append(f"**Budget Cycle:** {budget_cycle}")

        triggers = data.get('evaluation_triggers', [])
        if triggers:
            lines.append("**Evaluation Triggers:**")
            for t in triggers:
                lines.append(f"- {t}")

        confidence = data.get('confidence', '')
        if confidence:
            lines.append(f"**Confidence:** {confidence}")

        sources = data.get('sources', [])
        if sources:
            lines.append("**Sources:**")
            lines.extend(self._format_sources_list(sources))

        return "\n".join(lines)

    def _format_whitespace(self, data: dict[str, Any]) -> str:
        """Format whitespace / portfolio gaps section (Category 3)."""
        lines = ["## Whitespace & Portfolio Gaps", ""]

        missing = data.get('missing_capabilities', [])
        if missing:
            lines.append("**Missing Capabilities:**")
            for m in missing:
                lines.append(f"- {m}")

        underserved = data.get('underserved_areas', [])
        if underserved:
            lines.append("**Underserved Areas:**")
            for u in underserved:
                lines.append(f"- {u}")

        expansion = data.get('expansion_signals', [])
        if expansion:
            lines.append("**Expansion Signals:**")
            for e in expansion:
                lines.append(f"- {e}")

        confidence = data.get('confidence', '')
        if confidence:
            lines.append(f"**Confidence:** {confidence}")

        sources = data.get('sources', [])
        if sources:
            lines.append("**Sources:**")
            lines.extend(self._format_sources_list(sources))

        return "\n".join(lines)

    def _format_upcoming_needs(self, data: dict[str, Any]) -> str:
        """Format upcoming needs / projects section (Category 5)."""
        lines = ["## Upcoming Needs & Projects", ""]

        announced = data.get('announced_projects', [])
        if announced:
            lines.append("**Announced Projects:**")
            for a in announced:
                lines.append(f"- {a}")

        inferred = data.get('inferred_needs', [])
        if inferred:
            lines.append("**Inferred Needs:**")
            for i in inferred:
                lines.append(f"- {i}")

        budget = data.get('budget_indicators', [])
        if budget:
            lines.append("**Budget Indicators:**")
            for b in budget:
                lines.append(f"- {b}")

        timeline = data.get('timeline_signals', [])
        if timeline:
            lines.append("**Timeline Signals:**")
            for t in timeline:
                lines.append(f"- {t}")

        confidence = data.get('confidence', '')
        if confidence:
            lines.append(f"**Confidence:** {confidence}")

        sources = data.get('sources', [])
        if sources:
            lines.append("**Sources:**")
            lines.extend(self._format_sources_list(sources))

        return "\n".join(lines)

    def _format_champions(self, champions: list[dict[str, Any]]) -> str:
        """Format internal champions section (Category 7 — manual input)."""
        # Only format if there are champions with actual data
        has_data = any(
            c.get('name') or c.get('title')
            for c in champions
            if isinstance(c, dict)
        )
        if not has_data:
            return ""

        lines = ["## Internal Champions", ""]

        for champion in champions:
            if not isinstance(champion, dict):
                continue
            name = champion.get('name', '')
            title = champion.get('title', '')
            if not name and not title:
                continue

            label = f"{name} — {title}" if name and title else name or title
            lines.append(f"- **{label}**")

            status = champion.get('relationship_status', '')
            if status:
                lines.append(f"  Relationship: {status}")

            influence = champion.get('influence_level', '')
            if influence:
                lines.append(f"  Influence: {influence}")

            notes = champion.get('notes', '')
            if notes:
                lines.append(f"  Notes: {notes}")

            lines.append("")

        return "\n".join(lines)

    def _format_north_star(self, data: dict[str, Any]) -> str:
        """Format north-star signals section (Category 8)."""
        lines = ["## North-Star Signals & Thought Leadership", ""]

        initiatives = data.get('strategic_initiatives', [])
        if initiatives:
            lines.append("**Strategic Initiatives:**")
            for i in initiatives:
                lines.append(f"- {i}")

        leadership = data.get('thought_leadership', [])
        if leadership:
            lines.append("**Thought Leadership:**")
            for l in leadership:
                lines.append(f"- {l}")

        positioning = data.get('industry_positioning', [])
        if positioning:
            lines.append("**Industry Positioning:**")
            for p in positioning:
                lines.append(f"- {p}")

        transformation = data.get('transformation_signals', [])
        if transformation:
            lines.append("**Transformation Signals:**")
            for t in transformation:
                lines.append(f"- {t}")

        confidence = data.get('confidence', '')
        if confidence:
            lines.append(f"**Confidence:** {confidence}")

        sources = data.get('sources', [])
        if sources:
            lines.append("**Sources:**")
            lines.extend(self._format_sources_list(sources))

        return "\n".join(lines)

    def _format_research_metadata(self, data: dict[str, Any]) -> str:
        """Format research metadata section."""
        lines = ["## Research Metadata", ""]

        researched_at = data.get('researched_at', '')
        if researched_at:
            lines.append(f"**Researched At:** {researched_at}")

        agent_model = data.get('agent_model', '')
        if agent_model:
            lines.append(f"**Agent Model:** {agent_model}")

        searches = data.get('searches_performed', 0)
        if searches:
            lines.append(f"**Searches Performed:** {searches}")

        categories = data.get('categories_researched', [])
        if categories:
            lines.append(f"**Categories Researched:** {', '.join(categories)}")

        manual = data.get('manual_sections', [])
        if manual:
            lines.append(f"**Manual Sections:** {', '.join(manual)}")

        return "\n".join(lines)
