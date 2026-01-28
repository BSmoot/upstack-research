"""Brand context loader for brand alignment."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class BrandContextLoader:
    """
    Loads and manages brand context files for alignment.

    Handles:
    - Baseline brand context (values, voice, positioning)
    - Writing standards (style, formatting, tone)
    - Audience personas (target readers)
    - Glossary (terminology, definitions)
    """

    def __init__(
        self,
        config_dir: Path,
        context_files: Dict[str, str],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize brand context loader.

        Args:
            config_dir: Directory where project config resides (for relative paths)
            context_files: Dictionary mapping context type to file path
            logger: Optional logger instance
        """
        self.config_dir = Path(config_dir)
        self.context_files = context_files
        self.logger = logger or logging.getLogger(__name__)

        # Cache loaded context
        self._cache: Dict[str, Any] = {}

    def load_all(self) -> Dict[str, Any]:
        """
        Load all configured brand context files.

        Returns:
            Dictionary with all brand context data
        """
        context = {}

        for context_type, file_path in self.context_files.items():
            try:
                content = self._load_context_file(file_path)
                if content is not None:
                    context[context_type] = content
                    self.logger.info(f"Loaded brand context: {context_type} from {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load {context_type} from {file_path}: {e}")

        return context

    def _load_context_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a single brand context file.

        Args:
            file_path: Path to context file (relative to config_dir)

        Returns:
            Loaded context data or None if file doesn't exist
        """
        # Check cache first
        if file_path in self._cache:
            return self._cache[file_path]

        # Resolve path relative to config directory
        full_path = self.config_dir / file_path

        if not full_path.exists():
            self.logger.warning(f"Brand context file not found: {full_path}")
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            # Cache for future use
            self._cache[file_path] = content

            return content

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML from {full_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load brand context from {full_path}: {e}")
            raise

    def format_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format loaded brand context for inclusion in alignment prompt.

        Args:
            context: Brand context dictionary

        Returns:
            Formatted string for prompt injection
        """
        sections = []

        if 'baseline' in context:
            baseline = context['baseline']
            sections.append(self._format_baseline(baseline))

        if 'writing_standards' in context:
            standards = context['writing_standards']
            sections.append(self._format_writing_standards(standards))

        if 'audience_personas' in context:
            personas = context['audience_personas']
            sections.append(self._format_audience_personas(personas))

        if 'glossary' in context:
            glossary = context['glossary']
            sections.append(self._format_glossary(glossary))

        # Filter out empty sections
        sections = [s for s in sections if s and s.strip()]

        return "\n\n".join(sections)

    def _format_baseline(self, baseline: Dict[str, Any]) -> str:
        """Format baseline brand context."""
        lines = ["## Brand Baseline", ""]

        # Handle new schema (company.name) or legacy (company_name)
        company = baseline.get('company', {})
        if isinstance(company, dict):
            if 'name' in company:
                lines.append(f"**Company**: {company['name']}")
            if 'description' in company:
                lines.append(f"**Description**: {company['description']}")
        elif 'company_name' in baseline:
            lines.append(f"**Company**: {baseline['company_name']}")

        if 'tagline' in baseline:
            lines.append(f"**Tagline**: {baseline['tagline']}")

        # Business model
        biz_model = baseline.get('business_model', {})
        if isinstance(biz_model, dict):
            if 'description' in biz_model:
                lines.append(f"\n**Business Model**: {biz_model['description']}")
            if 'value_proposition' in biz_model:
                vp = biz_model['value_proposition']
                if isinstance(vp, dict) and 'primary' in vp:
                    lines.append(f"**Value Proposition**: {vp['primary']}")
                    if 'dimensions' in vp:
                        lines.append("\n**Value Dimensions**:")
                        for dim in vp['dimensions']:
                            lines.append(f"- {dim}")
            if 'trust_model' in biz_model:
                lines.append("\n**Trust Model**:")
                for key, val in biz_model['trust_model'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {val}")
            if 'differentiation' in biz_model:
                diff = biz_model['differentiation']
                if isinstance(diff, dict) and 'primary' in diff:
                    lines.append(f"\n**Key Differentiator**: {diff['primary']}")

        # Legacy values handling
        if 'values' in baseline:
            lines.append("\n**Core Values**:")
            for value in baseline['values']:
                lines.append(f"- {value}")

        if 'voice' in baseline:
            lines.append("\n**Brand Voice**:")
            for trait, description in baseline['voice'].items():
                lines.append(f"- **{trait.title()}**: {description}")

        if 'positioning' in baseline:
            lines.append(f"\n**Positioning**: {baseline['positioning']}")

        return "\n".join(lines)

    def _format_writing_standards(self, standards: Dict[str, Any]) -> str:
        """Format writing standards."""
        lines = ["## Writing Standards", ""]

        # Handle new schema (avoid_patterns, natural_writing, density)
        if 'avoid_patterns' in standards:
            lines.append("**Patterns to Avoid**:")
            for pattern in standards['avoid_patterns']:
                if isinstance(pattern, dict):
                    p = pattern.get('pattern', '')
                    fix = pattern.get('fix', '')
                    lines.append(f"- Avoid: \"{p}\" → Use: \"{fix}\"")
                else:
                    lines.append(f"- {pattern}")

        if 'natural_writing' in standards:
            nw = standards['natural_writing']
            if isinstance(nw, dict):
                if 'voice_test' in nw:
                    lines.append("\n**Voice Test**:")
                    for item in nw['voice_test']:
                        lines.append(f"- {item}")
                if 'pronouns' in nw:
                    lines.append("\n**Pronoun Usage**:")
                    for item in nw['pronouns']:
                        lines.append(f"- {item}")
                if 'contractions' in nw:
                    lines.append("\n**Contractions**:")
                    for item in nw['contractions']:
                        lines.append(f"- {item}")

        if 'density' in standards:
            density = standards['density']
            if isinstance(density, dict):
                if 'principle' in density:
                    lines.append(f"\n**Density Principle**: {density['principle']}")
                if 'word_choices' in density:
                    wc = density['word_choices']
                    if 'cut' in wc:
                        lines.append("\n**Words to Cut**:")
                        for word in wc['cut']:
                            lines.append(f"- {word}")
                    if 'prefer' in wc:
                        lines.append("\n**Preferred Words**:")
                        for word in wc['prefer']:
                            lines.append(f"- {word}")

        # Legacy format handling
        if 'tone' in standards:
            lines.append(f"**Tone**: {standards['tone']}")

        if 'style_guidelines' in standards:
            lines.append("\n**Style Guidelines**:")
            for guideline in standards['style_guidelines']:
                lines.append(f"- {guideline}")

        if 'formatting' in standards:
            lines.append("\n**Formatting Rules**:")
            for rule in standards['formatting']:
                lines.append(f"- {rule}")

        if 'avoid' in standards:
            lines.append("\n**Avoid**:")
            for item in standards['avoid']:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def _format_audience_personas(self, personas: Dict[str, Any]) -> str:
        """Format audience personas."""
        lines = ["## Target Audience Personas", ""]

        # Handle new schema (role_priorities, communication, etc.)
        if 'role_priorities' in personas:
            lines.append("### Role-Specific Priorities")
            for role_key, role_data in personas['role_priorities'].items():
                if isinstance(role_data, dict):
                    title = role_data.get('title', role_key)
                    focus = role_data.get('primary_focus', '')
                    lines.append(f"\n**{title}**")
                    if focus:
                        lines.append(f"- Primary Focus: {focus}")
                    if 'priorities' in role_data:
                        for priority in role_data['priorities']:
                            lines.append(f"- {priority}")

        if 'communication' in personas:
            comm = personas['communication']
            if isinstance(comm, dict) and 'tone_and_style' in comm:
                lines.append("\n### Communication Preferences")
                for style in comm['tone_and_style']:
                    if isinstance(style, dict):
                        guideline = style.get('guideline', '')
                        desc = style.get('description', '')
                        lines.append(f"- **{guideline}**: {desc}")

        if 'research_agent_guidelines' in personas:
            lines.append("\n### Key Principles")
            for guideline in personas['research_agent_guidelines']:
                if isinstance(guideline, dict):
                    principle = guideline.get('principle', '')
                    guidance = guideline.get('guidance', '')
                    lines.append(f"- **{principle}**: {guidance}")

        # Legacy format handling
        if 'personas' in personas:
            for persona in personas['personas']:
                lines.append(f"### {persona.get('title', 'Persona')}")

                if 'role' in persona:
                    lines.append(f"**Role**: {persona['role']}")

                if 'priorities' in persona:
                    lines.append("\n**Priorities**:")
                    for priority in persona['priorities']:
                        lines.append(f"- {priority}")

                if 'communication_style' in persona:
                    lines.append(f"\n**Communication Style**: {persona['communication_style']}")

                lines.append("")

        return "\n".join(lines)

    def _format_glossary(self, glossary: Dict[str, Any]) -> str:
        """Format terminology glossary."""
        lines = ["## Terminology Glossary", ""]

        # Handle new schema (categorized terms like network, data_center, etc.)
        # Extract key industry terms from glossary categories
        key_categories = ['business_model', 'commercial', 'operations']
        for category in key_categories:
            if category in glossary:
                cat_data = glossary[category]
                if isinstance(cat_data, dict):
                    lines.append(f"\n### {category.replace('_', ' ').title()} Terms")
                    count = 0
                    for term_key, term_data in cat_data.items():
                        if count >= 10:  # Limit to key terms
                            break
                        if isinstance(term_data, dict):
                            full_name = term_data.get('full', term_key)
                            definition = term_data.get('definition', '')
                            abbrev = term_data.get('abbrev', '')
                            if abbrev:
                                lines.append(f"- **{abbrev}** ({full_name}): {definition}")
                            elif definition:
                                lines.append(f"- **{full_name}**: {definition}")
                            count += 1

        # Legacy format handling
        if 'terms' in glossary:
            for term, definition in glossary['terms'].items():
                lines.append(f"**{term}**: {definition}")

        if 'preferred_terms' in glossary:
            lines.append("\n**Preferred Terms**:")
            for preferred, avoid in glossary['preferred_terms'].items():
                lines.append(f"- Use '{preferred}' instead of '{avoid}'")

        return "\n".join(lines)
