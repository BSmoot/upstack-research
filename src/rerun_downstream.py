#!/usr/bin/env python3
"""
Re-run downstream stages (playbooks, validation, brand alignment) using
existing layer 0-3 outputs from a prior run.

Usage:
    python rerun_downstream.py --prior-run e2e_healthcare_cio_network_260213_2017 \
        --config ../build/config/projects/e2e_healthcare_cio_network.yaml
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from research_orchestrator import ResearchOrchestrator


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Re-run playbooks + validation + brand alignment from prior layer 0-3 outputs"
    )
    parser.add_argument('--prior-run', required=True, help='Execution ID of prior run to reuse layers 0-3 from')
    parser.add_argument('--config', type=Path, required=True, help='Config YAML file')
    args = parser.parse_args()

    if not args.config.exists():
        print(f"Error: Config not found: {args.config}")
        sys.exit(1)

    # Load prior checkpoint
    prior_checkpoint = Path(f"checkpoints/{args.prior_run}.json")
    if not prior_checkpoint.exists():
        print(f"Error: Prior checkpoint not found: {prior_checkpoint}")
        sys.exit(1)

    with open(prior_checkpoint, 'r') as f:
        prior_state = json.load(f)

    # Verify layers 0-3 are complete
    for layer in ['layer_0', 'layer_1', 'layer_2', 'layer_3']:
        layer_data = prior_state.get(layer, {})
        for agent_name, agent_data in layer_data.items():
            if agent_data.get('status') != 'complete':
                print(f"Error: {agent_name} in {layer} is not complete in prior run")
                sys.exit(1)

    # Create new orchestrator (gets a fresh timestamped execution)
    print(f"Loading configuration: {args.config}")
    orchestrator = ResearchOrchestrator(config_path=args.config)

    print(f"New execution ID: {orchestrator.state.execution_id}")
    print(f"Outputs will go to: {orchestrator.output_dir}")
    print(f"Reusing layer 0-3 from: {args.prior_run}")

    # Inject prior layer 0-3 state into the new state tracker
    for layer in ['layer_0', 'layer_1', 'layer_2', 'layer_3']:
        orchestrator.state.state[layer] = prior_state[layer]

    # Save the merged state
    orchestrator.state._save_state()

    print("\nLayer 0-3 state injected from prior run.")
    print("Starting downstream stages: Playbooks -> Validation -> Brand Alignment\n")

    async def run_downstream():
        # Playbooks
        print("=" * 80)
        print("INTEGRATION: Generating Playbooks")
        print("=" * 80)
        await orchestrator.generate_playbooks_parallel()

        # Validation
        validation_enabled = orchestrator.config['execution_settings'].get('validation', {}).get('enabled', True)
        if validation_enabled:
            print("\n" + "=" * 80)
            print("VALIDATION: Quality Gate Assessment")
            print("=" * 80)
            await orchestrator.execute_validation()

        # Brand Alignment
        brand_config = orchestrator.config.get('brand_alignment', {})
        if brand_config.get('enabled', False):
            print("\n" + "=" * 80)
            print("BRAND ALIGNMENT: Aligning Outputs")
            print("=" * 80)
            await orchestrator.execute_brand_alignment()

    try:
        asyncio.run(run_downstream())
        print("\n" + "=" * 80)
        print("DOWNSTREAM RE-RUN COMPLETE")
        print("=" * 80)
        print(f"\nOutputs saved to: {orchestrator.output_dir}")
        print(f"Checkpoint: {orchestrator.state.checkpoint_file}")
    except KeyboardInterrupt:
        print("\n\nInterrupted. Progress saved to checkpoint.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
