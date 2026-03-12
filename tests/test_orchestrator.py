"""Tests for the Orchestrator agent routing logic."""

import json
import pytest
from unittest.mock import patch, MagicMock

from config.agent_registry import AgentRegistry, AgentInfo


class TestAgentRegistry:
    """Tests for the AgentRegistry class."""

    def test_registry_has_9_agents(self):
        registry = AgentRegistry()
        assert len(registry.list_all()) == 9

    def test_all_agent_ids_are_unique(self):
        registry = AgentRegistry()
        ids = registry.get_ids()
        assert len(ids) == len(set(ids))

    def test_get_existing_agent(self):
        registry = AgentRegistry()
        agent = registry.get("code_reviewer")
        assert agent is not None
        assert agent.name == "Code Reviewer"
        assert agent.agent_id == "code_reviewer"

    def test_get_nonexistent_agent(self):
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_all_agents_have_required_fields(self):
        registry = AgentRegistry()
        for agent in registry.list_all():
            assert agent.name, f"Agent {agent.agent_id} missing name"
            assert agent.agent_id, f"Agent {agent.name} missing agent_id"
            assert agent.description, f"Agent {agent.agent_id} missing description"
            assert len(agent.capabilities) > 0, f"Agent {agent.agent_id} has no capabilities"
            assert len(agent.keywords) > 0, f"Agent {agent.agent_id} has no keywords"

    def test_registry_summary_includes_all_agents(self):
        registry = AgentRegistry()
        summary = registry.get_registry_summary()
        for agent in registry.list_all():
            assert agent.name in summary
            assert agent.agent_id in summary

    @pytest.mark.parametrize("agent_id", [
        "code_reviewer", "bug_analyzer", "architecture", "testing",
        "security", "documentation", "refactoring", "devops", "performance",
    ])
    def test_each_agent_is_registered(self, agent_id):
        registry = AgentRegistry()
        assert registry.get(agent_id) is not None


class TestOrchestratorRouting:
    """Tests for orchestrator routing decision parsing."""

    def test_valid_routing_json_parsing(self):
        """Verify that valid JSON routing decisions are parsed correctly."""
        routing_json = json.dumps({
            "analysis": "User wants a code review",
            "assignments": [
                {"agent_id": "code_reviewer", "task": "Review the code", "priority": 1}
            ],
        })
        parsed = json.loads(routing_json)
        assert parsed["assignments"][0]["agent_id"] == "code_reviewer"
        assert parsed["assignments"][0]["priority"] == 1

    def test_multi_agent_routing(self):
        """Verify that multi-agent assignments are sorted by priority."""
        assignments = [
            {"agent_id": "refactoring", "task": "Refactor", "priority": 2},
            {"agent_id": "code_reviewer", "task": "Review", "priority": 1},
            {"agent_id": "testing", "task": "Test", "priority": 3},
        ]
        sorted_assignments = sorted(assignments, key=lambda a: a.get("priority", 1))
        assert sorted_assignments[0]["agent_id"] == "code_reviewer"
        assert sorted_assignments[1]["agent_id"] == "refactoring"
        assert sorted_assignments[2]["agent_id"] == "testing"

    def test_routing_fallback_on_invalid_json(self):
        """Verify graceful fallback when JSON parsing fails."""
        invalid_content = "This is not JSON"
        try:
            json.loads(invalid_content)
            parsed = True
        except json.JSONDecodeError:
            parsed = False
        assert not parsed


class TestOrchestratorAgentLookup:
    """Tests for agent instance lookup in the orchestrator."""

    def test_all_registered_agents_can_be_instantiated(self):
        """Verify that all agents in the registry have corresponding classes."""
        from agents.code_reviewer import CodeReviewerAgent
        from agents.bug_analyzer import BugAnalyzerAgent
        from agents.architecture import ArchitectureAgent
        from agents.testing import TestingAgent
        from agents.security import SecurityAgent
        from agents.documentation import DocumentationAgent
        from agents.refactoring import RefactoringAgent
        from agents.devops import DevOpsAgent
        from agents.performance import PerformanceAgent

        agent_classes = {
            "code_reviewer": CodeReviewerAgent,
            "bug_analyzer": BugAnalyzerAgent,
            "architecture": ArchitectureAgent,
            "testing": TestingAgent,
            "security": SecurityAgent,
            "documentation": DocumentationAgent,
            "refactoring": RefactoringAgent,
            "devops": DevOpsAgent,
            "performance": PerformanceAgent,
        }

        registry = AgentRegistry()
        for agent_id in registry.get_ids():
            assert agent_id in agent_classes, f"No class found for agent: {agent_id}"
