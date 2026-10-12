
import pytest

from agents import worker_agent
from agents.worker_agent import WorkerAgent
from models.agent_message import AgentMessage


def make_message(subtasks=None):
    if subtasks is None:
        subtasks = ["Create a study timetable"]

    return AgentMessage(
        sender="planner",
        receiver="worker",
        intent="execute_subtasks",
        content={
            "task": "Prepare a weekly study plan",
            "subtasks": subtasks,
        },
    )


def test_worker_generates_ai_output(monkeypatch):
    monkeypatch.setattr(
        worker_agent,
        "generate_response",
        lambda prompt: "Study Python on Monday.",
    )

    result = WorkerAgent().process(make_message())

    assert result.intent == "execution_result"
    assert result.receiver == "reviewer"
    assert result.content["results"] == [
        "Study Python on Monday."
    ]
    assert "Study Python on Monday." in (
        result.content["draft_output"]
    )


def test_worker_processes_multiple_subtasks(monkeypatch):
    calls = []

    def mock_generate(prompt):
        calls.append(prompt)
        return f"Generated result {len(calls)}"

    monkeypatch.setattr(
        worker_agent,
        "generate_response",
        mock_generate,
    )

    result = WorkerAgent().process(
        make_message(["Plan sessions", "Add revision"])
    )

    assert result.intent == "execution_result"
    assert len(calls) == 2
    assert len(result.content["results"]) == 2


@pytest.mark.parametrize(
    "subtasks",
    [[], [""] , ["Valid", None], "invalid"],
)
def test_worker_rejects_invalid_subtasks(subtasks):
    result = WorkerAgent().process(
        make_message(subtasks)
    )

    assert result.intent == "execution_failed"
    assert result.content["status"] == "error"


def test_worker_handles_empty_ai_response(monkeypatch):
    monkeypatch.setattr(
        worker_agent,
        "generate_response",
        lambda prompt: "",
    )

    result = WorkerAgent().process(make_message())

    assert result.intent == "execution_failed"


def test_worker_handles_gemini_exception(monkeypatch):
    def mock_failure(prompt):
        raise RuntimeError("Mock Gemini failure")

    monkeypatch.setattr(
        worker_agent,
        "generate_response",
        mock_failure,
    )

    result = WorkerAgent().process(make_message())

    assert result.intent == "execution_failed"
    assert "subtask 1" in result.content["reason"]
