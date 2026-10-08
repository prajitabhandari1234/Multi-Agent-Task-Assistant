"""
Tests for the multi-agent orchestrator.

Covers:
- Successful Planner -> Worker -> Reviewer workflow
- Message history and communication order
- Workflow identifiers
- Maximum iteration guardrail
- Invalid routing
- Agent exceptions
- Workflow state reset
- Failure message tracking
"""

from unittest.mock import Mock

from models.agent_message import AgentMessage
from orchestration.orchestrator import Orchestrator


def test_orchestrator_successful_workflow():
    """A normal workflow should finish with reviewer approval."""

    orchestrator = Orchestrator(max_iterations=5)

    result = orchestrator.run("Complete AI assignment")

    assert result.sender == "reviewer"
    assert result.receiver == "orchestrator"
    assert result.intent == "review_approved"
    assert result.content["status"] == "approved"
    assert orchestrator.step_count == 4


def test_orchestrator_records_message_history():
    """Messages should follow the expected agent sequence."""

    orchestrator = Orchestrator(max_iterations=5)

    orchestrator.run("Prepare weekly study plan")

    history = orchestrator.message_history

    assert len(history) == 4

    assert [
        (message.sender, message.receiver, message.intent)
        for message in history
    ] == [
        ("user", "planner", "plan_task"),
        ("planner", "worker", "execute_subtasks"),
        ("worker", "reviewer", "execution_result"),
        ("reviewer", "orchestrator", "review_approved"),
    ]


def test_orchestrator_generates_workflow_id():
    """Each workflow should have a traceable identifier."""

    orchestrator = Orchestrator()

    orchestrator.run("Create presentation slides")

    assert isinstance(orchestrator.workflow_id, str)
    assert len(orchestrator.workflow_id) == 8


def test_workflow_ids_are_different():
    """Separate executions should receive unique IDs."""

    orchestrator = Orchestrator()

    orchestrator.run("Task one")
    first_id = orchestrator.workflow_id

    orchestrator.run("Task two")
    second_id = orchestrator.workflow_id

    assert first_id != second_id


def test_max_iterations_guardrail():
    """The workflow should stop when its iteration limit is reached."""

    orchestrator = Orchestrator(max_iterations=2)

    result = orchestrator.run("Complete AI assignment")

    assert result.sender == "orchestrator"
    assert result.receiver == "user"
    assert result.intent == "max_iterations_exceeded"
    assert result.content["status"] == "error"
    assert result.content["steps"] == 2

    assert orchestrator.step_count == 2
    assert len(orchestrator.message_history) == 3

    assert (
        orchestrator.message_history[-1].intent
        == "max_iterations_exceeded"
    )


def test_invalid_receiver_returns_routing_error():
    """Unknown agents should produce a structured routing error."""

    orchestrator = Orchestrator()

    message = AgentMessage(
        sender="user",
        receiver="unknown_agent",
        intent="test_invalid_route",
        content={"task": "Test routing"},
    )

    result = orchestrator._route(message)

    assert result.sender == "orchestrator"
    assert result.receiver == "user"
    assert result.intent == "routing_error"
    assert result.content["status"] == "error"
    assert "Unknown receiver" in result.content["reason"]


def test_agent_exception_returns_structured_error():
    """Unexpected agent exceptions should not crash routing."""

    orchestrator = Orchestrator()

    orchestrator.planner.process = Mock(
        side_effect=RuntimeError("Simulated agent failure")
    )

    message = AgentMessage(
        sender="user",
        receiver="planner",
        intent="plan_task",
        content={"task": "Test agent failure"},
    )

    result = orchestrator._route(message)

    assert result.sender == "orchestrator"
    assert result.receiver == "user"
    assert result.intent == "agent_error"
    assert result.content["status"] == "error"
    assert result.content["agent"] == "planner"


def test_agent_exception_stops_workflow():
    """An agent exception should stop the workflow and be recorded."""

    orchestrator = Orchestrator()

    orchestrator.planner.process = Mock(
        side_effect=RuntimeError("Planner unavailable")
    )

    result = orchestrator.run("Complete AI assignment")

    assert result.intent == "agent_error"
    assert orchestrator.step_count == 1
    assert len(orchestrator.message_history) == 2

    assert orchestrator.message_history[-1].intent == "agent_error"


def test_planning_failure_stops_workflow():
    """A planning failure should stop further agent execution."""

    orchestrator = Orchestrator()

    orchestrator.planner.process = Mock(
        return_value=AgentMessage(
            sender="planner",
            receiver="user",
            intent="planning_failed",
            content={
                "status": "error",
                "reason": "Planning failed",
            },
        )
    )

    result = orchestrator.run("Test planning failure")

    assert result.intent == "planning_failed"
    assert orchestrator.step_count == 2
    assert orchestrator.message_history[-1].intent == "planning_failed"


def test_execution_failure_stops_workflow():
    """A worker failure should stop the workflow safely."""

    orchestrator = Orchestrator()

    orchestrator.worker.process = Mock(
        return_value=AgentMessage(
            sender="worker",
            receiver="user",
            intent="execution_failed",
            content={
                "status": "error",
                "reason": "Execution failed",
            },
        )
    )

    result = orchestrator.run("Test worker failure")

    assert result.intent == "execution_failed"
    assert orchestrator.step_count == 3
    assert orchestrator.message_history[-1].intent == "execution_failed"


def test_orchestrator_resets_state_between_runs():
    """Running again should reset the step count and message history."""

    orchestrator = Orchestrator()

    orchestrator.run("First task")
    first_id = orchestrator.workflow_id

    orchestrator.run("Second task")

    assert orchestrator.workflow_id != first_id
    assert orchestrator.step_count == 4
    assert len(orchestrator.message_history) == 4

    assert (
        orchestrator.message_history[0].content["task"]
        == "Second task"
    )


def test_zero_iterations_returns_guardrail_error():
    """A zero-iteration limit should prevent agent execution."""

    orchestrator = Orchestrator(max_iterations=0)

    result = orchestrator.run("Complete AI assignment")

    assert result.intent == "max_iterations_exceeded"
    assert orchestrator.step_count == 0
    assert len(orchestrator.message_history) == 1
    assert orchestrator.message_history[0].intent == "max_iterations_exceeded"