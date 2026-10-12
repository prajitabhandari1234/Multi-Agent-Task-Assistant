
import logging

from models.agent_message import AgentMessage


# Create a logger for the Reviewer Agent
logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviews the Worker Agent's output.

    Responsibilities:
    - Validate the task and subtasks.
    - Check the completeness of Worker results.
    - Detect mismatched subtask and result counts.
    - Approve valid output.
    - Request revisions for invalid output.
    """

    def __init__(self):
        self.name = "reviewer"

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process a structured execution result received
        from the Worker Agent.
        """

        logger.info(
            "Reviewer received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        # Extract information from the Worker message
        task = message.content.get("task", "")
        subtasks = message.content.get("subtasks", [])
        results = message.content.get("results", [])
        draft_output = message.content.get("draft_output", "")

        # Safely validate text fields
        if not isinstance(task, str):
            task = ""

        if not isinstance(draft_output, str):
            draft_output = ""

        # Validate the list of subtasks
        valid_subtasks = (
            isinstance(subtasks, list)
            and len(subtasks) > 0
            and all(
                isinstance(subtask, str)
                and bool(subtask.strip())
                for subtask in subtasks
            )
        )

        # Validate the list of execution results
        valid_results = (
            isinstance(results, list)
            and len(results) > 0
            and all(
                isinstance(result, str)
                and bool(result.strip())
                for result in results
            )
        )

        # Step 1: Reject incomplete or invalid output
        if not (
            task.strip()
            and valid_subtasks
            and valid_results
            and draft_output.strip()
        ):
            logger.warning(
                "Reviewer rejected incomplete Worker output"
            )

            return AgentMessage(
                sender=self.name,
                receiver="worker",
                intent="revision_required",
                content={
                    "status": "rejected",
                    "task": task,
                    "subtasks": subtasks,
                    "results": results,
                    "reason": "Worker output is incomplete",
                },
                constraints={
                    "retry": True,
                },
            )

        # Step 2: Verify the result count matches the subtasks
        if len(results) != len(subtasks):
            logger.warning(
                "Reviewer rejected mismatched Worker results"
            )

            return AgentMessage(
                sender=self.name,
                receiver="worker",
                intent="revision_required",
                content={
                    "status": "rejected",
                    "task": task,
                    "subtasks": subtasks,
                    "results": results,
                    "reason": (
                        "Worker result count does not match "
                        "the number of subtasks"
                    ),
                },
                constraints={
                    "retry": True,
                },
            )

        # Step 3: Approve valid Worker output
        response = AgentMessage(
            sender=self.name,
            receiver="orchestrator",
            intent="review_approved",
            content={
                "status": "approved",
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "final_output": draft_output,
            },
            constraints={
                "retry": False,
            },
        )

        # Log the successful review
        logger.info(
            "Reviewer approved output for task: %s",
            task,
        )

        logger.info(
            "Reviewer sending message to %s with intent %s",
            response.receiver,
            response.intent,
        )

        return response
