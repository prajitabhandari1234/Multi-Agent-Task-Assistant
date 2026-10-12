
from unittest.mock import Mock

from models.agent_message import AgentMessage
from orchestration.orchestrator import Orchestrator


def revision_message():
    return AgentMessage(
        sender="reviewer",
        receiver="worker",
        intent="revision_required",
        content={
            "task": "Prepare a study plan",
            "subtasks": ["Create timetable"],
            "results": [""],
            "reason": "Subtask 1 has an empty result",
        },
        constraints={"retry": True},
    )


def approval_message():
    return AgentMessage(
        sender="reviewer",
        receiver="orchestrator",
        intent="review_approved",
        content={
            "status": "approved",
            "task": "Prepare a study plan",
            "results": ["Monday: Study Python"],
            "final_output": "Monday: Study Python",
        },
    )


def test_revision_is_routed_to_worker():
    orchestrator = Orchestrator(max_iterations=10)

    orchestrator.worker.process = Mock(
        return_value=AgentMessage(
            sender="worker",
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": "Prepare a study plan",
                "subtasks": ["Create timetable"],
                "results": ["Monday: Study Python"],
                "draft_output": "Monday: Study Python",
            },
        )
    )

    result = orchestrator._route(revision_message())

    assert result.intent == "execution_result"
    assert result.receiver == "reviewer"
    orchestrator.worker.process.assert_called_once()


def test_reviewer_can_approve_revised_output():
    orchestrator = Orchestrator(max_iterations=10)

    orchestrator.reviewer.process = Mock(
        return_value=approval_message()
    )

    message = AgentMessage(
        sender="worker",
        receiver="reviewer",
        intent="execution_result",
        content={
            "task": "Prepare a study plan",
            "subtasks": ["Create timetable"],
            "results": ["Monday: Study Python"],
            "draft_output": "Monday: Study Python",
        },
    )

    result = orchestrator._route(message)

    assert result.intent == "review_approved"
    assert result.content["status"] == "approved"


def test_repeated_rejection_stops_at_revision_limit():
    orchestrator = Orchestrator(max_iterations=10)

    orchestrator.reviewer.process = Mock(
        return_value=revision_message()
    )

    orchestrator.worker.process = Mock(
        return_value=AgentMessage(
            sender="worker",
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": "Prepare a study plan",
                "subtasks": ["Create timetable"],
                "results": [""],
                "draft_output": "",
            },
        )
    )

    result = orchestrator.run("Prepare a study plan")

    assert result.intent == "revision_limit_exceeded"
    assert orchestrator.revision_count == 2
    assert result.content["revisions"] == 2
