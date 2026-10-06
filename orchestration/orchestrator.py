import logging
from typing import List

from agents.planner_agent import PlannerAgent
from agents.worker_agent import WorkerAgent
from agents.reviewer_agent import ReviewerAgent
from models.agent_message import AgentMessage


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates communication between the Planner, Worker,
    and Reviewer agents.
    """

    def __init__(self, max_iterations: int = 5):
        self.planner = PlannerAgent()
        self.worker = WorkerAgent()
        self.reviewer = ReviewerAgent()

        self.max_iterations = max_iterations
        self.step_count = 0

        # Stores messages exchanged during the current workflow.
        self.message_history: List[AgentMessage] = []

        # Maps receiver names to agent instances.
        self.agents = {
            "planner": self.planner,
            "worker": self.worker,
            "reviewer": self.reviewer,
        }

    def _record_message(self, message: AgentMessage) -> None:
        """Store and log an agent message."""

        self.message_history.append(message)

        logger.info(
            "Message: %s -> %s | intent=%s",
            message.sender,
            message.receiver,
            message.intent,
        )

    def _route(self, message: AgentMessage) -> AgentMessage:
        """
        Route a message to the correct agent.
        """

        receiver = message.receiver

        if receiver not in self.agents:
            logger.error(
                "Invalid receiver '%s'",
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

        agent = self.agents[receiver]

        return agent.process(message)

    def run(self, task: str) -> AgentMessage:
        """
        Start and coordinate a complete multi-agent workflow.
        """

        # Reset workflow-specific state.
        self.step_count = 0
        self.message_history = []

        current_message = AgentMessage(
            sender="user",
            receiver="planner",
            intent="plan_task",
            content={
                "task": task,
            },
        )

        while self.step_count < self.max_iterations:

            self.step_count += 1
            self._record_message(current_message)

            logger.info(
                "Workflow step %s of %s",
                self.step_count,
                self.max_iterations,
            )

            # Reviewer has approved the result.
            if (
                current_message.receiver == "orchestrator"
                and current_message.intent == "review_approved"
            ):
                logger.info("Workflow completed successfully")
                return current_message

            # Handle agent failure messages.
            if current_message.intent in {
                "planning_failed",
                "execution_failed",
            }:
                logger.error(
                    "Workflow stopped because of %s",
                    current_message.intent,
                )
                return current_message

            # Route the message to the requested agent.
            next_message = self._route(current_message)

            # Handle an invalid receiver immediately.
            if next_message.intent == "routing_error":
                self._record_message(next_message)
                return next_message

            current_message = next_message

        # Maximum iterations reached.
        logger.error(
            "Maximum workflow iterations reached: %s",
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