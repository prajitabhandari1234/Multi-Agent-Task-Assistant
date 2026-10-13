
"""
Tests for the Multi-Agent Task Assistant FastAPI workflow endpoints.

Covers:
- Successful API requests
- Reviewer approval
- Four-step workflow without revision
- Six-step workflow with one revision
- Agent communication history
- Workflow identifiers
- Empty and whitespace-only tasks
- Task length validation
- Input trimming
- Missing and invalid request fields

The Orchestrator is mocked for successful workflow tests
to avoid external Gemini API calls.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models.agent_message import AgentMessage


client = TestClient(app)

WORKFLOW_URL = "/api/workflow/run"

ORCHESTRATOR_PATCH = "api.workflow_routes.Orchestrator"


def setup_mock_workflow(
    mock_orchestrator,
    task,
    revisions=0,
    workflow_id="abc12345",
):
    """
    Configure a mocked Orchestrator.

    The real Orchestrator.run() returns an AgentMessage.

    The API obtains workflow metadata from the
    Orchestrator instance.
    """

    instance = mock_orchestrator.return_value

    subtasks = [
        "Analyse the task",
        "Prepare the final output",
    ]

    results = [
        "Task analysed successfully.",
        "Final output prepared.",
    ]

    history = [
        AgentMessage(
            sender="user",
            receiver="planner",
            intent="plan_task",
            content={
                "task": task,
            },
        ),
        AgentMessage(
            sender="planner",
            receiver="worker",
            intent="execute_subtasks",
            content={
                "task": task,
                "subtasks": subtasks,
            },
        ),
        AgentMessage(
            sender="worker",
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "draft_output": "Initial task output.",
            },
        ),
    ]

    for _ in range(revisions):

        history.append(
            AgentMessage(
                sender="reviewer",
                receiver="worker",
                intent="revision_required",
                content={
                    "status": "rejected",
                    "task": task,
                    "subtasks": subtasks,
                    "results": results,
                    "reason": "Improve output consistency.",
                },
                constraints={
                    "retry": True,
                },
            )
        )

        history.append(
            AgentMessage(
                sender="worker",
                receiver="reviewer",
                intent="execution_result",
                content={
                    "task": task,
                    "subtasks": subtasks,
                    "results": [
                        "Revised task analysis.",
                        "Improved final output.",
                    ],
                    "draft_output": "Revised task output.",
                    "revised": True,
                },
            )
        )

    approval = AgentMessage(
        sender="reviewer",
        receiver="orchestrator",
        intent="review_approved",
        content={
            "status": "approved",
            "task": task,
            "subtasks": subtasks,
            "results": results,
            "final_output": "Completed task successfully.",
            "review_reason": "Output meets requirements.",
        },
        constraints={
            "retry": False,
        },
    )

    history.append(approval)

    instance.run.return_value = approval

    instance.workflow_id = workflow_id
    instance.step_count = len(history)
    instance.revision_count = revisions
    instance.message_history = history

    return instance


@patch(ORCHESTRATOR_PATCH)
def test_workflow_endpoint_success(mock_orchestrator):
    """A valid task should return HTTP 200."""

    setup_mock_workflow(
        mock_orchestrator,
        "Complete AI assignment",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Complete AI assignment"},
    )

    assert response.status_code == 200


@patch(ORCHESTRATOR_PATCH)
def test_workflow_returns_reviewer_approval(mock_orchestrator):
    """The final result should contain Reviewer approval."""

    setup_mock_workflow(
        mock_orchestrator,
        "Complete AI assignment",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Complete AI assignment"},
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert result["sender"] == "reviewer"
    assert result["receiver"] == "orchestrator"
    assert result["intent"] == "review_approved"
    assert result["content"]["status"] == "approved"


@patch(ORCHESTRATOR_PATCH)
def test_workflow_returns_four_steps(mock_orchestrator):
    """A workflow approved immediately takes four steps."""

    setup_mock_workflow(
        mock_orchestrator,
        "Prepare weekly study plan",
        revisions=0,
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Prepare weekly study plan"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["steps"] == 4
    assert len(data["message_history"]) == 4


@patch(ORCHESTRATOR_PATCH)
def test_workflow_returns_six_steps_after_revision(mock_orchestrator):
    """One Reviewer revision produces six steps."""

    setup_mock_workflow(
        mock_orchestrator,
        "Prepare weekly study plan",
        revisions=1,
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Prepare weekly study plan"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["steps"] == 6
    assert len(data["message_history"]) == 6


@patch(ORCHESTRATOR_PATCH)
def test_workflow_returns_message_history(mock_orchestrator):
    """The API should return the full communication history."""

    setup_mock_workflow(
        mock_orchestrator,
        "Prepare weekly study plan",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Prepare weekly study plan"},
    )

    assert response.status_code == 200

    history = response.json()["message_history"]

    assert len(history) == 4

    assert [message["intent"] for message in history] == [
        "plan_task",
        "execute_subtasks",
        "execution_result",
        "review_approved",
    ]


@patch(ORCHESTRATOR_PATCH)
def test_workflow_message_history_with_revision(mock_orchestrator):
    """History should include Reviewer feedback and revised output."""

    setup_mock_workflow(
        mock_orchestrator,
        "Prepare weekly study plan",
        revisions=1,
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Prepare weekly study plan"},
    )

    assert response.status_code == 200

    history = response.json()["message_history"]

    assert len(history) == 6

    assert [message["intent"] for message in history] == [
        "plan_task",
        "execute_subtasks",
        "execution_result",
        "revision_required",
        "execution_result",
        "review_approved",
    ]


@patch(ORCHESTRATOR_PATCH)
def test_workflow_returns_workflow_id(mock_orchestrator):
    """The response should contain an eight-character workflow ID."""

    setup_mock_workflow(
        mock_orchestrator,
        "Create presentation slides",
        workflow_id="abc12345",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Create presentation slides"},
    )

    assert response.status_code == 200

    workflow_id = response.json()["workflow_id"]

    assert isinstance(workflow_id, str)
    assert len(workflow_id) == 8
    assert workflow_id == "abc12345"


@patch(ORCHESTRATOR_PATCH)
def test_separate_requests_have_different_workflow_ids(
    mock_orchestrator,
):
    """Different API requests should have different workflow IDs."""

    instance = setup_mock_workflow(
        mock_orchestrator,
        "First task",
        workflow_id="abc12345",
    )

    first_response = client.post(
        WORKFLOW_URL,
        json={"task": "First task"},
    )

    instance.workflow_id = "xyz67890"

    second_response = client.post(
        WORKFLOW_URL,
        json={"task": "Second task"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        first_response.json()["workflow_id"]
        != second_response.json()["workflow_id"]
    )


def test_empty_task_returns_422():
    """An empty task should fail Pydantic validation."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": ""},
    )

    assert response.status_code == 422


def test_whitespace_only_task_returns_422():
    """Whitespace-only input should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "     "},
    )

    assert response.status_code == 422

    assert (
        "Task cannot be empty or whitespace only"
        in str(response.json())
    )


@patch(ORCHESTRATOR_PATCH)
def test_task_whitespace_is_trimmed(mock_orchestrator):
    """Leading and trailing spaces should be removed."""

    instance = setup_mock_workflow(
        mock_orchestrator,
        "Prepare study plan",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "   Prepare study plan   "},
    )

    assert response.status_code == 200

    instance.run.assert_called_once_with(
        "Prepare study plan"
    )


def test_missing_task_returns_422():
    """A request without a task should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={},
    )

    assert response.status_code == 422


def test_task_exceeding_max_length_returns_422():
    """Tasks longer than 500 characters should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "A" * 501},
    )

    assert response.status_code == 422


@patch(ORCHESTRATOR_PATCH)
def test_task_at_max_length_is_accepted(mock_orchestrator):
    """A task of exactly 500 characters should be accepted."""

    task = "A" * 500

    instance = setup_mock_workflow(
        mock_orchestrator,
        task,
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": task},
    )

    assert response.status_code == 200

    instance.run.assert_called_once_with(task)


def test_invalid_task_type_returns_422():
    """Non-string task input should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": 12345},
    )

    assert response.status_code == 422


def test_null_task_returns_422():
    """A null task should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": None},
    )

    assert response.status_code == 422


@patch(ORCHESTRATOR_PATCH)
def test_response_contains_required_fields(mock_orchestrator):
    """A successful response should contain required fields."""

    setup_mock_workflow(
        mock_orchestrator,
        "Complete AI assignment",
    )

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Complete AI assignment"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "workflow_id" in data
    assert "result" in data
    assert "steps" in data
    assert "message_history" in data

    assert data["steps"] == len(data["message_history"])
