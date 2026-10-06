# Import logging so the Reviewer Agent can record
# received and sent messages
import logging

# Import the shared structured message model
from models.agent_message import AgentMessage


# Create a module-specific logger for the Reviewer Agent
logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviewer Agent validates the output produced by the Worker Agent
    before the result is accepted as the final workflow output.
    """

    def __init__(self):
        # Unique name used in agent-to-agent communication
        self.name = "reviewer"

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Review the Worker's execution result and return either
        an approved result or a revision request.
        """

        # Log the received message
        logger.info(
            "Reviewer received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        # Extract information from the Worker message
        task = message.content.get("task", "").strip()
        results = message.content.get("results", [])
        draft_output = message.content.get("draft_output", "").strip()

        # Validate that the Worker produced usable results
        if not results or not draft_output:
            logger.warning(
                "Reviewer rejected output because required results are missing"
            )

            return AgentMessage(
                sender=self.name,
                receiver="worker",
                intent="revision_required",
                content={
                    "status": "rejected",
                    "task": task,
                    "reason": "Worker output is incomplete",
                },
                constraints={
                    "retry": True,
                },
            )

        # Approve the Worker's output
        response = AgentMessage(
            sender=self.name,
            receiver="orchestrator",
            intent="review_approved",
            content={
                "status": "approved",
                "task": task,
                "results": results,
                "final_output": draft_output,
            },
            constraints={
                "retry": False,
            },
        )

        # Log the outgoing message
        logger.info(
            "Reviewer sending message to %s with intent %s",
            response.receiver,
            response.intent,
        )

        return response