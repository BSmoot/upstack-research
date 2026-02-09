# research_orchestrator/state/tracker.py
"""
StateTracker - Manages research execution state and dependencies.

Enables checkpoint/resume capability and tracks layer dependencies.
"""

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime


class StateTracker:
    """
    Tracks research execution state.
    Enables resume after interruption.
    Manages layer dependencies.
    """
    
    def __init__(
        self,
        checkpoint_dir: Path,
        execution_id: str | None = None,
        logger: logging.Logger | None = None
    ):
        """
        Initialize state tracker.
        
        Args:
            checkpoint_dir: Directory for checkpoint files
            execution_id: Optional execution ID (generated if not provided)
            logger: Optional logger instance
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.execution_id = execution_id or self._generate_execution_id()
        self.checkpoint_file = self.checkpoint_dir / f"{self.execution_id}.json"
        
        self.logger = logger or logging.getLogger(__name__)
        
        # Load existing state or initialize new
        self.state = self.load_or_initialize()
    
    def _generate_execution_id(self) -> str:
        """Generate execution ID with timestamp."""
        return f"research_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    def load_or_initialize(self) -> dict[str, Any]:
        """Load existing checkpoint or initialize new state."""
        if self.checkpoint_file.exists():
            self.logger.info(f"Loading checkpoint from: {self.checkpoint_file}")
            try:
                with open(self.checkpoint_file, 'r') as f:
                    state = json.load(f)
                    # Backward compatibility: add missing keys
                    if 'layer_0' not in state:
                        state['layer_0'] = {}
                    if 'validation' not in state:
                        state['validation'] = {}
                    if 'target_alignment' not in state:
                        state['target_alignment'] = {}
                    return state
            except Exception as e:
                self.logger.error(f"Failed to load checkpoint: {e}")
                self.logger.info("Initializing new state")
        
        # Initialize new state
        state = {
            "execution_id": self.execution_id,
            "started_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "layer_0": {},
            "layer_1": {
                "buyer_journey": {"status": "pending"},
                "channels_competitive": {"status": "pending"},
                "customer_expansion": {"status": "pending"},
                "messaging_positioning": {"status": "pending"},
                "gtm_synthesis": {"status": "pending"}
            },
            "layer_2": {},
            "layer_3": {},
            "integrations": {},
            "validation": {},
            "brand_alignment": {},
            "target_alignment": {}
        }
        
        self._save_state(state)
        return state
    
    def _save_state(self, state: dict[str, Any] | None = None):
        """Save current state to checkpoint file with atomic write."""
        import tempfile
        import os
        
        if state is None:
            state = self.state
        
        state["last_updated"] = datetime.utcnow().isoformat()
        
        try:
            # Atomic write: tmp file + rename
            with tempfile.NamedTemporaryFile('w', delete=False, 
                                             dir=self.checkpoint_dir,
                                             suffix='.json.tmp') as tmp:
                json.dump(state, tmp, indent=2)
                tmp_path = tmp.name
            
            # Atomic rename
            os.replace(tmp_path, self.checkpoint_file)
            self.logger.debug(f"Checkpoint saved: {self.checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            # Cleanup temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except OSError as cleanup_error:
                    self.logger.warning(f"Failed to cleanup temp file {tmp_path}: {cleanup_error}")
    
    def is_agent_complete(self, agent_name: str) -> bool:
        """
        Check if specific agent has completed.

        Args:
            agent_name: Name of the agent to check

        Returns:
            True if agent status is 'complete'
        """
        # Check in all layers
        for layer_name in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'integrations', 'validation', 'brand_alignment', 'target_alignment']:
            layer = self.state.get(layer_name, {})
            if agent_name in layer:
                return layer[agent_name].get('status') == 'complete'

        return False
    
    def can_execute_layer_2(self, vertical: str) -> bool:
        """
        Check if Layer 0 and Layer 1 dependencies are met for Layer 2 execution.

        Args:
            vertical: Vertical name to check

        Returns:
            True if all Layer 1 agents are complete (Layer 0 is optional)
        """
        # Layer 0 is optional, check if configured
        layer_0_agents = list(self.state.get('layer_0', {}).keys())
        if layer_0_agents:
            for agent in layer_0_agents:
                if not self.is_agent_complete(agent):
                    self.logger.debug(
                        f"Layer 2 ({vertical}) blocked: {agent} not complete"
                    )
                    return False

        # Layer 1 is required
        layer_1_agents = [
            'buyer_journey',
            'channels_competitive',
            'customer_expansion',
            'messaging_positioning',
            'gtm_synthesis'
        ]

        for agent in layer_1_agents:
            if not self.is_agent_complete(agent):
                self.logger.debug(
                    f"Layer 2 ({vertical}) blocked: {agent} not complete"
                )
                return False

        return True
    
    def can_execute_layer_3(self, title_cluster: str, vertical: str | None = None) -> bool:
        """
        Check if Layer 1 + Layer 2 dependencies are met for Layer 3 execution.
        
        Args:
            title_cluster: Title cluster name to check
            vertical: Optional specific vertical dependency
            
        Returns:
            True if dependencies are met
        """
        # First check Layer 1 completion
        if not self.can_execute_layer_2("_check"):
            return False
        
        # If specific vertical provided, check it
        if vertical:
            vertical_key = f"vertical_{vertical}"
            if not self.is_agent_complete(vertical_key):
                self.logger.debug(
                    f"Layer 3 ({title_cluster}) blocked: {vertical_key} not complete"
                )
                return False
        
        return True
    
    def mark_complete(
        self,
        agent_name: str,
        outputs: dict[str, Any],
        layer: str = "layer_1"
    ):
        """
        Record agent completion and save checkpoint.
        
        Args:
            agent_name: Name of the agent
            outputs: Agent output data
            layer: Layer name (layer_1, layer_2, layer_3, integrations)
        """
        self.logger.info(f"Marking {agent_name} as complete")
        
        # Ensure layer exists
        if layer not in self.state:
            self.state[layer] = {}
        
        # Update agent status
        self.state[layer][agent_name] = {
            "status": "complete",
            "completed_at": datetime.utcnow().isoformat(),
            **outputs
        }
        
        # Save checkpoint
        self._save_state()
        
        self.logger.info(f"Checkpoint saved for {agent_name}")
    
    def mark_in_progress(self, agent_name: str, layer: str = "layer_1"):
        """Mark agent as in progress."""
        if layer not in self.state:
            self.state[layer] = {}
        
        if agent_name not in self.state[layer]:
            self.state[layer][agent_name] = {}
        
        self.state[layer][agent_name]["status"] = "in_progress"
        self.state[layer][agent_name]["started_at"] = datetime.utcnow().isoformat()
        
        self._save_state()
    
    def mark_failed(
        self,
        agent_name: str,
        error: str,
        layer: str = "layer_1"
    ):
        """Mark agent as failed."""
        if layer not in self.state:
            self.state[layer] = {}

        if agent_name not in self.state[layer]:
            self.state[layer][agent_name] = {}

        self.state[layer][agent_name]["status"] = "failed"
        self.state[layer][agent_name]["failed_at"] = datetime.utcnow().isoformat()
        self.state[layer][agent_name]["error"] = error

        self._save_state()

    def mark_for_rerun(self, agent_name: str, layer: str | None = None) -> bool:
        """
        Mark a completed agent for re-execution by resetting its status to pending.

        Used with --force flag to re-run agents that have already completed.
        Preserves prior run metadata in 'prior_runs' history.

        Args:
            agent_name: Name of the agent to reset
            layer: Layer to search in (if None, searches all layers)

        Returns:
            True if agent was found and reset, False otherwise
        """
        # Find the agent in layers
        target_layer = None
        if layer:
            if layer in self.state and agent_name in self.state[layer]:
                target_layer = layer
        else:
            for layer_name in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'integrations', 'validation', 'brand_alignment', 'target_alignment']:
                if layer_name in self.state and agent_name in self.state[layer_name]:
                    target_layer = layer_name
                    break

        if not target_layer:
            self.logger.warning(f"Agent {agent_name} not found for rerun")
            return False

        agent_data = self.state[target_layer][agent_name]

        # Only reset if currently complete
        if agent_data.get('status') != 'complete':
            self.logger.info(f"Agent {agent_name} is not complete (status: {agent_data.get('status')}), skipping reset")
            return False

        # Preserve prior run in history
        prior_runs = agent_data.get('prior_runs', [])
        prior_run_record = {
            'completed_at': agent_data.get('completed_at'),
            'output_path': agent_data.get('output_path'),
            'searches_performed': agent_data.get('searches_performed'),
            'total_turns': agent_data.get('total_turns'),
            'execution_time_seconds': agent_data.get('execution_time_seconds'),
            'reset_at': datetime.utcnow().isoformat()
        }
        prior_runs.append(prior_run_record)

        # Reset to pending while preserving history
        self.state[target_layer][agent_name] = {
            'status': 'pending',
            'prior_runs': prior_runs
        }

        self.logger.info(f"Agent {agent_name} marked for rerun (prior runs: {len(prior_runs)})")
        self._save_state()
        return True

    def save_checkpoint_history(self) -> Path | None:
        """
        Save a timestamped copy of the current checkpoint before modification.

        Returns:
            Path to the saved history file, or None if save failed
        """
        history_dir = self.checkpoint_dir / 'history'
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        history_file = history_dir / f"{self.execution_id}_{timestamp}.json"

        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
            self.logger.info(f"Checkpoint history saved: {history_file}")
            return history_file
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint history: {e}")
            return None
    
    def get_agent_output(self, agent_name: str, layer: str | None = None) -> dict[str, Any] | None:
        """
        Retrieve complete output for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., 'buyer_journey', 'vertical_healthcare')
            layer: Optional layer name to search in. If not provided, searches all layers.

        Returns:
            Agent output dictionary or None if not found
        """
        if layer:
            # Search in specific layer
            layer_data = self.state.get(layer, {})
            return layer_data.get(agent_name)

        # Search in all layers
        for layer_name in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'integrations', 'validation', 'brand_alignment', 'target_alignment']:
            layer_data = self.state.get(layer_name, {})
            if agent_name in layer_data:
                return layer_data[agent_name]

        return None
    
    def get_context_for_agent(self, agent_name: str) -> dict[str, Any]:
        """
        Retrieve all prior outputs needed by this agent.

        Args:
            agent_name: Name of the agent requesting context

        Returns:
            Dictionary of prior agent outputs
        """
        context = {}

        # For Layer 1 agents, include Layer 0 if available
        if agent_name in ['buyer_journey', 'channels_competitive', 'customer_expansion']:
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data

        # For Layer 1 agents with dependencies
        if agent_name == 'messaging_positioning':
            # Needs buyer_journey, channels_competitive, customer_expansion
            for dep in ['buyer_journey', 'channels_competitive', 'customer_expansion']:
                if dep in self.state.get('layer_1', {}):
                    context[dep] = self.state['layer_1'][dep]
            # Also include Layer 0 if available
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data

        elif agent_name == 'gtm_synthesis':
            # Needs all prior Layer 1 agents
            for dep in ['buyer_journey', 'channels_competitive', 'customer_expansion', 'messaging_positioning']:
                if dep in self.state.get('layer_1', {}):
                    context[dep] = self.state['layer_1'][dep]
            # Also include Layer 0 if available
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data

        # For Layer 2 agents, provide Layer 0 + Layer 1 context
        elif agent_name.startswith('vertical_'):
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data
            context['layer_1'] = self.state.get('layer_1', {})

        # For Layer 3 agents, provide Layer 0 + Layer 1 + Layer 2
        elif agent_name.startswith('title_'):
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data
            context['layer_1'] = self.state.get('layer_1', {})
            context['layer_2'] = self.state.get('layer_2', {})

        # For integration, provide all layers
        elif agent_name.startswith('playbook_'):
            layer_0_data = self.state.get('layer_0', {})
            if layer_0_data:
                context['layer_0'] = layer_0_data
            context['layer_1'] = self.state.get('layer_1', {})
            context['layer_2'] = self.state.get('layer_2', {})
            context['layer_3'] = self.state.get('layer_3', {})

        # For brand alignment agents, provide original content
        elif agent_name.startswith('align_'):
            # Extract original file path from agent name (e.g., align_playbook_healthcare_cfo)
            original_name = agent_name.replace('align_', '')
            context['original_content'] = self.state.get('integrations', {}).get(original_name, {})

        return context
    
    def get_pending_agents(self, layer: str = "layer_1") -> list[str]:
        """Get list of pending agents in a layer."""
        layer_data = self.state.get(layer, {})
        return [
            agent_name 
            for agent_name, data in layer_data.items()
            if data.get('status') == 'pending'
        ]
    
    def get_layer_status(self, layer: str = "layer_1") -> dict[str, int]:
        """Get status counts for a layer."""
        layer_data = self.state.get(layer, {})
        
        status_counts = {
            'total': len(layer_data),
            'pending': 0,
            'in_progress': 0,
            'complete': 0,
            'failed': 0
        }
        
        for agent_data in layer_data.values():
            status = agent_data.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1
        
        return status_counts
    
    def is_layer_complete(self, layer: str = "layer_1") -> bool:
        """Check if all agents in a layer are complete."""
        status = self.get_layer_status(layer)
        return status['complete'] == status['total'] and status['total'] > 0
    
    def initialize_layer_0(self, service_categories: list[str]):
        """Initialize Layer 0 state with service category names."""
        for category in service_categories:
            agent_name = f"service_category_{category}"
            if agent_name not in self.state['layer_0']:
                self.state['layer_0'][agent_name] = {"status": "pending"}

        self._save_state()

    def initialize_layer_2(self, verticals: list[str]):
        """Initialize Layer 2 state with vertical names."""
        for vertical in verticals:
            agent_name = f"vertical_{vertical}"
            if agent_name not in self.state['layer_2']:
                self.state['layer_2'][agent_name] = {"status": "pending"}

        self._save_state()
    
    def initialize_layer_3(self, title_clusters: list[str]):
        """Initialize Layer 3 state with title cluster names."""
        for title in title_clusters:
            agent_name = f"title_{title}"
            if agent_name not in self.state['layer_3']:
                self.state['layer_3'][agent_name] = {"status": "pending"}
        
        self._save_state()
    
    def initialize_integrations(self, combinations: list[tuple]):
        """Initialize integration state with vertical x title combinations."""
        for vertical, title in combinations:
            agent_name = f"playbook_{vertical}_{title}"
            if agent_name not in self.state['integrations']:
                self.state['integrations'][agent_name] = {"status": "pending"}

        self._save_state()

    def initialize_integrations_3d(self, agent_names: list[str]):
        """
        Initialize integration state for 3D playbooks (V × T × SC).

        Args:
            agent_names: List of agent names (e.g., ['playbook_healthcare_cfo_security', ...])
        """
        for agent_name in agent_names:
            if agent_name not in self.state['integrations']:
                self.state['integrations'][agent_name] = {"status": "pending"}

        self._save_state()

    def initialize_validation(self, agent_names: list[str]):
        """Initialize validation state with agent names."""
        if 'validation' not in self.state:
            self.state['validation'] = {}

        for agent_name in agent_names:
            if agent_name not in self.state['validation']:
                self.state['validation'][agent_name] = {"status": "pending"}

        self._save_state()

    def initialize_brand_alignment(self, agent_names: list[str]):
        """Initialize brand alignment state with agent names."""
        for agent_name in agent_names:
            if agent_name not in self.state['brand_alignment']:
                self.state['brand_alignment'][agent_name] = {"status": "pending"}

        self._save_state()

    def initialize_target_alignment(self, agent_names: list[str]):
        """Initialize target alignment state with agent names."""
        if 'target_alignment' not in self.state:
            self.state['target_alignment'] = {}

        for agent_name in agent_names:
            if agent_name not in self.state['target_alignment']:
                self.state['target_alignment'][agent_name] = {"status": "pending"}

        self._save_state()

    def get_execution_summary(self) -> dict[str, Any]:
        """Get overall execution summary."""
        return {
            'execution_id': self.execution_id,
            'started_at': self.state.get('started_at'),
            'last_updated': self.state.get('last_updated'),
            'layer_0_status': self.get_layer_status('layer_0'),
            'layer_1_status': self.get_layer_status('layer_1'),
            'layer_2_status': self.get_layer_status('layer_2'),
            'layer_3_status': self.get_layer_status('layer_3'),
            'integration_status': self.get_layer_status('integrations'),
            'validation_status': self.get_layer_status('validation'),
            'brand_alignment_status': self.get_layer_status('brand_alignment'),
            'target_alignment_status': self.get_layer_status('target_alignment'),
            'checkpoint_file': str(self.checkpoint_file)
        }
