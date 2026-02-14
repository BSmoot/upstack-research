#!/usr/bin/env python3
# run_target_research.py
"""
Standalone runner for target company research and alignment.

Usage:
    python run_target_research.py --config path/to/config.yaml
    python run_target_research.py --config path/to/config.yaml --research-only
    python run_target_research.py --prior-run <execution_id> --config path/to/config.yaml
"""

import argparse
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from research_orchestrator import ResearchOrchestrator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Target Company Research - Research and personalize for a specific prospect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Research target + run alignment on brand-aligned outputs
  python run_target_research.py --config ../build/config/projects/my_project.yaml

  # Research only — output target YAML, don't run alignment
  python run_target_research.py --config ../build/config/projects/my_project.yaml --research-only

  # Use prior run's outputs for alignment context
  python run_target_research.py --prior-run research_260214_1030 --config ../build/config/projects/my_project.yaml
        """
    )

    parser.add_argument(
        '--config',
        type=Path,
        required=True,
        help='Path to configuration YAML file'
    )

    parser.add_argument(
        '--research-only',
        action='store_true',
        help='Only run target research, output YAML, do not run alignment'
    )

    parser.add_argument(
        '--prior-run',
        type=str,
        help='Execution ID of a prior run to use as context for alignment'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without executing'
    )

    return parser.parse_args()


async def run_target_research_only(orchestrator: ResearchOrchestrator):
    """Run just the target research phase."""
    target_config = orchestrator.config.get('target_alignment', {})
    research_config = target_config.get('research', {})

    if not research_config.get('enabled', False):
        print("Error: target_alignment.research.enabled is not true in config")
        sys.exit(1)

    await orchestrator.execute_target_research()


async def run_target_research_and_alignment(orchestrator: ResearchOrchestrator):
    """Run target research followed by target alignment."""
    target_config = orchestrator.config.get('target_alignment', {})

    if not target_config.get('enabled', False):
        print("Error: target_alignment.enabled is not true in config")
        sys.exit(1)

    # Run research if enabled
    research_config = target_config.get('research', {})
    if research_config.get('enabled', False):
        orchestrator.logger.info("\n" + "=" * 80)
        orchestrator.logger.info("TARGET RESEARCH: Researching Target Company")
        orchestrator.logger.info("=" * 80)
        await orchestrator.execute_target_research()

    # Run alignment
    orchestrator.logger.info("\n" + "=" * 80)
    orchestrator.logger.info("TARGET ALIGNMENT: Personalizing for Target Company")
    orchestrator.logger.info("=" * 80)
    await orchestrator.execute_target_alignment()


def main():
    """Main entry point."""
    load_dotenv()
    args = parse_args()

    if not args.config.exists():
        print(f"Error: Configuration file not found: {args.config}")
        sys.exit(1)

    try:
        # Initialize orchestrator
        execution_id = args.prior_run if args.prior_run else None
        print(f"Loading configuration: {args.config}")
        if execution_id:
            print(f"Using prior run: {execution_id}")

        orchestrator = ResearchOrchestrator(
            config_path=args.config,
            execution_id=execution_id
        )

        # Dry run
        if args.dry_run:
            target_config = orchestrator.config.get('target_alignment', {})
            research_config = target_config.get('research', {})
            seed = research_config.get('seed', {})

            print("\nConfiguration valid!")
            print(f"Execution ID: {orchestrator.state.execution_id}")
            print(f"Target alignment enabled: {target_config.get('enabled', False)}")
            print(f"Target research enabled: {research_config.get('enabled', False)}")
            if seed:
                print(f"Research seed:")
                print(f"  Name: {seed.get('name', 'N/A')}")
                print(f"  Industry: {seed.get('industry', 'N/A')}")
                print(f"  Size: {seed.get('size', 'N/A')}")
                print(f"  Location: {seed.get('location', 'N/A')}")
            print(f"Output Directory: {orchestrator.output_dir}")
            return

        # Execute
        if args.research_only:
            asyncio.run(run_target_research_only(orchestrator))
        else:
            asyncio.run(run_target_research_and_alignment(orchestrator))

        print("\n" + "=" * 80)
        print("TARGET RESEARCH COMPLETE")
        print("=" * 80)
        print(f"\nOutputs saved to: {orchestrator.output_dir}")
        print(f"Checkpoint saved to: {orchestrator.state.checkpoint_file}")

    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        print("Progress has been saved to checkpoint file")
        sys.exit(0)

    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
