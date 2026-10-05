# Import logging so the Worker Agent can record
# received and sent messages
import logging

# Import the shared structured message model
from models.agent_message import AgentMessage


# Create a module-specific logger for the Worker Agent
logger = logging.getLogger(__name__)


class WorkerAgent:
    """
    Worker Agent executes the subtasks produced by the Planner Agent
    and sends the execution result to the Reviewer Agent.
    """

    def __init__(self):
        # Unique name used in agent-to-agent communication
        self.name = "worker"

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process subtasks received from the Planner Agent
        and return a structured execution result.
        """

        # Log the received message
        logger.info(
            "Worker received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        # Extract task information from the structured message
        task = message.content.get("task", "").strip()
        subtasks = message.content.get("subtasks", [])

        # Validate that subtasks were provided
        if not subtasks:
            logger.warning("Worker received no subtasks")

            return AgentMessage(
                sender=self.name,
                receiver=message.sender,
                intent="execution_failed",
                content={
                    "status": "error",
                    "reason": "No subtasks were provided",
                },
            )

        # Execute each subtask
        results = []

        for subtask in subtasks:
            results.append(
                f"Completed subtask: {subtask}"
            )

        # Create a structured message for the Reviewer Agent
        response = AgentMessage(
            sender=self.name,
            receiver="reviewer",
            intent="execution_result",
            content={
                "task": task,
                "results": results,
                "draft_output": (
                    f"Completed {len(results)} subtasks "
                    f"for '{task}'"
                ),
            },
            constraints={
                "requires_review": True,
            },
        )

        # Log the outgoing message
        logger.info(
            "Worker sending message to %s with intent %s",
            response.receiver,
            response.intent,
        )

        return response