"""Tests for strategic messaging loader."""

import pytest
import tempfile
import yaml
from pathlib import Path
from research_orchestrator.utils.strategic_messaging import StrategicMessagingLoader


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_messaging_data():
    return {
        'category_creation': {
            'category_name': 'Technology Infrastructure Advisory',
            'category_thesis': 'Traditional IT procurement is broken. Organizations struggle with vendor complexity, technology obsolescence, and hidden costs. UPSTACK creates a new category: independent infrastructure advisory that guides buyers through the entire technology lifecycle.',
            'framing_rules': [
                {
                    'rule': 'Never position as middleman or reseller',
                    'example_bad': 'We connect you with vendors',
                    'example_good': 'We guide your infrastructure decisions'
                },
                {
                    'rule': 'Frame vendor payment as independence proof',
                    'example_bad': 'Our service is free',
                    'example_good': 'You pay nothing—vendors compensate us for bringing them qualified opportunities'
                }
            ]
        },
        'intelligence_staging': {
            'purpose': 'Control information disclosure based on prospect readiness',
            'agent_guidance': 'Never mention vendor payment model in early outreach',
            'levels': [
                {
                    'level': 1,
                    'name': 'Problem Awareness',
                    'description': 'Focus on infrastructure challenges',
                    'safe_language': ['infrastructure planning', 'technology evaluation'],
                    'unsafe_language': ['vendor-paid', 'commission']
                },
                {
                    'level': 2,
                    'name': 'Solution Exploration',
                    'description': 'Introduce advisory value',
                    'safe_language': ['independent advisory', 'technology lifecycle'],
                    'unsafe_language': ['referral fee', 'vendor funding']
                }
            ]
        },
        'three_pillars': {
            'pillars': [
                {
                    'name': 'Independent Advisory',
                    'description': 'Vendor-agnostic guidance throughout technology lifecycle',
                    'replaces': 'Sales engineering',
                    'agent_guidance': 'Emphasize lifecycle support, not one-time recommendations'
                },
                {
                    'name': 'Vendor Orchestration',
                    'description': 'Manage complexity of multi-vendor ecosystems',
                    'replaces': 'RFP consultants',
                    'agent_guidance': 'Position as ongoing relationship manager'
                },
                {
                    'name': 'Risk Management',
                    'description': 'De-risk infrastructure decisions through expert validation',
                    'replaces': 'Internal IT assessment',
                    'agent_guidance': 'Highlight experience across hundreds of implementations'
                }
            ]
        },
        'maturity_model': {
            'name': 'Infrastructure Procurement Maturity',
            'purpose': 'Help prospects self-assess their current state',
            'levels': [
                {
                    'name': 'Reactive',
                    'description': 'Responding to immediate failures'
                },
                {
                    'name': 'Managed',
                    'description': 'Structured evaluation processes'
                },
                {
                    'name': 'Strategic',
                    'description': 'Proactive lifecycle planning'
                }
            ],
            'agent_guidance': 'Use maturity model to create urgency without pressure'
        },
        'service_components': {
            'components': [
                {
                    'name': 'Technology Assessment',
                    'description': 'Evaluate current infrastructure and identify gaps'
                },
                {
                    'name': 'Vendor Selection',
                    'description': 'Navigate vendor landscape and manage RFP process'
                },
                {
                    'name': 'Lifecycle Management',
                    'description': 'Ongoing optimization and technology refresh planning'
                }
            ]
        },
        'champion_enablement': {
            'context': 'Champions must be able to forward materials to stakeholders',
            'requirements': [
                {
                    'requirement': 'No vendor payment mentions',
                    'description': 'Early materials must be stakeholder-safe'
                },
                {
                    'requirement': 'Quantified value statements',
                    'description': 'Champions need specific ROI claims'
                }
            ],
            'forwardable_criteria': {
                'good': [
                    'Infrastructure assessment findings',
                    'Technology lifecycle recommendations',
                    'Risk mitigation strategies'
                ],
                'bad': [
                    'Vendor payment model explanations',
                    'UPSTACK commission structure',
                    'Supplier referral processes'
                ]
            }
        },
        'operational_proof': {
            'narratives': [
                {
                    'title': 'The Hidden Vendor Lock-In',
                    'problem': 'CIO renews expensive contract because migration seems impossible',
                    'intervention': 'UPSTACK maps migration path with competing vendors, quantifies savings',
                    'counterfactual': 'CIO overpays $200K/year for 3+ years'
                },
                {
                    'title': 'The Premature Cloud Migration',
                    'problem': 'VP IT pressured to move workloads to cloud without TCO analysis',
                    'intervention': 'UPSTACK models hybrid scenarios, prevents $500K mistake',
                    'counterfactual': 'Company migrates unsuitable workloads, faces cost overruns'
                }
            ]
        },
        'outreach_audit': {
            'anti_patterns': [
                {
                    'pattern': 'Generic vendor pitches ("we work with all major carriers")',
                    'instead': 'Specific infrastructure challenges relevant to their vertical'
                },
                {
                    'pattern': 'Asking for meetings without value preview',
                    'instead': 'Leading with insight or assessment offer'
                }
            ],
            'kill_items': [
                {
                    'item': '"Free consultation" language',
                    'reason': 'Triggers skepticism, sounds like sales trap'
                },
                {
                    'item': 'Commission or referral fee mentions',
                    'reason': 'Too early—wait until interest established'
                }
            ]
        },
        'vertical_adaptations': {
            'healthcare': {
                'category_thesis_adaptation': 'Healthcare infrastructure procurement is uniquely complex due to HIPAA compliance, clinical uptime requirements, and evolving telehealth demands.',
                'maturity_model_emphasis': 'Emphasize compliance maturity and risk management in healthcare context.',
                'champion_profile': 'Healthcare CIOs and IT directors with patient care responsibility'
            },
            'financial_services': {
                'category_thesis_adaptation': 'Financial services face unique infrastructure challenges: regulatory compliance (SOX, PCI-DSS), low-latency trading requirements, and disaster recovery mandates.',
                'maturity_model_emphasis': 'Focus on risk management and business continuity maturity.',
                'champion_profile': 'CTOs and VPs of Technology with regulatory oversight'
            }
        }
    }


@pytest.fixture
def messaging_file(temp_dir, sample_messaging_data):
    file_path = temp_dir / "strategic-messaging.yaml"
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_messaging_data, f)
    return file_path


class TestLoad:
    def test_load_valid_file(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        data = loader.load()
        assert isinstance(data, dict)
        assert 'category_creation' in data
        assert 'intelligence_staging' in data

    def test_load_caches_data(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        data1 = loader.load()
        data2 = loader.load()
        assert data1 is data2  # Same object reference

    def test_load_missing_file(self, temp_dir):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="nonexistent.yaml"
        )
        data = loader.load()
        assert data == {}


class TestSectionAccessors:
    def test_get_framing_rules(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        rules = loader.get_framing_rules()
        assert isinstance(rules, list)
        assert len(rules) == 2
        assert rules[0]['rule'] == 'Never position as middleman or reseller'

    def test_get_intelligence_staging(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        staging = loader.get_intelligence_staging()
        assert isinstance(staging, dict)
        assert 'purpose' in staging
        assert 'levels' in staging

    def test_get_three_pillars(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        pillars = loader.get_three_pillars()
        assert isinstance(pillars, list)
        assert len(pillars) == 3
        assert pillars[0]['name'] == 'Independent Advisory'

    def test_get_maturity_model(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        model = loader.get_maturity_model()
        assert isinstance(model, dict)
        assert model['name'] == 'Infrastructure Procurement Maturity'

    def test_get_service_components(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        components = loader.get_service_components()
        assert isinstance(components, list)
        assert len(components) == 3

    def test_get_champion_requirements(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        champion = loader.get_champion_requirements()
        assert isinstance(champion, dict)
        assert 'requirements' in champion

    def test_get_operational_proof(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        proof = loader.get_operational_proof()
        assert isinstance(proof, list)
        assert len(proof) == 2

    def test_get_outreach_audit(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        audit = loader.get_outreach_audit()
        assert isinstance(audit, dict)
        assert 'anti_patterns' in audit

    def test_get_vertical_adaptation(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        adaptation = loader.get_vertical_adaptation('healthcare')
        assert isinstance(adaptation, dict)
        assert 'category_thesis_adaptation' in adaptation


class TestFormatForResearch:
    def test_format_includes_framing_rules(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_research()
        assert '## Strategic Framing Rules' in formatted
        assert 'Never position as middleman or reseller' in formatted

    def test_format_includes_intelligence_staging(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_research()
        assert '## Intelligence Staging' in formatted
        assert 'Never mention vendor payment model' in formatted

    def test_format_excludes_full_details(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_research()
        # Should NOT include full category creation
        assert 'Traditional IT procurement is broken' not in formatted


class TestFormatForPlaybook:
    def test_format_includes_category_creation(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_playbook()
        assert '## Category Creation Framework' in formatted
        assert 'Technology Infrastructure Advisory' in formatted

    def test_format_includes_pillars(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_playbook()
        assert '## Three Strategic Pillars' in formatted
        assert 'Independent Advisory' in formatted

    def test_format_includes_maturity_model(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_playbook()
        assert '## Maturity Model' in formatted
        assert 'Infrastructure Procurement Maturity' in formatted

    def test_format_with_vertical_adaptation(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_playbook(vertical='healthcare')
        assert 'Healthcare Messaging Adaptation' in formatted
        assert 'HIPAA compliance' in formatted


class TestFormatForValidation:
    def test_format_includes_outreach_audit(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_validation()
        assert '## Outreach Quality Requirements' in formatted
        assert 'Anti-Patterns to Avoid' in formatted

    def test_format_includes_full_intelligence_staging(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_validation()
        assert '## Intelligence Staging Framework' in formatted
        assert 'Level 1: Problem Awareness' in formatted

    def test_format_includes_forwardable_criteria(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_validation()
        assert 'Forwardable Content Criteria' in formatted
        assert 'Good (forwardable)' in formatted


class TestFormatForPrompt:
    def test_format_includes_full_category_creation(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_prompt()
        assert '## Category Creation Framework' in formatted
        assert 'Traditional IT procurement is broken' in formatted

    def test_format_includes_all_sections(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        formatted = loader.format_for_prompt()
        assert '## Category Creation Framework' in formatted
        assert '## Three Strategic Pillars' in formatted
        assert '## Maturity Model' in formatted
        assert '## Service Components' in formatted
        assert '## Intelligence Staging Framework' in formatted
        assert '## Champion Enablement Requirements' in formatted
        assert '## Operational Proof Narratives' in formatted
        assert '## Outreach Quality Requirements' in formatted


class TestScaffoldHandling:
    def test_scaffold_section_excluded(self, temp_dir):
        scaffold_data = {
            'category_creation': {
                'status': 'SCAFFOLD',
                'category_name': 'PLACEHOLDER',
                'category_thesis': 'PLACEHOLDER'
            },
            'three_pillars': {
                'pillars': [
                    {
                        'name': 'Real Pillar',
                        'description': 'Real description'
                    }
                ]
            }
        }
        file_path = temp_dir / "scaffold.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(scaffold_data, f)

        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="scaffold.yaml"
        )
        formatted = loader.format_for_playbook()
        assert '## Category Creation Framework' not in formatted
        assert '## Three Strategic Pillars' in formatted

    def test_placeholder_content_excluded(self, temp_dir):
        placeholder_data = {
            'three_pillars': {
                'pillars': [
                    {
                        'name': 'PLACEHOLDER',
                        'description': 'PLACEHOLDER'
                    }
                ]
            }
        }
        file_path = temp_dir / "placeholder.yaml"
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(placeholder_data, f)

        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="placeholder.yaml"
        )
        pillars = loader.get_three_pillars()
        assert pillars == []


class TestMissingFileHandling:
    def test_missing_file_returns_empty(self, temp_dir):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="missing.yaml"
        )
        formatted = loader.format_for_playbook()
        assert formatted == ""

    def test_missing_vertical_adaptation(self, temp_dir, messaging_file):
        loader = StrategicMessagingLoader(
            config_dir=temp_dir,
            file_path="strategic-messaging.yaml"
        )
        adaptation = loader.get_vertical_adaptation('nonexistent_vertical')
        assert adaptation == {}
