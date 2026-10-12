
import logging

from models.agent_message import AgentMessage
from utils.llm_client import generate_response


logger = logging.getLogger(__name__)


class WorkerAgent:
    """
    Executes subtasks using Gemini and sends
    structured results to the Reviewer Agent.
    """

    def __init__(self):
        self.name = "worker"

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process Planner subtasks and generate useful
        outputs using Gemini.
        """

        logger.info(
            "Worker received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        task = message.content.get("task", "")
        subtasks = message.content.get("subtasks", [])

        if not isinstance(task, str) or not task.strip():
            return self._failure(
                message,
                "Task is missing or invalid",
            )

        if (
            not isinstance(subtasks, list)
            or not subtasks
            or not all(
                isinstance(item, str) and item.strip()
                for item in subtasks
            )
        ):
            return self._failure(
                message,
                "No valid subtasks were provided",
            )

        task = task.strip()
        results = []

        for index, subtask in enumerate(subtasks, start=1):
            logger.info(
                "Worker processing subtask %s of %s",
                index,
                len(subtasks),
            )

            prompt = f"""
You are the Worker Agent in a multi-agent
task assistant.

Overall user task:
{task}

Current subtask:
{subtask}

Instructions:
- Produce a useful, specific result for this subtask.
- Follow the overall task objective.
- Do not claim to have performed real-world actions.
- Do not invent completed actions or external results.
- Return clear plain-text content.
"""

            try:
                output = generate_response(prompt)

                if not isinstance(output, str) or not output.strip():
                    raise ValueError(
                        "Gemini returned an empty response"
                    )

                results.append(output.strip())

            except Exception as error:
                logger.error(
                    "Worker failed on subtask %s: %s",
                    index,
                    error,
                )

                return self._failure(
                    message,
                    f"Unable to process subtask {index}",
                )

        draft_output = "\n\n".join(
            f"Subtask {index}: {subtask}\n{result}"
            for index, (subtask, result)
            in enumerate(zip(subtasks, results), start=1)
        )

        response = AgentMessage(
            sender=self.name,
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "draft_output": draft_output,
            },
            constraints={
                "requires_review": True,
            },
        )

        logger.info(
            "Worker sending %s results to Reviewer",
            len(results),
        )

        return response

    def _failure(
        self,
        message: AgentMessage,
        reason: str,
    ) -> AgentMessage:
        """
        Return a structured failure message.
        """

        logger.warning(
            "Worker execution failed: %s",
            reason,
        )

        return AgentMessage(
            sender=self.name,
            receiver=message.sender,
            intent="execution_failed",
            content={
                "status": "error",
                "reason": reason,
            },
        )
