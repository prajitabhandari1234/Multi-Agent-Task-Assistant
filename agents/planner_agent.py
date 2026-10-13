
import logging
import re

from models.agent_message import AgentMessage


# Create a logger for the Planner Agent
logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Analyse a user task and generate structured,
    context-aware subtasks for the Worker Agent.

    Responsibilities:
    - Validate incoming tasks
    - Identify the task category
    - Preserve the user's original context
    - Generate relevant subtasks
    - Provide execution constraints
    """

    def __init__(self):
        self.name = "planner"

    def _identify_task_category(self, task: str) -> str:
        """
        Identify the task category using keyword matching.

        This is a rule-based classification method.
        It does not require a Gemini API request.
        """

        task_lower = task.lower()

        # Use word boundaries to avoid partial-word matches
        def contains_keyword(keywords):
            return any(
                re.search(
                    rf"\b{re.escape(keyword)}\b",
                    task_lower,
                )
                for keyword in keywords
            )

        # Academic planning and study-related tasks
        if contains_keyword([
            "study",
            "studying",
            "student",
            "students",
            "university",
            "college",
            "subject",
            "subjects",
            "course",
            "courses",
            "semester",
            "timetable",
            "exam",
            "exams",
            "revision",
            "learning",
        ]):
            return "study"

        # Presentation tasks
        if contains_keyword([
            "presentation",
            "presentations",
            "slides",
            "powerpoint",
            "slideshow",
        ]):
            return "presentation"

        # Report and assignment tasks
        if contains_keyword([
            "report",
            "reports",
            "assignment",
            "assignments",
            "essay",
            "essays",
        ]):
            return "report"

        # General task planning
        return "general"

    def _generate_subtasks(self, task: str) -> list[str]:
        """
        Generate four subtasks based on the identified
        task category.
        """

        category = self._identify_task_category(task)

        if category == "study":
            return [
                "Identify subjects, topics and learning goals",
                "Prioritise topics based on difficulty and deadlines",
                "Allocate study sessions across available days",
                "Include breaks, revision and progress checks",
            ]

        if category == "presentation":
            return [
                "Identify the presentation topic and audience",
                "Prepare a logical slide outline",
                "Develop key points for each slide",
                "Suggest visuals and presentation improvements",
            ]

        if category == "report":
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
        Process an incoming task and return a structured
        message containing subtasks and execution constraints.
        """

        logger.info(
            "Planner received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        # Extract and validate the task
        raw_task = message.content.get("task", "")

        task = (
            raw_task.strip()
            if isinstance(raw_task, str)
            else ""
        )

        if not task:
            logger.warning(
                "Planner received an empty task"
            )

            return AgentMessage(
                sender=self.name,
                receiver=message.sender,
                intent="planning_failed",
                content={
                    "status": "error",
                    "reason": "Task cannot be empty",
                },
            )

        # Identify task category
        category = self._identify_task_category(task)

        # Generate task-specific subtasks
        subtasks = self._generate_subtasks(task)

        # Send structured instructions to the Worker Agent
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
                "preserve_user_context": True,
                "avoid_unsupported_assumptions": True,
                "task_category": category,
            },
        )

        logger.info(
            "Planner generated %s subtasks | category=%s | task=%s",
            len(subtasks),
            category,
            task,
        )

        return response
