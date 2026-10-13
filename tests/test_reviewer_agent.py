
from unittest.mock import patch

from agents.reviewer_agent import ReviewerAgent
from models.agent_message import AgentMessage


def make_worker_message():
    """Create a valid Worker Agent response for testing."""
    return AgentMessage(
        sender="worker",
        receiver="reviewer",
        intent="execution_result",
        content={
            "task": "Prepare a Python study plan",
            "subtasks": [
                "Identify Python topics",
                "Create a weekly study schedule",
            ],
            "results": [
                "Study variables, loops, functions and classes.",
                "Study Python on Monday and Wednesday.",
            ],
            "draft_output": (
                "Study Python fundamentals and follow "
                "a weekly study schedule."
            ),
        },
    )


@patch("agents.reviewer_agent.generate_response")
def test_reviewer_approves_valid_output(mock_generate):
    """Reviewer approves a valid AI-reviewed result."""

    mock_generate.return_value = """
    {
        "approved": true,
        "reason": "All subtasks are addressed.",
        "issues": []
    }
    """

    reviewer = ReviewerAgent()
    response = reviewer.process(make_worker_message())

    assert response.intent == "review_approved"
    assert response.receiver == "orchestrator"
    assert response.content["status"] == "approved"


@patch("agents.reviewer_agent.generate_response")
def test_reviewer_requests_revision(mock_generate):
    """Reviewer requests corrections for poor-quality output."""

    mock_generate.return_value = """
    {
        "approved": false,
        "reason": "The schedule is incomplete.",
        "issues": [
            "Add study sessions for the remaining days."
        ]
    }
    """

    reviewer = ReviewerAgent()
    response = reviewer.process(make_worker_message())

    assert response.intent == "revision_required"
    assert response.receiver == "worker"
    assert "remaining days" in response.content["reason"]


def test_reviewer_rejects_missing_results():
    """Reviewer rejects structurally incomplete output."""

    message = make_worker_message()
    message.content["results"] = []

    reviewer = ReviewerAgent()
    response = reviewer.process(message)

    assert response.intent == "revision_required"
    assert response.content["status"] == "rejected"


def test_reviewer_rejects_mismatched_results():
    """Reviewer detects a mismatch between subtasks and results."""

    message = make_worker_message()
    message.content["results"] = [
        "Study Python fundamentals."
    ]

    reviewer = ReviewerAgent()
    response = reviewer.process(message)

    assert response.intent == "revision_required"
    assert "does not match" in response.content["reason"]


@patch("agents.reviewer_agent.generate_response")
def test_reviewer_handles_invalid_json(mock_generate):
    """Reviewer must not approve an invalid AI response."""

    mock_generate.return_value = "This is not valid JSON"

    reviewer = ReviewerAgent()
    response = reviewer.process(make_worker_message())

    assert response.intent == "revision_required"
    assert response.content["status"] == "rejected"
