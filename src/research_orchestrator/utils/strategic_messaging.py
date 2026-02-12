"""Strategic messaging loader for research agent context."""

import yaml
import logging
from pathlib import Path
from typing import Any


class StrategicMessagingLoader:
    """
    Loads and manages strategic messaging context for research agents.

    Handles:
    - Category creation framework and framing rules
    - Intelligence staging levels and safe language
    - Three pillars strategic positioning
    - Maturity model for prospect self-assessment
    - Service components (distinct from service categories)
    - Champion enablement requirements
    - Operational proof narratives
    - Outreach audit findings and anti-patterns
    - Vertical-specific messaging adaptations
    """

    def __init__(
        self,
        config_dir: Path,
        file_path: str,
        logger: logging.Logger | None = None
    ):
        self.config_dir = Path(config_dir)
        self.file_path = file_path
        self.logger = logger or logging.getLogger(__name__)
        self._cache: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache

        full_path = self.config_dir / self.file_path

        if not full_path.exists():
            self.logger.warning(f"Strategic messaging file not found: {full_path}")
            return {}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self.logger.warning(f"Strategic messaging file is not a dict: {full_path}")
                return {}

            self._cache = data
            self.logger.info(f"Loaded strategic messaging from {full_path}")
            return self._cache

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse strategic messaging YAML from {full_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load strategic messaging from {full_path}: {e}")
            raise

    def _is_populated(self, section: dict[str, Any]) -> bool:
        if section.get('status') == 'SCAFFOLD':
            return False

        def has_placeholder(obj: Any) -> bool:
            if isinstance(obj, str):
                return 'PLACEHOLDER' in obj
            elif isinstance(obj, dict):
                return any(has_placeholder(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(has_placeholder(item) for item in obj)
            return False

        return not has_placeholder(section)

    # --- Section-Level Accessors ---

    def get_framing_rules(self) -> list[dict[str, Any]]:
        data = self.load()
        category_creation = data.get('category_creation', {})
        if not self._is_populated(category_creation):
            return []
        return category_creation.get('framing_rules', [])

    def get_intelligence_staging(self) -> dict[str, Any]:
        data = self.load()
        intelligence_staging = data.get('intelligence_staging', {})
        if not self._is_populated(intelligence_staging):
            return {}
        return intelligence_staging

    def get_three_pillars(self) -> list[dict[str, Any]]:
        data = self.load()
        three_pillars = data.get('three_pillars', {})
        if not self._is_populated(three_pillars):
            return []
        return three_pillars.get('pillars', [])

    def get_maturity_model(self) -> dict[str, Any]:
        data = self.load()
        maturity_model = data.get('maturity_model', {})
        if not self._is_populated(maturity_model):
            return {}
        return maturity_model

    def get_service_components(self) -> list[dict[str, Any]]:
        data = self.load()
        service_components = data.get('service_components', {})
        if not self._is_populated(service_components):
            return []
        return service_components.get('components', [])

    def get_champion_requirements(self) -> dict[str, Any]:
        data = self.load()
        champion_enablement = data.get('champion_enablement', {})
        if not self._is_populated(champion_enablement):
            return {}
        return champion_enablement

    def get_operational_proof(self) -> list[dict[str, Any]]:
        data = self.load()
        operational_proof = data.get('operational_proof', {})
        if not self._is_populated(operational_proof):
            return []
        return operational_proof.get('narratives', [])

    def get_outreach_audit(self) -> dict[str, Any]:
        data = self.load()
        outreach_audit = data.get('outreach_audit', {})
        if not self._is_populated(outreach_audit):
            return {}
        return outreach_audit

    def get_vertical_adaptation(self, vertical: str) -> dict[str, Any]:
        data = self.load()
        vertical_adaptations = data.get('vertical_adaptations', {})
        if not self._is_populated(vertical_adaptations):
            return {}
        adaptation = vertical_adaptations.get(vertical, {})
        if not adaptation or (isinstance(adaptation, dict) and not adaptation):
            return {}
        return adaptation

    # --- Stage-Specific Formatters ---

    def format_for_research(self) -> str:
        sections = []

        framing_rules = self.get_framing_rules()
        if framing_rules:
            formatted = self._format_framing_rules(framing_rules)
            if formatted:
                sections.append(formatted)

        intelligence_staging = self.get_intelligence_staging()
        if intelligence_staging:
            formatted = self._format_intelligence_staging_compact(intelligence_staging)
            if formatted:
                sections.append(formatted)

        return "\n\n".join(sections)

    def format_for_playbook(self, vertical: str | None = None) -> str:
        sections = []

        data = self.load()
        category_creation = data.get('category_creation', {})
        if self._is_populated(category_creation):
            formatted = self._format_category_creation_playbook(category_creation)
            if formatted:
                sections.append(formatted)

        pillars = self.get_three_pillars()
        if pillars:
            formatted = self._format_pillars(pillars)
            if formatted:
                sections.append(formatted)

        maturity_model = self.get_maturity_model()
        if maturity_model:
            formatted = self._format_maturity_model_compact(maturity_model)
            if formatted:
                sections.append(formatted)

        components = self.get_service_components()
        if components:
            formatted = self._format_service_components(components)
            if formatted:
                sections.append(formatted)

        champion = self.get_champion_requirements()
        if champion:
            formatted = self._format_champion_enablement_compact(champion)
            if formatted:
                sections.append(formatted)

        operational_proof = self.get_operational_proof()
        if operational_proof:
            formatted = self._format_operational_proof_compact(operational_proof)
            if formatted:
                sections.append(formatted)

        if vertical:
            adaptation = self.get_vertical_adaptation(vertical)
            if adaptation:
                formatted = self._format_vertical_adaptation(vertical, adaptation)
                if formatted:
                    sections.append(formatted)

        return "\n\n".join(sections)

    def format_for_validation(self) -> str:
        sections = []

        outreach_audit = self.get_outreach_audit()
        if outreach_audit:
            formatted = self._format_outreach_audit(outreach_audit)
            if formatted:
                sections.append(formatted)

        intelligence_staging = self.get_intelligence_staging()
        if intelligence_staging:
            formatted = self._format_intelligence_staging_full(intelligence_staging)
            if formatted:
                sections.append(formatted)

        champion = self.get_champion_requirements()
        if champion:
            formatted = self._format_champion_forwardable_criteria(champion)
            if formatted:
                sections.append(formatted)

        return "\n\n".join(sections)

    def format_for_prompt(self, vertical: str | None = None) -> str:
        """
        Format all strategic messaging sections (~800 tokens).

        Used for brand alignment — provides complete strategic context.
        """
        sections = self._collect_core_sections()
        sections.extend(self._collect_vertical_sections(vertical))
        return "\n\n".join(sections)

    def _collect_core_sections(self) -> list[str]:
        """Collect all core strategic messaging sections (full format)."""
        sections: list[str] = []
        formatters: list[tuple[Any, Any]] = [
            (lambda: self._get_and_format_category_creation(), None),
            (self.get_three_pillars, self._format_pillars_full),
            (self.get_maturity_model, self._format_maturity_model_full),
            (self.get_service_components, self._format_service_components),
            (self.get_intelligence_staging, self._format_intelligence_staging_full),
            (self.get_champion_requirements, self._format_champion_enablement_full),
            (self.get_operational_proof, self._format_operational_proof_full),
            (self.get_outreach_audit, self._format_outreach_audit),
        ]

        for getter, formatter in formatters:
            if formatter is None:
                # Special case: getter returns pre-formatted string
                formatted = getter()
            else:
                data = getter()
                if not data:
                    continue
                formatted = formatter(data)
            if formatted:
                sections.append(formatted)

        return sections

    def _get_and_format_category_creation(self) -> str:
        """Get and format category creation section (full)."""
        data = self.load()
        category_creation = data.get('category_creation', {})
        if self._is_populated(category_creation):
            return self._format_category_creation_full(category_creation)
        return ""

    def _collect_vertical_sections(
        self,
        vertical: str | None
    ) -> list[str]:
        """Collect vertical-specific sections."""
        if not vertical:
            return []
        adaptation = self.get_vertical_adaptation(vertical)
        if not adaptation:
            return []
        formatted = self._format_vertical_adaptation(vertical, adaptation)
        return [formatted] if formatted else []

    # --- Private Formatting Helpers ---

    def _format_framing_rules(self, rules: list[dict[str, Any]]) -> str:
        lines = ["## Strategic Framing Rules", ""]

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            rule_text = rule.get('rule', '')
            example_good = rule.get('example_good', '')
            example_bad = rule.get('example_bad', '')

            if rule_text:
                lines.append(f"**{rule_text}**")
                if example_bad:
                    lines.append(f"- DON'T: {example_bad}")
                if example_good:
                    lines.append(f"- DO: {example_good}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_category_creation_playbook(
        self,
        category_creation: dict[str, Any]
    ) -> str:
        lines = ["## Category Creation Framework", ""]

        category_name = category_creation.get('category_name', '')
        if category_name:
            lines.append(f"**Category:** {category_name}")
            lines.append("")

        thesis = category_creation.get('category_thesis', '').strip()
        if thesis:
            sentences = thesis.split('. ')
            short_thesis = '. '.join(sentences[:2])
            if not short_thesis.endswith('.'):
                short_thesis += '.'
            lines.append(short_thesis)
            lines.append("")

        framing_rules = category_creation.get('framing_rules', [])
        if framing_rules:
            formatted_rules = self._format_framing_rules(framing_rules)
            if formatted_rules:
                lines.append(formatted_rules)

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_category_creation_full(
        self,
        category_creation: dict[str, Any]
    ) -> str:
        lines = ["## Category Creation Framework", ""]

        category_name = category_creation.get('category_name', '')
        if category_name:
            lines.append(f"**Category:** {category_name}")
            lines.append("")

        thesis = category_creation.get('category_thesis', '').strip()
        if thesis:
            lines.append(thesis)
            lines.append("")

        framing_rules = category_creation.get('framing_rules', [])
        if framing_rules:
            formatted_rules = self._format_framing_rules(framing_rules)
            if formatted_rules:
                lines.append(formatted_rules)

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_intelligence_staging_compact(
        self,
        staging: dict[str, Any]
    ) -> str:
        lines = ["## Intelligence Staging", ""]

        agent_guidance = staging.get('agent_guidance', '').strip()
        if agent_guidance:
            lines.append(agent_guidance)

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_intelligence_staging_full(
        self,
        staging: dict[str, Any]
    ) -> str:
        lines = ["## Intelligence Staging Framework", ""]

        purpose = staging.get('purpose', '').strip()
        if purpose:
            lines.append(purpose)
            lines.append("")

        levels = staging.get('levels', [])
        if levels:
            for level in levels:
                if not isinstance(level, dict):
                    continue

                level_num = level.get('level', '')
                name = level.get('name', '')
                description = level.get('description', '').strip()

                if name:
                    lines.append(f"**Level {level_num}: {name}**")
                    if description:
                        lines.append(description)

                safe_language = level.get('safe_language', [])
                if safe_language:
                    lines.append("- Safe language:")
                    for lang in safe_language:
                        lines.append(f"  - {lang}")

                unsafe_language = level.get('unsafe_language', [])
                if unsafe_language:
                    lines.append("- Unsafe language:")
                    for lang in unsafe_language:
                        lines.append(f"  - {lang}")

                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_pillars(self, pillars: list[dict[str, Any]]) -> str:
        lines = ["## Three Strategic Pillars", ""]

        for pillar in pillars:
            if not isinstance(pillar, dict):
                continue

            name = pillar.get('name', '')
            description = pillar.get('description', '').strip()

            if name and description:
                lines.append(f"**{name}:** {description}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_pillars_full(self, pillars: list[dict[str, Any]]) -> str:
        lines = ["## Three Strategic Pillars", ""]

        for pillar in pillars:
            if not isinstance(pillar, dict):
                continue

            name = pillar.get('name', '')
            description = pillar.get('description', '').strip()
            replaces = pillar.get('replaces', '').strip()
            agent_guidance = pillar.get('agent_guidance', '').strip()

            if name:
                lines.append(f"### {name}")
                if description:
                    lines.append(description)
                if replaces:
                    lines.append(f"**Replaces:** {replaces}")
                if agent_guidance:
                    lines.append(f"**Agent Guidance:** {agent_guidance}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_maturity_model_compact(
        self,
        model: dict[str, Any]
    ) -> str:
        lines = ["## Maturity Model", ""]

        name = model.get('name', '')
        if name:
            lines.append(f"**{name}**")
            lines.append("")

        levels = model.get('levels', [])
        if levels:
            level_names = [
                level.get('name', '')
                for level in levels
                if isinstance(level, dict) and level.get('name')
            ]
            if level_names:
                lines.append("**Levels:** " + " -> ".join(level_names))

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_maturity_model_full(
        self,
        model: dict[str, Any]
    ) -> str:
        lines = ["## Maturity Model", ""]

        name = model.get('name', '')
        purpose = model.get('purpose', '').strip()

        if name:
            lines.append(f"**{name}**")
        if purpose:
            lines.append(purpose)
            lines.append("")

        levels = model.get('levels', [])
        if levels:
            for level in levels:
                if not isinstance(level, dict):
                    continue

                level_name = level.get('name', '')
                description = level.get('description', '').strip()

                if level_name:
                    lines.append(f"**{level_name}**")
                    if description:
                        lines.append(description)
                    lines.append("")

        agent_guidance = model.get('agent_guidance', '').strip()
        if agent_guidance:
            lines.append(f"**Agent Guidance:** {agent_guidance}")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_service_components(
        self,
        components: list[dict[str, Any]]
    ) -> str:
        lines = ["## Service Components", ""]

        for component in components:
            if not isinstance(component, dict):
                continue

            name = component.get('name', '')
            description = component.get('description', '').strip()

            if name and description:
                lines.append(f"**{name}:** {description}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_champion_enablement_compact(
        self,
        champion: dict[str, Any]
    ) -> str:
        lines = ["## Champion Enablement", ""]

        requirements = champion.get('requirements', [])
        if requirements:
            for req in requirements:
                if isinstance(req, dict):
                    requirement = req.get('requirement', '')
                    if requirement:
                        lines.append(f"- {requirement}")
                elif isinstance(req, str):
                    lines.append(f"- {req}")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_champion_enablement_full(
        self,
        champion: dict[str, Any]
    ) -> str:
        lines = ["## Champion Enablement Requirements", ""]

        context = champion.get('context', '').strip()
        if context:
            lines.append(context)
            lines.append("")

        requirements = champion.get('requirements', [])
        if requirements:
            lines.append("**Requirements:**")
            for req in requirements:
                if isinstance(req, dict):
                    requirement = req.get('requirement', '')
                    description = req.get('description', req.get('detail', '')).strip()
                    if requirement:
                        lines.append(f"- {requirement}")
                        if description:
                            lines.append(f"  {description}")
                elif isinstance(req, str):
                    lines.append(f"- {req}")
            lines.append("")

        forwardable = champion.get('forwardable_criteria', {})
        if forwardable:
            formatted = self._format_champion_forwardable_criteria(champion)
            if formatted:
                lines.append(formatted)

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_champion_forwardable_criteria(
        self,
        champion: dict[str, Any]
    ) -> str:
        lines = ["**Forwardable Content Criteria:**", ""]

        forwardable = champion.get('forwardable_criteria', {})
        if not forwardable:
            return ""

        good = forwardable.get('good', [])
        if good:
            lines.append("**Good (forwardable):**")
            for item in good:
                lines.append(f"- {item}")
            lines.append("")

        bad = forwardable.get('bad', [])
        if bad:
            lines.append("**Bad (not forwardable):**")
            for item in bad:
                lines.append(f"- {item}")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_operational_proof_compact(
        self,
        narratives: list[dict[str, Any]]
    ) -> str:
        lines = ["## Operational Proof Narratives", ""]

        for narrative in narratives:
            if not isinstance(narrative, dict):
                continue

            title = narrative.get('title', '')
            problem = narrative.get('problem', '').strip()

            if title:
                lines.append(f"**{title}**")
                if problem:
                    lines.append(f"Problem: {problem}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_operational_proof_full(
        self,
        narratives: list[dict[str, Any]]
    ) -> str:
        lines = ["## Operational Proof Narratives", ""]

        for narrative in narratives:
            if not isinstance(narrative, dict):
                continue

            title = narrative.get('title', '')
            problem = narrative.get('problem', '').strip()
            intervention = narrative.get('intervention', '').strip()
            counterfactual = narrative.get('counterfactual', '').strip()

            if title:
                lines.append(f"### {title}")
                if problem:
                    lines.append(f"**Problem:** {problem}")
                if intervention:
                    lines.append(f"**UPSTACK Intervention:** {intervention}")
                if counterfactual:
                    lines.append(f"**Without UPSTACK:** {counterfactual}")
                lines.append("")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_outreach_audit(self, audit: dict[str, Any]) -> str:
        lines = ["## Outreach Quality Requirements", ""]

        anti_patterns = audit.get('anti_patterns', [])
        if anti_patterns:
            lines.append("**Anti-Patterns to Avoid:**")
            for pattern in anti_patterns:
                if isinstance(pattern, dict):
                    pattern_text = pattern.get('pattern', '')
                    instead = pattern.get('instead', '').strip()
                    if pattern_text:
                        lines.append(f"- {pattern_text}")
                        if instead:
                            lines.append(f"  Instead: {instead}")
                elif isinstance(pattern, str):
                    lines.append(f"- {pattern}")
            lines.append("")

        kill_items = audit.get('kill_items', [])
        if kill_items:
            lines.append("**Kill Items (NEVER include):**")
            for item in kill_items:
                if isinstance(item, dict):
                    item_text = item.get('item', '')
                    reason = item.get('reason', '').strip()
                    if item_text:
                        lines.append(f"- {item_text}")
                        if reason:
                            lines.append(f"  Reason: {reason}")
                elif isinstance(item, str):
                    lines.append(f"- {item}")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)

    def _format_vertical_adaptation(
        self,
        vertical: str,
        adaptation: dict[str, Any]
    ) -> str:
        vertical_label = vertical.replace('_', ' ').title()
        lines = [f"## {vertical_label} Messaging Adaptation", ""]

        thesis_adaptation = adaptation.get('category_thesis_adaptation', '').strip()
        if thesis_adaptation:
            lines.append(f"**Category Thesis Adaptation:** {thesis_adaptation}")
            lines.append("")

        maturity_emphasis = adaptation.get('maturity_model_emphasis', '').strip()
        if maturity_emphasis:
            lines.append(f"**Maturity Model Emphasis:** {maturity_emphasis}")
            lines.append("")

        champion_profile = adaptation.get('champion_profile', '').strip()
        if champion_profile:
            lines.append(f"**Champion Profile:** {champion_profile}")

        if len(lines) <= 2:
            return ""
        return "\n".join(lines)
