import logging
import uuid
from typing import List

from agents.planner_agent import PlannerAgent
from agents.worker_agent import WorkerAgent
from agents.reviewer_agent import ReviewerAgent
from models.agent_message import AgentMessage


# Create a logger for the orchestrator
logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates communication between the Planner, Worker,
    and Reviewer agents.
    """

    def __init__(self, max_iterations: int = 5):
        # Create the specialised agents
        self.planner = PlannerAgent()
        self.worker = WorkerAgent()
        self.reviewer = ReviewerAgent()

        # Guardrail to prevent uncontrolled workflow loops
        self.max_iterations = max_iterations

        # Tracks the number of workflow steps
        self.step_count = 0

        # Unique identifier for the current workflow run
        self.workflow_id = ""

        # Stores all messages exchanged during the workflow
        self.message_history: List[AgentMessage] = []

        # Maps receiver names to agent instances
        self.agents = {
            "planner": self.planner,
            "worker": self.worker,
            "reviewer": self.reviewer,
        }

    def _record_message(self, message: AgentMessage) -> None:
        """
        Store and log each message exchanged during the workflow.
        """

        self.message_history.append(message)

        logger.info(
            "Workflow %s | Step %s | %s -> %s | intent=%s",
            self.workflow_id,
            self.step_count,
            message.sender,
            message.receiver,
            message.intent,
        )

    def _route(self, message: AgentMessage) -> AgentMessage:
        """
        Route a structured message to the correct agent.
        """

        receiver = message.receiver

        # Validate that the receiver exists
        if receiver not in self.agents:
            logger.error(
                "Workflow %s | Invalid receiver '%s'",
                self.workflow_id,
                receiver,
            )

            return AgentMessage(
                sender="orchestrator",
                receiver="user",
                intent="routing_error",
                content={
                    "status": "error",
                    "reason": f"Unknown receiver: {receiver}",
                },
            )

        # Find the requested agent
        agent = self.agents[receiver]

        # Send the message to the agent
        return agent.process(message)

    def run(self, task: str) -> AgentMessage:
        """
        Start and coordinate a complete multi-agent workflow.
        """

        # Reset workflow-specific state
        self.step_count = 0
        self.message_history = []

        # Generate a unique ID for this workflow run
        self.workflow_id = str(uuid.uuid4())[:8]

        logger.info(
            "Workflow %s | START | task=%s",
            self.workflow_id,
            task,
        )

        # Create the initial message for the Planner Agent
        current_message = AgentMessage(
            sender="user",
            receiver="planner",
            intent="plan_task",
            content={
                "task": task,
            },
        )

        # Continue routing until the workflow finishes
        # or the maximum iteration limit is reached
        while self.step_count < self.max_iterations:

            self.step_count += 1

            # Store and log the current message
            self._record_message(current_message)

            # Check whether the Reviewer approved the result
            if (
                current_message.receiver == "orchestrator"
                and current_message.intent == "review_approved"
            ):
                logger.info(
                    "Workflow %s | COMPLETED | steps=%s",
                    self.workflow_id,
                    self.step_count,
                )

                return current_message

            # Stop the workflow if an agent reports a failure
            if current_message.intent in {
                "planning_failed",
                "execution_failed",
            }:
                logger.error(
                    "Workflow %s | FAILED | intent=%s",
                    self.workflow_id,
                    current_message.intent,
                )

                return current_message

            # Route the message to the requested agent
            next_message = self._route(current_message)

            # Stop immediately if routing failed
            if next_message.intent == "routing_error":
                self._record_message(next_message)

                logger.error(
                    "Workflow %s | FAILED | routing error",
                    self.workflow_id,
                )

                return next_message

            # Continue the workflow with the next message
            current_message = next_message

        # Guardrail: stop if maximum iterations are reached
        logger.error(
            "Workflow %s | MAX ITERATIONS | limit=%s",
            self.workflow_id,
            self.max_iterations,
        )

        return AgentMessage(
            sender="orchestrator",
            receiver="user",
            intent="max_iterations_exceeded",
            content={
                "status": "error",
                "reason": "Maximum workflow iterations reached",
                "steps": self.step_count,
            },
        )