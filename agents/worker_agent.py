
import logging

from models.agent_message import AgentMessage
from utils.llm_client import generate_response


logger = logging.getLogger(__name__)


class WorkerAgent:
    """
    Generates task content using Gemini and
    revises output when the Reviewer requests it.
    """

    def __init__(self):
        self.name = "worker"

    def _failure(self, reason: str) -> AgentMessage:
        logger.error("Worker failed: %s", reason)

        return AgentMessage(
            sender=self.name,
            receiver="user",
            intent="execution_failed",
            content={
                "status": "error",
                "reason": reason,
            },
        )

    def process(self, message: AgentMessage) -> AgentMessage:
        logger.info(
            "Worker received %s from %s",
            message.intent,
            message.sender,
        )

        if message.intent not in {
            "execute_subtasks",
            "revision_required",
        }:
            return self._failure(
                "Unsupported Worker message intent"
            )

        content = message.content
        task = content.get("task", "")
        subtasks = content.get("subtasks", [])

        if not isinstance(task, str) or not task.strip():
            return self._failure("Invalid task")

        if (
            not isinstance(subtasks, list)
            or not subtasks
            or not all(
                isinstance(item, str) and item.strip()
                for item in subtasks
            )
        ):
            return self._failure("Invalid subtasks")

        is_revision = message.intent == "revision_required"

        feedback = (
            str(content.get("reason", ""))
            if is_revision
            else ""
        )

        previous_results = (
            content.get("results", [])
            if is_revision
            else []
        )

        if not isinstance(previous_results, list):
            previous_results = []

        results = []

        for index, subtask in enumerate(subtasks, start=1):
            previous = (
                previous_results[index - 1]
                if index <= len(previous_results)
                else ""
            )

            prompt = f"""
You are the Worker Agent in a multi-agent system.

Overall task:
{task}

Current subtask:
{subtask}

Previous output:
{previous}

Reviewer feedback:
{feedback}

Instructions:
- Generate useful content for the subtask.
- Follow the overall user task.
- If revising, address the reviewer's feedback.
- Do not claim to have performed external actions.
- Do not invent completed real-world work.
- Return only the generated content.
"""

            try:
                output = generate_response(prompt)

                if not isinstance(output, str) or not output.strip():
                    raise ValueError("Empty Gemini response")

                results.append(output.strip())

            except Exception:
                logger.exception(
                    "Worker generation failed at subtask %s",
                    index,
                )
                return self._failure(
                    f"Unable to process subtask {index}"
                )

        draft_output = "\n\n".join(
            f"Subtask {index}: {subtask}\n{result}"
            for index, (subtask, result)
            in enumerate(zip(subtasks, results), start=1)
        )

        logger.info(
            "Worker completed %s subtasks | revision=%s",
            len(results),
            is_revision,
        )

        return AgentMessage(
            sender=self.name,
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "draft_output": draft_output,
                "revised": is_revision,
            },
            constraints={
                "requires_review": True,
            },
        )
