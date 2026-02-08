#!/usr/bin/env python3
# run_research.py
"""
Command-line interface for Research Orchestrator.

Usage:
    python run_research.py --config path/to/config.yaml
    python run_research.py --resume execution_id --config path/to/config.yaml
    python run_research.py --layer 1 --config path/to/config.yaml
    python run_research.py --layer 0 --config path/to/config.yaml
    python run_research.py --layer 2 --verticals healthcare --config path/to/config.yaml
    python run_research.py --layer 3 --titles cfo_cluster --config path/to/config.yaml
    python run_research.py --layer 0 --service-categories security --config path/to/config.yaml
    python run_research.py --layer 2 --verticals healthcare --force --config path/to/config.yaml
    python run_research.py --agents buyer_journey --config path/to/config.yaml
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
        description="Research Orchestrator - AI-powered market research system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start new research program
  python run_research.py --config ../build/design/251002_initial_design/research_config.yaml

  # Resume interrupted research
  python run_research.py --resume research_20251002_170000

  # Run specific layer only
  python run_research.py --layer 1 --config path/to/config.yaml

  # Run specific agents only
  python run_research.py --agents buyer_journey,channels_competitive --config path/to/config.yaml

  # Run Layer 0 (service category research) only
  python run_research.py --layer 0 --config path/to/config.yaml

  # Run specific verticals in Layer 2
  python run_research.py --layer 2 --verticals healthcare,financial_services --config path/to/config.yaml

  # Run specific titles in Layer 3
  python run_research.py --layer 3 --titles cfo_cluster,cio_cto_cluster --config path/to/config.yaml

  # Run specific service categories in Layer 0
  python run_research.py --layer 0 --service-categories security,cloud --config path/to/config.yaml

  # Force re-run of completed agents
  python run_research.py --layer 2 --verticals healthcare --force --config path/to/config.yaml
        """
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration YAML file'
    )
    
    parser.add_argument(
        '--resume',
        type=str,
        help='Resume from checkpoint with execution ID'
    )
    
    parser.add_argument(
        '--layer',
        type=int,
        choices=[0, 1, 2, 3],
        help='Execute specific layer only (0=service categories, 1=horizontal, 2=vertical, 3=title)'
    )
    
    parser.add_argument(
        '--agents',
        type=str,
        help='Comma-separated list of specific agents to run (e.g., buyer_journey,channels_competitive)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without executing'
    )

    parser.add_argument(
        '--verticals',
        type=str,
        help='Comma-separated verticals to run in Layer 2 (e.g., healthcare,financial_services)'
    )

    parser.add_argument(
        '--titles',
        type=str,
        help='Comma-separated title clusters to run in Layer 3 (e.g., cfo_cluster,cio_cto_cluster)'
    )

    parser.add_argument(
        '--service-categories',
        type=str,
        help='Comma-separated service categories to run in Layer 0 (e.g., security,cloud)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-run of completed agents (even if already in checkpoint)'
    )

    return parser.parse_args()


async def run_full_research(orchestrator: ResearchOrchestrator):
    """Run full three-layer research program."""
    await orchestrator.execute_full_research()


async def run_layer(orchestrator: ResearchOrchestrator, layer: int):
    """Run specific layer only."""
    if layer == 0:
        await orchestrator.execute_layer_0_parallel()
    elif layer == 1:
        await orchestrator.execute_layer_1_parallel()
    elif layer == 2:
        await orchestrator.execute_layer_2_parallel()
    elif layer == 3:
        await orchestrator.execute_layer_3_parallel()


async def run_specific_agents(orchestrator: ResearchOrchestrator, agent_names: list):
    """Run specific agents only."""
    orchestrator.logger.info(f"Running specific agents: {', '.join(agent_names)}")
    
    tasks = []
    for agent_name in agent_names:
        if not orchestrator.state.is_agent_complete(agent_name):
            tasks.append(orchestrator._execute_agent(agent_name, layer='layer_1'))
        else:
            orchestrator.logger.info(f"Skipping {agent_name} (already complete)")
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    orchestrator.logger.info("Specified agents complete!")


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Validate arguments
    if not args.config and not args.resume:
        print("Error: Must provide either --config or --resume")
        sys.exit(1)
    
    if args.resume and args.agents:
        print("Error: --resume cannot be used with --agents")
        sys.exit(1)

    # --resume with --layer IS allowed (e.g., Phase 2 using Phase 1 checkpoint)

    # Selective flag validation
    if args.verticals and args.layer != 2:
        print("Error: --verticals requires --layer 2")
        sys.exit(1)

    if args.titles and args.layer != 3:
        print("Error: --titles requires --layer 3")
        sys.exit(1)

    if args.service_categories and args.layer != 0:
        print("Error: --service-categories requires --layer 0")
        sys.exit(1)

    try:
        # Initialize orchestrator
        if args.resume:
            if not args.config:
                print("Error: --config is required when using --resume")
                sys.exit(1)

            config_path = args.config
            if not config_path.exists():
                print(f"Error: Configuration file not found: {config_path}")
                sys.exit(1)

            print(f"Resuming execution: {args.resume}")
            print(f"Loading configuration: {config_path}")

            orchestrator = ResearchOrchestrator(
                config_path=config_path,
                execution_id=args.resume
            )
        else:
            config_path = args.config
            if not config_path.exists():
                print(f"Error: Configuration file not found: {config_path}")
                sys.exit(1)

            print(f"Loading configuration: {config_path}")
            orchestrator = ResearchOrchestrator(config_path=config_path)

        # Process --force flag
        if args.force:
            force_agents = []
            if args.service_categories:
                for cat in [c.strip() for c in args.service_categories.split(',')]:
                    force_agents.append(f"service_category_{cat}")
            elif args.verticals:
                for v in [v.strip() for v in args.verticals.split(',')]:
                    force_agents.append(f"vertical_{v}")
            elif args.titles:
                for t in [t.strip() for t in args.titles.split(',')]:
                    force_agents.append(f"title_{t}")
            elif args.layer is not None:
                # Force all agents in specified layer
                if args.layer == 0:
                    for cat in orchestrator.config.get('service_categories', []):
                        force_agents.append(f"service_category_{cat}")
                elif args.layer == 1:
                    # Layer 1 agents are fixed
                    force_agents.extend([
                        'buyer_journey', 'channels_competitive',
                        'customer_expansion', 'messaging_positioning',
                        'gtm_synthesis'
                    ])
                elif args.layer == 2:
                    for v in orchestrator.config['verticals']:
                        force_agents.append(f"vertical_{v}")
                elif args.layer == 3:
                    for t in orchestrator.config['title_clusters']:
                        force_agents.append(f"title_{t}")

            if force_agents:
                orchestrator.force_agents = force_agents
                orchestrator._process_force_agents()

        # Dry run - just validate config
        if args.dry_run:
            print("\nConfiguration valid!")
            print(f"Execution ID: {orchestrator.state.execution_id}")
            print(f"Verticals: {', '.join(orchestrator.config['verticals'])}")
            print(f"Title Clusters: {', '.join(orchestrator.config['title_clusters'])}")
            if orchestrator.config.get('service_categories'):
                print(f"Service Categories: {', '.join(orchestrator.config['service_categories'])}")
            print(f"Output Directory: {orchestrator.output_dir}")
            print(f"Checkpoint Directory: {orchestrator.state.checkpoint_dir}")
            return
        
        # Execute based on arguments
        if args.agents:
            # Run specific agents
            agent_names = [name.strip() for name in args.agents.split(',')]
            asyncio.run(run_specific_agents(orchestrator, agent_names))

        elif args.verticals or args.titles or args.service_categories:
            # Selective execution within a layer
            if args.verticals:
                selected = [v.strip() for v in args.verticals.split(',')]
                orchestrator.config['verticals'] = selected
                asyncio.run(run_layer(orchestrator, 2))
            elif args.titles:
                selected = [t.strip() for t in args.titles.split(',')]
                orchestrator.config['title_clusters'] = selected
                asyncio.run(run_layer(orchestrator, 3))
            elif args.service_categories:
                selected = [c.strip() for c in args.service_categories.split(',')]
                orchestrator.config['service_categories'] = selected
                asyncio.run(run_layer(orchestrator, 0))

        elif args.layer is not None:
            # Run specific layer
            asyncio.run(run_layer(orchestrator, args.layer))

        else:
            # Run full research program
            asyncio.run(run_full_research(orchestrator))
        
        print("\n" + "=" * 80)
        print("RESEARCH EXECUTION COMPLETE")
        print("=" * 80)
        print(f"\nOutputs saved to: {orchestrator.output_dir}")
        print(f"Checkpoint saved to: {orchestrator.state.checkpoint_file}")
        print("\nNext steps:")
        print("1. Review outputs in the outputs directory")
        print("2. Test messaging with prospects")
        print("3. Iterate based on market feedback")
        
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        print("Progress has been saved to checkpoint file")
        print("Resume with: python run_research.py --resume <execution_id> --config <path>")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
