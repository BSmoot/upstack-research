"""Unit tests for target_research layer in StateTracker."""

import pytest
from pathlib import Path

from research_orchestrator.state.tracker import StateTracker


@pytest.fixture
def tracker(tmp_path):
    """Create a StateTracker with a temp checkpoint directory."""
    return StateTracker(
        checkpoint_dir=tmp_path,
        execution_id="test_target_research",
    )


class TestTargetResearchInitialization:
    """Test target_research appears in initial state."""

    def test_initial_state_has_target_research(self, tracker):
        assert "target_research" in tracker.state

    def test_initial_target_research_is_empty(self, tracker):
        assert tracker.state["target_research"] == {}

    def test_initialize_target_research_creates_agent(self, tracker):
        tracker.initialize_target_research("target_research")
        assert "target_research" in tracker.state["target_research"]
        assert tracker.state["target_research"]["target_research"]["status"] == "pending"

    def test_initialize_is_idempotent(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.initialize_target_research("target_research")
        assert len(tracker.state["target_research"]) == 1


class TestTargetResearchLifecycle:
    """Test state transitions for target_research agents."""

    def test_pending_to_in_progress(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_in_progress("target_research", "target_research")
        assert tracker.state["target_research"]["target_research"]["status"] == "in_progress"

    def test_in_progress_to_complete(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_in_progress("target_research", "target_research")
        tracker.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md", "searches_performed": 35},
            layer="target_research",
        )
        assert tracker.state["target_research"]["target_research"]["status"] == "complete"

    def test_is_agent_complete_finds_target_research(self, tracker):
        tracker.initialize_target_research("target_research")
        assert not tracker.is_agent_complete("target_research")

        tracker.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md"},
            layer="target_research",
        )
        assert tracker.is_agent_complete("target_research")

    def test_mark_failed(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_failed("target_research", "API error", layer="target_research")
        assert tracker.state["target_research"]["target_research"]["status"] == "failed"

    def test_mark_for_rerun_finds_target_research(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md"},
            layer="target_research",
        )
        result = tracker.mark_for_rerun("target_research")
        assert result is True
        assert tracker.state["target_research"]["target_research"]["status"] == "pending"

    def test_get_agent_output_finds_target_research(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md", "searches_performed": 40},
            layer="target_research",
        )
        output = tracker.get_agent_output("target_research")
        assert output is not None
        assert output["output_path"] == "/tmp/test.md"
        assert output["searches_performed"] == 40


class TestTargetResearchInSummary:
    """Test target_research shows up in execution summary."""

    def test_execution_summary_includes_target_research(self, tracker):
        summary = tracker.get_execution_summary()
        assert "target_research_status" in summary

    def test_target_research_status_counts(self, tracker):
        tracker.initialize_target_research("target_research")
        summary = tracker.get_execution_summary()
        status = summary["target_research_status"]
        assert status["total"] == 1
        assert status["pending"] == 1
        assert status["complete"] == 0

    def test_target_research_status_after_complete(self, tracker):
        tracker.initialize_target_research("target_research")
        tracker.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md"},
            layer="target_research",
        )
        summary = tracker.get_execution_summary()
        status = summary["target_research_status"]
        assert status["complete"] == 1
        assert status["pending"] == 0


class TestTargetResearchCheckpoint:
    """Test target_research survives checkpoint save/load."""

    def test_target_research_persists_across_load(self, tmp_path):
        # Create tracker and complete target_research
        tracker1 = StateTracker(
            checkpoint_dir=tmp_path,
            execution_id="persist_test",
        )
        tracker1.initialize_target_research("target_research")
        tracker1.mark_complete(
            "target_research",
            outputs={"output_path": "/tmp/test.md"},
            layer="target_research",
        )

        # Load from same checkpoint
        tracker2 = StateTracker(
            checkpoint_dir=tmp_path,
            execution_id="persist_test",
        )
        assert "target_research" in tracker2.state
        assert tracker2.is_agent_complete("target_research")

    def test_backward_compat_adds_target_research_on_load(self, tmp_path):
        """Old checkpoints without target_research should get it added."""
        import json

        # Write a checkpoint without target_research
        checkpoint_file = tmp_path / "old_checkpoint.json"
        old_state = {
            "execution_id": "old_checkpoint",
            "started_at": "2026-01-01",
            "last_updated": "2026-01-01",
            "layer_0": {},
            "layer_1": {},
            "layer_2": {},
            "layer_3": {},
            "integrations": {},
            "validation": {},
            "brand_alignment": {},
            "target_alignment": {},
        }
        with open(checkpoint_file, "w") as f:
            json.dump(old_state, f)

        tracker = StateTracker(
            checkpoint_dir=tmp_path,
            execution_id="old_checkpoint",
        )
        assert "target_research" in tracker.state
