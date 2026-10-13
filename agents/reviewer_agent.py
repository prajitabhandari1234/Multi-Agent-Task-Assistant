
import json
import logging
import re

from models.agent_message import AgentMessage
from utils.llm_client import generate_response


logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviews the Worker Agent's output.

    Responsibilities:
    - Validate task, subtasks, and results.
    - Check completeness and result counts.
    - Evaluate relevance and consistency using AI.
    - Approve acceptable output.
    - Request revisions when problems are identified.
    """

    def __init__(self):
        self.name = "reviewer"

    def _revision(
        self,
        task: str,
        subtasks: list,
        results: list,
        reason: str,
    ) -> AgentMessage:
        """
        Return structured revision feedback to the Worker.
        """

        logger.warning(
            "Reviewer requested revision: %s",
            reason,
        )

        return AgentMessage(
            sender=self.name,
            receiver="worker",
            intent="revision_required",
            content={
                "status": "rejected",
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "reason": reason,
            },
            constraints={
                "retry": True,
            },
        )

    def _ai_review(
        self,
        task: str,
        subtasks: list[str],
        results: list[str],
    ) -> dict:
        """
        Ask Gemini to review the complete Worker output.
        """

        combined_results = "\n\n".join(
            f"Subtask {index}: {subtask}\n"
            f"Result:\n{result}"
            for index, (subtask, result)
            in enumerate(zip(subtasks, results), start=1)
        )

        prompt = f"""
You are the Reviewer Agent in a multi-agent
task assistant.

Your responsibility is to evaluate the Worker
Agent's output independently.

ORIGINAL USER TASK:
{task}

WORKER OUTPUT:
{combined_results}

Review the output against these criteria:

1. COMPLETENESS
Does the output address every assigned subtask?

2. RELEVANCE
Does the output directly satisfy the original task?

3. CONSISTENCY
Are there contradictions between different subtasks?

4. ACCURACY
Are calculations, totals, dates, and schedules
internally consistent where they can be checked?

5. ASSUMPTIONS
Are missing user details clearly identified as
assumptions rather than presented as facts?

6. QUALITY
Is the output clear, practical, and sufficiently
structured for the user's request?

Important rules:
- Do not reject merely because the user omitted
  information that is not essential.
- Reasonable assumptions are acceptable when
  explicitly labelled.
- Do not invent requirements.
- Do not require a specific output format unless
  the user requested it.
- Reject only when you identify a meaningful issue.
- Give actionable feedback explaining what the
  Worker must correct.
- Evaluate the entire response, not just one subtask.

Return ONLY valid JSON using this structure:

{{
    "approved": true,
    "reason": "Brief explanation of the decision",
    "issues": []
}}

If revision is necessary, return:

{{
    "approved": false,
    "reason": "Brief explanation of the decision",
    "issues": [
        "Specific issue and required correction"
    ]
}}

Do not include Markdown code fences.
"""

        response = generate_response(prompt)

        if not isinstance(response, str) or not response.strip():
            raise ValueError("Empty AI review response")

        cleaned = response.strip()

        # Accept JSON enclosed in Markdown code fences.
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        review = json.loads(cleaned)

        if not isinstance(review, dict):
            raise ValueError("AI review must be a JSON object")

        approved = review.get("approved")
        reason = review.get("reason")
        issues = review.get("issues")

        if not isinstance(approved, bool):
            raise ValueError("Invalid approval value")

        if not isinstance(reason, str):
            raise ValueError("Invalid review reason")

        if not isinstance(issues, list):
            raise ValueError("Invalid review issues")

        if not all(isinstance(issue, str) for issue in issues):
            raise ValueError("Review issues must be strings")

        if not approved and not issues:
            raise ValueError(
                "Rejected review must include actionable issues"
            )

        return {
            "approved": approved,
            "reason": reason.strip(),
            "issues": issues,
        }

    def process(self, message: AgentMessage) -> AgentMessage:
        """
        Validate and review the Worker Agent's output.
        """

        logger.info(
            "Reviewer received message from %s with intent %s",
            message.sender,
            message.intent,
        )

        if message.intent != "execution_result":
            return self._revision(
                task="",
                subtasks=[],
                results=[],
                reason="Unsupported Reviewer message intent",
            )

        content = message.content

        task = content.get("task", "")
        subtasks = content.get("subtasks", [])
        results = content.get("results", [])
        draft_output = content.get("draft_output", "")

        if not isinstance(task, str):
            task = ""

        if not isinstance(subtasks, list):
            subtasks = []

        if not isinstance(results, list):
            results = []

        if not isinstance(draft_output, str):
            draft_output = ""

        valid_subtasks = (
            bool(subtasks)
            and all(
                isinstance(item, str) and item.strip()
                for item in subtasks
            )
        )

        valid_results = (
            bool(results)
            and all(
                isinstance(item, str) and item.strip()
                for item in results
            )
        )

        # Step 1: Structural validation
        if not (
            task.strip()
            and valid_subtasks
            and valid_results
            and draft_output.strip()
        ):
            return self._revision(
                task,
                subtasks,
                results,
                "Worker output is incomplete or invalid.",
            )

        # Step 2: Result count validation
        if len(results) != len(subtasks):
            return self._revision(
                task,
                subtasks,
                results,
                "Worker result count does not match "
                "the number of subtasks.",
            )

        # Step 3: AI-assisted quality review
        try:
            review = self._ai_review(
                task,
                subtasks,
                results,
            )

        except Exception:
            logger.exception(
                "AI-assisted review failed"
            )

            # Do not silently approve an unreviewed result.
            return self._revision(
                task,
                subtasks,
                results,
                "The AI quality review could not be completed. "
                "Please retry the review.",
            )

        # Step 4: Request revision if quality checks fail
        if not review["approved"]:
            feedback = review["reason"]

            if review["issues"]:
                feedback += "\n\nRequired corrections:\n"

                feedback += "\n".join(
                    f"{index}. {issue}"
                    for index, issue
                    in enumerate(review["issues"], start=1)
                )

            return self._revision(
                task,
                subtasks,
                results,
                feedback,
            )

        # Step 5: Approve reviewed output
        response = AgentMessage(
            sender=self.name,
            receiver="orchestrator",
            intent="review_approved",
            content={
                "status": "approved",
                "task": task,
                "subtasks": subtasks,
                "results": results,
                "final_output": draft_output,
                "review_reason": review["reason"],
            },
            constraints={
                "retry": False,
            },
        )

        logger.info(
            "Reviewer approved output for task: %s",
            task,
        )

        logger.info(
            "Reviewer sending message to %s with intent %s",
            response.receiver,
            response.intent,
        )

        return response
