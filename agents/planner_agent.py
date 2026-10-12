
import logging

from models.agent_message import AgentMessage

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Analyse a user task and produce structured,
    task-specific subtasks for the Worker Agent.
    """

    def __init__(self):
        self.name = "planner"

    def _generate_subtasks(self, task: str) -> list[str]:
        """
        Generate subtasks based on the task category.
        """

        task_lower = task.lower()

        if any(word in task_lower for word in [
            "study", "exam", "revision"
        ]):
            return [
                "Identify subjects, topics and learning goals",
                "Prioritise topics based on difficulty and deadlines",
                "Allocate study sessions across available days",
                "Include breaks, revision and progress checks",
            ]

        if any(word in task_lower for word in [
            "presentation", "slides", "powerpoint"
        ]):
            return [
                "Identify the presentation topic and audience",
                "Prepare a logical slide outline",
                "Develop key points for each slide",
                "Suggest visuals and presentation improvements",
            ]

        if any(word in task_lower for word in [
            "report", "assignment", "essay"
        ]):
            return [
                "Identify the requirements and expected deliverables",
                "Prepare a structured outline",
                "Identify research and supporting evidence needed",
                "Develop a drafting and review plan",
            ]

        return [
            f"Clarify the objective and requirements of: {task}",
            "Break the work into manageable activities",
            "Organise activities into a logical sequence",
            "Identify completion criteria and review steps",
        ]

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process an incoming task and prepare
        a structured plan.
        """

        logger.info(
            "Planner received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        raw_task = message.content.get("task", "")

        task = raw_task.strip() if isinstance(raw_task, str) else ""

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

        subtasks = self._generate_subtasks(task)

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

        logger.info(
            "Planner generated %s subtasks for task: %s",
            len(subtasks),
            task,
        )

        return response
