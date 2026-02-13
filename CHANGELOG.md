# Changelog

All notable changes to the UPSTACK Research System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- feat(context): Universal company context injection across all research layers
  - Layer 1, 2, and 3 agents now receive company context (previously GTM-only)
  - Added `{company_context_section}` placeholder to vertical and title prompt templates
  - Added `company_context: str = ""` parameter to `build_vertical_prompt()` and `build_title_prompt()`
  - Static CATEGORY FRAMING and UPSTACK DATA OVERRIDES sections in all Layer 1 horizontal templates
  - Prevents misframing UPSTACK as "vendor selection advisory" by injecting business model context early
  - Enabled by default via `company_context.enabled: true` in `defaults.yaml`

### Changed
- refactor(orchestrator): Removed GTM-only gate on company context loading
  - `_build_company_context()` now runs for all Layer 1 agents
  - Added company context wiring to `_execute_vertical_agent()` (with vertical param)
  - Added company context wiring to `_execute_title_agent()` (cross-vertical, no param)
- refactor(prompts): Standardized company context formatting across prompt builders
  - Vertical and title prompts now wrap context with `=== COMPANY CONTEXT ===` headers
  - Matches existing pattern from `playbook.py`

### Fixed
- fix(research-quality): Layer 1-3 agents no longer produce outputs with incorrect category framing
  - Research agents now understand UPSTACK's direct vendor competition model from the start
  - Outputs use UPSTACK data (verified metrics, retention, customer count) instead of generic benchmarks
  - Strategic recommendations align with established architecture rather than contradicting it
