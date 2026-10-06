"""
FastAPI endpoints for the multi-agent workflow.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from models.agent_message import AgentMessage
from orchestration.orchestrator import Orchestrator


# Create router for multi-agent workflow endpoints
router = APIRouter(
    prefix="/api/workflow",
    tags=["Multi-Agent Workflow"],
)


class WorkflowRequest(BaseModel):
    """
    Input model for a multi-agent workflow request.
    """

    task: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Task to be processed by the agents",
    )


class WorkflowResponse(BaseModel):
    """
    Response returned after the multi-agent workflow finishes.
    """

    # Unique identifier for tracing this workflow
    workflow_id: str

    # Final structured message returned by the workflow
    result: AgentMessage

    # Number of workflow steps completed
    steps: int

    # Complete history of messages exchanged between agents
    message_history: list[AgentMessage]


@router.post("/run", response_model=WorkflowResponse)
def run_workflow(request: WorkflowRequest):
    """
    Execute the Planner -> Worker -> Reviewer workflow
    using the multi-agent orchestrator.
    """

    # Create a new orchestrator for each API request
    orchestrator = Orchestrator(
        max_iterations=5
    )

    # Run the complete multi-agent workflow
    result = orchestrator.run(
        request.task
    )

    # Return the final result and workflow trace
    return WorkflowResponse(
        workflow_id=orchestrator.workflow_id,
        result=result,
        steps=orchestrator.step_count,
        message_history=orchestrator.message_history,
    )