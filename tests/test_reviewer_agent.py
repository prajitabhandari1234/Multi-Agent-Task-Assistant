
from agents.reviewer_agent import ReviewerAgent
from models.agent_message import AgentMessage


def make_message(subtasks, results, draft_output):
    return AgentMessage(
        sender="worker",
        receiver="reviewer",
        intent="execution_result",
        content={
            "task": "Prepare a study plan",
            "subtasks": subtasks,
            "results": results,
            "draft_output": draft_output,
        },
    )


def test_reviewer_approves_complete_output():
    message = make_message(
        ["Plan Monday", "Plan Tuesday"],
        ["Study Python", "Revise testing"],
        "Monday: Study Python\nTuesday: Revise testing",
    )

    result = ReviewerAgent().process(message)

    assert result.intent == "review_approved"
    assert result.receiver == "orchestrator"
    assert result.content["status"] == "approved"


def test_reviewer_rejects_missing_results():
    message = make_message(
        ["Plan Monday"],
        [],
        "",
    )

    result = ReviewerAgent().process(message)

    assert result.intent == "revision_required"
    assert result.receiver == "worker"


def test_reviewer_rejects_mismatched_results():
    message = make_message(
        ["Plan Monday", "Plan Tuesday"],
        ["Study Python"],
        "Monday: Study Python",
    )

    result = ReviewerAgent().process(message)

    assert result.intent == "revision_required"
    assert "does not match" in result.content["reason"]


def test_reviewer_rejects_empty_result():
    message = make_message(
        ["Plan Monday"],
        [""],
        "Generated plan",
    )

    result = ReviewerAgent().process(message)

    assert result.intent == "revision_required"
