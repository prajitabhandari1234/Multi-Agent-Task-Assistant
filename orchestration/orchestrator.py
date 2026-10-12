
import logging
import uuid
from typing import List

from agents.planner_agent import PlannerAgent
from agents.worker_agent import WorkerAgent
from agents.reviewer_agent import ReviewerAgent
from models.agent_message import AgentMessage


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates communication between the Planner,
    Worker and Reviewer agents.

    Supports:
    - Structured message routing
    - Workflow logging and tracing
    - Reviewer feedback and revisions
    - Maximum iteration guardrails
    - Agent error handling
    """

    def __init__(
        self,
        max_iterations: int = 10,
        max_revisions: int = 2,
    ):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        if max_revisions < 0:
            raise ValueError("max_revisions cannot be negative")

        # Initialise the specialised agents
        self.planner = PlannerAgent()
        self.worker = WorkerAgent()
        self.reviewer = ReviewerAgent()

        # Workflow guardrails
        self.max_iterations = max_iterations
        self.max_revisions = max_revisions

        # Workflow state
        self.step_count = 0
        self.revision_count = 0
        self.workflow_id = ""

        # Complete workflow message history
        self.message_history: List[AgentMessage] = []

        # Available agents
        self.agents = {
            "planner": self.planner,
            "worker": self.worker,
            "reviewer": self.reviewer,
        }

    def _record_message(self, message: AgentMessage) -> None:
        """
        Store and log a workflow message.
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

    def _create_failure(
        self,
        intent: str,
        reason: str,
        **details,
    ) -> AgentMessage:
        """
        Create and record a structured failure message.
        """

        failure_message = AgentMessage(
            sender="orchestrator",
            receiver="user",
            intent=intent,
            content={
                "status": "error",
                "reason": reason,
                **details,
            },
        )

        self._record_message(failure_message)

        return failure_message

    def _route(self, message: AgentMessage) -> AgentMessage:
        """
        Route a structured message to the correct agent.
        """

        receiver = message.receiver

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

        agent = self.agents[receiver]

        try:
            response = agent.process(message)

            if not isinstance(response, AgentMessage):
                raise TypeError(
                    "Agent must return an AgentMessage"
                )

            return response

        except Exception:
            logger.exception(
                "Workflow %s | Agent '%s' failed",
                self.workflow_id,
                receiver,
            )

            return AgentMessage(
                sender="orchestrator",
                receiver="user",
                intent="agent_error",
                content={
                    "status": "error",
                    "agent": receiver,
                    "reason": "Agent processing failed",
                },
            )

    def run(self, task: str) -> AgentMessage:
        """
        Execute the complete multi-agent workflow.

        Normal flow:
        User -> Planner -> Worker -> Reviewer
        -> Orchestrator

        Revision flow:
        Reviewer -> Worker -> Reviewer

        Stops on approval, failure or guardrail limit.
        """

        # Reset state for each workflow run
        self.step_count = 0
        self.revision_count = 0
        self.message_history = []

        # Create a unique workflow identifier
        self.workflow_id = str(uuid.uuid4())[:8]

        if not isinstance(task, str) or not task.strip():
            return self._create_failure(
                intent="invalid_task",
                reason="Task cannot be empty",
            )

        logger.info(
            "Workflow %s | START | task=%s",
            self.workflow_id,
            task,
        )

        # Initial message to the Planner Agent
        current_message = AgentMessage(
            sender="user",
            receiver="planner",
            intent="plan_task",
            content={
                "task": task.strip(),
            },
        )

        while self.step_count < self.max_iterations:

            self.step_count += 1

            # Record current message
            self._record_message(current_message)

            # Workflow successfully approved
            if (
                current_message.receiver == "orchestrator"
                and current_message.intent == "review_approved"
            ):
                logger.info(
                    "Workflow %s | COMPLETED | steps=%s | revisions=%s",
                    self.workflow_id,
                    self.step_count,
                    self.revision_count,
                )

                return current_message

            # Stop on known agent failures
            if current_message.intent in {
                "planning_failed",
                "execution_failed",
                "routing_error",
                "agent_error",
            }:
                logger.error(
                    "Workflow %s | FAILED | intent=%s",
                    self.workflow_id,
                    current_message.intent,
                )

                return current_message

            # Handle Reviewer revision requests
            if current_message.intent == "revision_required":

                # Only Reviewer can request a revision
                if (
                    current_message.sender != "reviewer"
                    or current_message.receiver != "worker"
                ):
                    return self._create_failure(
                        intent="routing_error",
                        reason="Invalid revision request route",
                    )

                # Stop before allowing an extra revision
                if self.revision_count >= self.max_revisions:
                    logger.error(
                        "Workflow %s | REVISION LIMIT EXCEEDED",
                        self.workflow_id,
                    )

                    return self._create_failure(
                        intent="revision_limit_exceeded",
                        reason="Maximum revisions exceeded",
                        revisions=self.revision_count,
                    )

                self.revision_count += 1

                logger.warning(
                    "Workflow %s | REVISION %s of %s",
                    self.workflow_id,
                    self.revision_count,
                    self.max_revisions,
                )

            # Route the message to the next agent
            next_message = self._route(current_message)

            # Handle routing and unexpected agent errors
            if next_message.intent in {
                "routing_error",
                "agent_error",
            }:
                self._record_message(next_message)

                return next_message

            # Move to the next message
            current_message = next_message

        # Maximum iteration limit reached
        logger.error(
            "Workflow %s | MAX ITERATIONS | limit=%s",
            self.workflow_id,
            self.max_iterations,
        )

        return self._create_failure(
            intent="max_iterations_exceeded",
            reason="Maximum workflow iterations reached",
            steps=self.step_count,
        )
