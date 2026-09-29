# Import logging so the Planner Agent can record
# received and sent messages
import logging

# Import the shared structured message model used
# for communication between agents
from models.agent_message import AgentMessage


# Create a module-specific logger for the Planner Agent
logger = logging.getLogger(__name__)


# Planner Agent is responsible for analysing a user task
# and breaking it into smaller subtasks
class PlannerAgent:

    def __init__(self):
        # Unique name used when sending agent messages
        self.name = "planner"

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process an incoming task message and create
        a structured plan for the Worker Agent.
        """

        # Log the received message
        logger.info(
            "Planner received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        # Extract the task from the structured message
        task = message.content.get("task", "").strip()

        # Basic validation before creating a plan
        if not task:
            logger.warning("Planner received an empty task")

            return AgentMessage(
                sender=self.name,
                receiver=message.sender,
                intent="planning_failed",
                content={
                    "status": "error",
                    "reason": "Task cannot be empty",
                },
            )

        # Break the task into clear subtasks
        subtasks = [
            f"Analyse requirements for '{task}'",
            f"Prepare an action plan for '{task}'",
            f"Complete the required work for '{task}'",
        ]

        # Create a structured message for the Worker Agent
        response = AgentMessage(
            sender=self.name,
            receiver="worker",
            intent="execute_subtasks",
            content={
                "task": task,
                "subtasks": subtasks,
            },
            constraints={
                "follow_plan": True,
            },
        )

        # Log the outgoing message
        logger.info(
            "Planner sending message to %s with intent %s",
            response.receiver,
            response.intent,
        )

        return response