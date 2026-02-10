"""
Standalone test script: Run brand enrichment on an existing playbook.

Usage:
    cd src
    python test_enrichment.py

Reads the existing e2e_minimal_test playbook, loads brand context + brand assets,
builds the enrichment prompt, calls the Anthropic API with Sonnet, and saves output
alongside the existing brand_alignment output for comparison.

Requires ANTHROPIC_API_KEY in environment or .env file at project root.
"""

import asyncio
import os
import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from research_orchestrator.utils.brand_context import BrandContextLoader
from research_orchestrator.utils.brand_assets import BrandAssetsLoader
from research_orchestrator.prompts.brand_alignment import build_brand_alignment_prompt
from research_orchestrator.research_session import ResearchSession


# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "build" / "config" / "projects"

# Input: existing playbook from the e2e_minimal_test run
PLAYBOOK_PATH = PROJECT_ROOT / "outputs" / "e2e_minimal_test" / "playbooks" / "playbook_healthcare_cio_cto_cluster.md"

# Brand context files (same paths as e2e_minimal_test.yaml config)
CONTEXT_FILES = {
    "baseline": "../../../research-manager/context/baseline.yaml",
    "writing_standards": "../../../research-manager/context/writing-standards.yaml",
    "audience_personas": "../../../research-manager/context/audience-personas.yaml",
    "glossary": "../../../research-manager/context/glossary.yaml",
}

# Brand assets file
ASSETS_FILE = "../../../research-manager/context/brand-assets.yaml"

# Output: save alongside existing outputs for comparison
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "e2e_minimal_test" / "brand_alignment" / "enrichment_test_healthcare_cio_cto_cluster.md"

# Model: Sonnet (matches updated config)
MODEL = "claude-sonnet-4-5-20250929"

# Playbook context for filtering assets
VERTICAL = "healthcare"
SERVICE_CATEGORY = "security"


def setup_logging() -> logging.Logger:
    """Configure logging for the test script."""
    logger = logging.getLogger("enrichment_test")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


async def run_enrichment_test() -> None:
    """Run the brand enrichment test against the existing playbook."""
    logger = setup_logging()

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    # Validate playbook exists
    if not PLAYBOOK_PATH.exists():
        logger.error("Playbook not found: %s", PLAYBOOK_PATH)
        raise FileNotFoundError(f"Playbook not found: {PLAYBOOK_PATH}")

    logger.info("Loading playbook from %s", PLAYBOOK_PATH)
    with open(PLAYBOOK_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()
    logger.info("Playbook loaded: %d characters", len(original_content))

    # Load brand context
    logger.info("Loading brand context files...")
    brand_context_loader = BrandContextLoader(
        config_dir=CONFIG_DIR,
        context_files=CONTEXT_FILES,
        logger=logger
    )
    brand_context_data = brand_context_loader.load_all()
    brand_context_formatted = brand_context_loader.format_for_prompt(brand_context_data)
    logger.info("Brand context formatted: %d characters", len(brand_context_formatted))

    # Load brand assets (filtered for healthcare + security)
    logger.info("Loading brand assets (vertical=%s, service_category=%s)...", VERTICAL, SERVICE_CATEGORY)
    brand_assets_loader = BrandAssetsLoader(
        config_dir=CONFIG_DIR,
        file_path=ASSETS_FILE,
        logger=logger
    )
    assets_data = brand_assets_loader.load()
    if not assets_data:
        logger.error("Brand assets file is empty or missing")
        raise FileNotFoundError("Brand assets data could not be loaded")

    brand_assets_formatted = brand_assets_loader.format_for_prompt(
        context=assets_data,
        vertical=VERTICAL,
        service_category=SERVICE_CATEGORY
    )
    logger.info("Brand assets formatted: %d characters", len(brand_assets_formatted))

    # Build the enrichment prompt
    prompt = build_brand_alignment_prompt(
        original_content=original_content,
        brand_context=brand_context_formatted,
        brand_assets=brand_assets_formatted
    )
    logger.info("Enrichment prompt built: %d characters", len(prompt))

    # Execute via ResearchSession
    logger.info("Starting enrichment session with model: %s", MODEL)
    client = AsyncAnthropic(api_key=api_key)

    session = ResearchSession(
        agent_name="enrichment_test_healthcare_security",
        anthropic_client=client,
        model=MODEL,
        max_tokens=16000,
        max_searches=1,  # No search needed for enrichment
        logger=logger
    )

    start_time = time.time()
    result = await session.execute_research(
        prompt=prompt,
        context={"original_content": original_content},
        max_turns=5
    )
    elapsed = time.time() - start_time

    # Report results
    logger.info("Enrichment complete in %.1f seconds", elapsed)
    logger.info("  Status: %s", result.get("completion_status", "unknown"))
    logger.info("  Turns: %d", result.get("total_turns", 0))
    logger.info("  Cost: $%.4f", result.get("estimated_cost_usd", 0))

    # Check for errors
    if result.get("completion_status") == "error":
        logger.error("Enrichment session ended in error")
        logger.error("Result: %s", result)
        return

    # Save output
    deliverables = result.get("deliverables", "")
    if not deliverables:
        logger.error("No deliverables produced")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(deliverables)

    logger.info("Enriched output saved to: %s", OUTPUT_PATH)
    logger.info("Output size: %d characters", len(deliverables))
    logger.info("")
    logger.info("Compare outputs:")
    logger.info("  Original playbook:  %s", PLAYBOOK_PATH)
    logger.info("  Old brand alignment: %s",
                PROJECT_ROOT / "outputs" / "e2e_minimal_test" / "brand_alignment" / "align_playbook_healthcare_cio_cto_cluster.md")
    logger.info("  New enrichment:      %s", OUTPUT_PATH)


if __name__ == "__main__":
    # Load .env from project root (same pattern as run_research.py)
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
    asyncio.run(run_enrichment_test())
