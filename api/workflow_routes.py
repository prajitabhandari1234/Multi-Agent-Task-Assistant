"""
FastAPI endpoints for the multi-agent workflow.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from models.agent_message import AgentMessage
from orchestration.orchestrator import Orchestrator


router = APIRouter(
    prefix="/api/workflow",
    tags=["Multi-Agent Workflow"]
)


class WorkflowRequest(BaseModel):
    """Input model for a workflow request."""

    task: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Task to be processed by the agents"
    )


class WorkflowResponse(BaseModel):
    """Response returned after the workflow finishes."""

    result: AgentMessage
    steps: int
    message_history: list[AgentMessage]


@router.post("/run", response_model=WorkflowResponse)
def run_workflow(request: WorkflowRequest):
    """
    Execute Planner -> Worker -> Reviewer
    using the multi-agent orchestrator.
    """

    orchestrator = Orchestrator(max_iterations=5)

    result = orchestrator.run(request.task)

    return WorkflowResponse(
        result=result,
        steps=orchestrator.step_count,
        message_history=orchestrator.message_history
    )