
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

    Features:
    - Structured inter-agent communication
    - Message routing and validation
    - Workflow logging and tracing
    - Reviewer feedback and revision handling
    - Maximum iteration and revision guardrails
    - Structured agent error handling
    - Workflow state and message history
    """

    def __init__(
        self,
        max_iterations: int = 10,
        max_revisions: int = 2,
    ):
        # Validate workflow configuration
        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be at least 1"
            )

        if max_revisions < 0:
            raise ValueError(
                "max_revisions cannot be negative"
            )

        # Initialise specialised agents
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

        # Message history
        self.message_history: List[AgentMessage] = []

        # Agent registry
        self.agents = {
            "planner": self.planner,
            "worker": self.worker,
            "reviewer": self.reviewer,
        }

        # Allowed communication routes
        self.allowed_routes = {
            ("user", "planner", "plan_task"),
            ("planner", "worker", "execute_subtasks"),
            ("worker", "reviewer", "execution_result"),
            ("reviewer", "worker", "revision_required"),
        }

        # Recognised terminal failures
        self.failure_intents = {
            "invalid_task",
            "planning_failed",
            "execution_failed",
            "routing_error",
            "agent_error",
            "revision_limit_exceeded",
            "max_iterations_exceeded",
        }

    def _reset_workflow(self) -> None:
        """
        Reset workflow state before each execution.
        """

        self.step_count = 0
        self.revision_count = 0
        self.message_history = []
        self.workflow_id = uuid.uuid4().hex[:8]

    def _record_message(
        self,
        message: AgentMessage,
    ) -> None:
        """
        Record and log a workflow message.
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

        logger.error(
            "Workflow %s | FAILED | intent=%s | reason=%s",
            self.workflow_id,
            intent,
            reason,
        )

        return failure_message

    def _is_valid_route(
        self,
        message: AgentMessage,
    ) -> bool:
        """
        Check whether the message follows an allowed
        communication route.
        """

        route = (
            message.sender,
            message.receiver,
            message.intent,
        )

        return route in self.allowed_routes

    def _is_valid_approval(
        self,
        message: AgentMessage,
    ) -> bool:
        """
        Validate that approval originates from the
        Reviewer and contains an approved result.
        """

        return (
            message.sender == "reviewer"
            and message.receiver == "orchestrator"
            and message.intent == "review_approved"
            and isinstance(message.content, dict)
            and message.content.get("status") == "approved"
            and isinstance(
                message.content.get("final_output"),
                str,
            )
            and bool(
                message.content.get(
                    "final_output", ""
                ).strip()
            )
        )

    def _route(
        self,
        message: AgentMessage,
    ) -> AgentMessage:
        """
        Route a structured message to the
        appropriate specialised agent.
        """

        receiver = message.receiver

        # Validate receiver
        if receiver not in self.agents:
            logger.error(
                "Workflow %s | Unknown receiver: %s",
                self.workflow_id,
                receiver,
            )

            return AgentMessage(
                sender="orchestrator",
                receiver="user",
                intent="routing_error",
                content={
                    "status": "error",
                    "reason": (
                        f"Unknown receiver: {receiver}"
                    ),
                },
            )

        # Validate sender, receiver and intent
        if not self._is_valid_route(message):
            logger.error(
                "Workflow %s | Invalid route: %s -> %s | %s",
                self.workflow_id,
                message.sender,
                message.receiver,
                message.intent,
            )

            return AgentMessage(
                sender="orchestrator",
                receiver="user",
                intent="routing_error",
                content={
                    "status": "error",
                    "reason": (
                        "Invalid agent communication route"
                    ),
                },
            )

        agent = self.agents[receiver]

        try:
            response = agent.process(message)

            # Ensure the agent returns a structured message
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

    def run(
        self,
        task: str,
    ) -> AgentMessage:
        """
        Execute the complete multi-agent workflow.

        Normal workflow:
        User -> Planner -> Worker -> Reviewer
        -> Orchestrator

        Revision workflow:
        Reviewer -> Worker -> Reviewer

        Stops when:
        - Reviewer approves the result
        - An agent fails
        - A routing error occurs
        - Maximum revisions are reached
        - Maximum iterations are reached
        """

        # Reset workflow state
        self._reset_workflow()

        # Validate input
        if not isinstance(task, str) or not task.strip():
            return self._create_failure(
                intent="invalid_task",
                reason="Task cannot be empty",
            )

        task = task.strip()

        logger.info(
            "Workflow %s | START | task=%s",
            self.workflow_id,
            task,
        )

        # Create initial user message
        current_message = AgentMessage(
            sender="user",
            receiver="planner",
            intent="plan_task",
            content={
                "task": task,
            },
        )

        # Execute workflow with iteration guardrail
        while self.step_count < self.max_iterations:

            self.step_count += 1

            # Record current message
            self._record_message(current_message)

            # Step 1: Check for successful approval
            if current_message.intent == "review_approved":

                if not self._is_valid_approval(
                    current_message
                ):
                    return self._create_failure(
                        intent="routing_error",
                        reason=(
                            "Invalid Reviewer approval message"
                        ),
                    )

                logger.info(
                    "Workflow %s | COMPLETED | "
                    "steps=%s | revisions=%s",
                    self.workflow_id,
                    self.step_count,
                    self.revision_count,
                )

                return current_message

            # Step 2: Stop on recognised failures
            if current_message.intent in self.failure_intents:

                logger.error(
                    "Workflow %s | STOPPED | intent=%s",
                    self.workflow_id,
                    current_message.intent,
                )

                return current_message

            # Step 3: Process Reviewer revision requests
            if current_message.intent == "revision_required":

                # Validate the revision request
                if (
                    current_message.sender != "reviewer"
                    or current_message.receiver != "worker"
                ):
                    return self._create_failure(
                        intent="routing_error",
                        reason="Invalid revision request route",
                    )

                # Check maximum revision guardrail
                if self.revision_count >= self.max_revisions:

                    logger.error(
                        "Workflow %s | "
                        "REVISION LIMIT EXCEEDED",
                        self.workflow_id,
                    )

                    return self._create_failure(
                        intent="revision_limit_exceeded",
                        reason="Maximum revisions exceeded",
                        revisions=self.revision_count,
                    )

                # Record revision attempt
                self.revision_count += 1

                logger.warning(
                    "Workflow %s | REVISION %s of %s",
                    self.workflow_id,
                    self.revision_count,
                    self.max_revisions,
                )

            # Step 4: Validate route before execution
            if not self._is_valid_route(current_message):

                return self._create_failure(
                    intent="routing_error",
                    reason=(
                        "Invalid workflow message route: "
                        f"{current_message.sender} -> "
                        f"{current_message.receiver} "
                        f"({current_message.intent})"
                    ),
                )

            # Step 5: Route message to the agent
            next_message = self._route(current_message)

            # Step 6: Handle routing or agent errors
            if next_message.intent in {
                "routing_error",
                "agent_error",
            }:
                self._record_message(next_message)

                return next_message

            # Step 7: Validate agent response origin
            if next_message.sender != current_message.receiver:

                return self._create_failure(
                    intent="routing_error",
                    reason=(
                        "Agent response sender does not "
                        "match the expected agent"
                    ),
                )

            # Step 8: Validate next message destination
            if (
                next_message.receiver == "orchestrator"
                and next_message.intent != "review_approved"
            ):
                return self._create_failure(
                    intent="routing_error",
                    reason=(
                        "Unexpected message sent "
                        "to orchestrator"
                    ),
                )

            # Continue workflow
            current_message = next_message

        # Maximum iteration guardrail reached
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
