"""
Tests for the multi-agent workflow FastAPI endpoints.

Covers:
- Successful API requests
- Agent approval responses
- Workflow message history
- Workflow identifiers
- Empty and whitespace-only input
- Task length validation
- Input trimming
- Missing and invalid request fields
"""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

WORKFLOW_URL = "/api/workflow/run"


def test_workflow_endpoint_success():
    """A valid task should return HTTP 200."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Complete AI assignment"},
    )

    assert response.status_code == 200


def test_workflow_returns_reviewer_approval():
    """The final workflow result should be reviewer approval."""

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


def test_workflow_returns_four_steps():
    """The normal workflow should contain four recorded steps."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Prepare weekly study plan"},
    )

    assert response.status_code == 200
    assert response.json()["steps"] == 4


def test_workflow_returns_message_history():
    """The API should return the full communication history."""

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


def test_workflow_returns_workflow_id():
    """The response should contain a workflow tracing ID."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "Create presentation slides"},
    )

    assert response.status_code == 200

    workflow_id = response.json()["workflow_id"]

    assert isinstance(workflow_id, str)
    assert len(workflow_id) == 8


def test_separate_requests_have_different_workflow_ids():
    """Different API requests should have different tracing IDs."""

    first_response = client.post(
        WORKFLOW_URL,
        json={"task": "First task"},
    )

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


def test_task_whitespace_is_trimmed():
    """Leading and trailing spaces should be removed."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "   Prepare study plan   "},
    )

    assert response.status_code == 200

    history = response.json()["message_history"]

    assert history[0]["content"]["task"] == "Prepare study plan"


def test_missing_task_returns_422():
    """A request without the required task should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={},
    )

    assert response.status_code == 422


def test_task_exceeding_max_length_returns_422():
    """Tasks exceeding 500 characters should be rejected."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "A" * 501},
    )

    assert response.status_code == 422


def test_task_at_max_length_is_accepted():
    """A task containing exactly 500 characters should be accepted."""

    response = client.post(
        WORKFLOW_URL,
        json={"task": "A" * 500},
    )

    assert response.status_code == 200


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


def test_response_contains_required_fields():
    """A successful response should include all required fields."""

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