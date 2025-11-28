"""
Agent Controller

Main autonomous agent loop implementing SENSE → PLAN → ACT → OBSERVE → REFLECT.
"""

import logging
import json
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path
from openai import AsyncOpenAI

from .logger import AgentLogger
from .tools import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for agent execution."""

    max_iterations: int = 10
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    log_level: str = "INFO"


@dataclass
class AgentResult:
    """Result from agent execution."""

    output: Dict[str, Any]
    logs: List[Dict[str, Any]]
    iteration_count: int
    status: str  # "completed", "timeout", "failed"
    session_id: str


class AgentController:
    """
    Autonomous agent controller.

    Executes SENSE → PLAN → ACT → OBSERVE → REFLECT loop to achieve user goals.
    """

    def __init__(
        self,
        config: AgentConfig,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize agent controller.

        Args:
            config: Agent configuration
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key for LLM calls
            anthropic_api_key: Anthropic API key (optional)
        """
        self.config = config
        self.logger = AgentLogger()
        self.tools = ToolRegistry(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )
        self.llm_client = AsyncOpenAI(api_key=openai_api_key)

        # Load prompts
        prompts_dir = Path(__file__).parent / "prompts"
        with open(prompts_dir / "system.txt", "r") as f:
            self.system_prompt = f.read()
        with open(prompts_dir / "planning.txt", "r") as f:
            self.planning_prompt_template = f.read()
        with open(prompts_dir / "reflection.txt", "r") as f:
            self.reflection_prompt_template = f.read()

    async def run(self, goal: str, user_id: str) -> AgentResult:
        """
        Main entry point for agent execution.

        Args:
            goal: Natural language goal from user
            user_id: UUID of the user

        Returns:
            AgentResult with output, logs, and metadata
        """
        session_id = uuid.uuid4()
        self.logger.start_session(session_id, goal, user_id)

        logger.info(f"Starting agent session {session_id} for user {user_id}")
        logger.info(f"Goal: {goal}")

        iteration = 0
        context = {"user_id": user_id, "iteration_history": []}

        try:
            while iteration < self.config.max_iterations:
                iteration += 1
                logger.info(f"=== Iteration {iteration}/{self.config.max_iterations} ===")

                # SENSE: Gather user context (only on first iteration)
                if iteration == 1:
                    context = await self._sense(user_id, context, session_id, iteration)

                # PLAN: Decide next action
                plan = await self._plan(goal, context, session_id, iteration)

                # Check if we should complete
                if plan.get("action_type") == "COMPLETE":
                    output = plan.get("output", {})
                    self.logger.log(
                        session_id,
                        "COMPLETE",
                        {"output": output, "reasoning": plan.get("reasoning", "")},
                        iteration,
                    )
                    self.logger.complete_session(session_id, "completed", output)

                    return AgentResult(
                        output=output,
                        logs=self.logger.get_logs(session_id),
                        iteration_count=iteration,
                        status="completed",
                        session_id=str(session_id),
                    )

                # Check if we need clarification
                if plan.get("action_type") == "CLARIFY":
                    question = plan.get("question", "Need more information")
                    self.logger.log(
                        session_id,
                        "CLARIFY",
                        {"question": question, "reasoning": plan.get("reasoning", "")},
                        iteration,
                    )
                    self.logger.complete_session(
                        session_id, "needs_clarification", {"question": question}
                    )

                    return AgentResult(
                        output={"question": question, "type": "clarification_needed"},
                        logs=self.logger.get_logs(session_id),
                        iteration_count=iteration,
                        status="needs_clarification",
                        session_id=str(session_id),
                    )

                # ACT: Execute the planned action
                result = await self._act(plan, session_id, iteration)

                # OBSERVE: Log the result
                self._observe(plan, result, session_id, iteration)

                # REFLECT: Evaluate progress
                reflection = await self._reflect(
                    plan, result, goal, context, session_id, iteration
                )

                # Update context with reflection
                context["last_reflection"] = reflection
                context["iteration_history"].append(
                    {
                        "iteration": iteration,
                        "action": plan.get("action_type"),
                        "tool": plan.get("tool"),
                        "reflection": reflection,
                    }
                )

            # Max iterations reached
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached")
            self.logger.log(
                session_id,
                "COMPLETE",
                {
                    "status": "timeout",
                    "message": f"Max iterations ({self.config.max_iterations}) reached",
                    "context": context,
                },
            )
            self.logger.complete_session(session_id, "timeout")

            return AgentResult(
                output={
                    "message": "Agent reached maximum iterations without completing goal",
                    "partial_context": context,
                },
                logs=self.logger.get_logs(session_id),
                iteration_count=iteration,
                status="timeout",
                session_id=str(session_id),
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            self.logger.log(session_id, "ERROR", {"error": str(e)})
            self.logger.complete_session(session_id, "failed")

            return AgentResult(
                output={"error": str(e)},
                logs=self.logger.get_logs(session_id),
                iteration_count=iteration,
                status="failed",
                session_id=str(session_id),
            )

    async def _sense(
        self,
        user_id: str,
        context: Dict[str, Any],
        session_id: uuid.UUID,
        iteration: int,
    ) -> Dict[str, Any]:
        """
        SENSE: Gather user context.

        Args:
            user_id: UUID of the user
            context: Current context dictionary
            session_id: Session UUID
            iteration: Current iteration number

        Returns:
            Updated context dictionary
        """
        logger.info("SENSE: Gathering user context")

        try:
            # Get user context using tool
            user_context = await self.tools.execute_tool(
                "get-user-context", {"user_id": user_id}
            )

            context["user_context"] = user_context

            self.logger.log(
                session_id,
                "SENSE",
                {
                    "user_context": user_context,
                    "message": "Successfully gathered user learning context",
                },
                iteration,
            )

            return context

        except Exception as e:
            logger.error(f"Error in SENSE phase: {e}", exc_info=True)
            self.logger.log(
                session_id, "SENSE", {"error": str(e), "status": "failed"}, iteration
            )
            # Return context as-is if SENSE fails
            return context

    async def _plan(
        self,
        goal: str,
        context: Dict[str, Any],
        session_id: uuid.UUID,
        iteration: int,
    ) -> Dict[str, Any]:
        """
        PLAN: Decide next action using LLM.

        Args:
            goal: User's goal
            context: Current context
            session_id: Session UUID
            iteration: Current iteration number

        Returns:
            Plan dictionary with action_type, tool, args, reasoning
        """
        logger.info("PLAN: Deciding next action")

        # Format the planning prompt
        tool_schemas = self.tools.get_tool_schemas_for_prompt()

        # Format iteration history
        iteration_history = []
        for hist in context.get("iteration_history", []):
            iteration_history.append(
                f"Iteration {hist['iteration']}: {hist['action']} - {hist.get('reflection', '')}"
            )
        iteration_history_str = "\n".join(iteration_history) if iteration_history else "No previous iterations"

        planning_prompt = self.planning_prompt_template.format(
            goal=goal,
            context=json.dumps(context.get("user_context", {}), indent=2),
            iteration_history=iteration_history_str,
            tool_schemas=tool_schemas,
        )

        try:
            # Call LLM for planning
            response = await self.llm_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": planning_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=500,
            )

            response_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM planning response: {response_text}")

            # Parse JSON response
            plan = self._parse_json_response(response_text)

            self.logger.log(
                session_id,
                "PLAN",
                {
                    "plan": plan,
                    "llm_response": response_text,
                    "iteration": iteration,
                },
                iteration,
            )

            return plan

        except Exception as e:
            logger.error(f"Error in PLAN phase: {e}", exc_info=True)
            self.logger.log(
                session_id, "PLAN", {"error": str(e), "status": "failed"}, iteration
            )
            # Fallback plan
            return {
                "action_type": "COMPLETE",
                "output": {"error": f"Planning failed: {str(e)}"},
                "reasoning": "Error in planning phase",
            }

    async def _act(
        self, plan: Dict[str, Any], session_id: uuid.UUID, iteration: int
    ) -> Dict[str, Any]:
        """
        ACT: Execute the planned action.

        Args:
            plan: Plan from PLAN phase
            session_id: Session UUID
            iteration: Current iteration number

        Returns:
            Execution result
        """
        action_type = plan.get("action_type")
        logger.info(f"ACT: Executing action type: {action_type}")

        if action_type != "TOOL_CALL":
            return {"status": "skipped", "reason": f"Action type is {action_type}"}

        tool_name = plan.get("tool")
        args = plan.get("args", {})

        try:
            result = await self.tools.execute_tool(tool_name, args)

            self.logger.log(
                session_id,
                "ACT",
                {
                    "tool": tool_name,
                    "args": args,
                    "result_preview": str(result)[:200] + "...",
                },
                iteration,
            )

            return result

        except Exception as e:
            logger.error(f"Error in ACT phase: {e}", exc_info=True)
            error_result = {"error": str(e), "tool": tool_name, "args": args}
            self.logger.log(session_id, "ACT", error_result, iteration)
            return error_result

    def _observe(
        self,
        plan: Dict[str, Any],
        result: Dict[str, Any],
        session_id: uuid.UUID,
        iteration: int,
    ) -> None:
        """
        OBSERVE: Log the execution result.

        Args:
            plan: Plan that was executed
            result: Result from execution
            session_id: Session UUID
            iteration: Current iteration number
        """
        logger.info("OBSERVE: Logging execution result")

        # Determine if execution was successful
        has_error = "error" in result
        status = "failed" if has_error else "success"

        observation = {
            "tool": plan.get("tool"),
            "status": status,
            "result_summary": self._summarize_result(result),
        }

        if has_error:
            observation["error"] = result["error"]

        self.logger.log(session_id, "OBSERVE", observation, iteration)

    async def _reflect(
        self,
        plan: Dict[str, Any],
        result: Dict[str, Any],
        goal: str,
        context: Dict[str, Any],
        session_id: uuid.UUID,
        iteration: int,
    ) -> str:
        """
        REFLECT: Evaluate the result and determine next steps.

        Args:
            plan: Plan that was executed
            result: Result from execution
            goal: Original goal
            context: Current context
            session_id: Session UUID
            iteration: Current iteration number

        Returns:
            Reflection string
        """
        logger.info("REFLECT: Evaluating progress")

        # Format reflection prompt
        reflection_prompt = self.reflection_prompt_template.format(
            goal=goal,
            user_context=json.dumps(context.get("user_context", {}), indent=2),
            tool_name=plan.get("tool", "unknown"),
            args=json.dumps(plan.get("args", {}), indent=2),
            reasoning=plan.get("reasoning", ""),
            result=json.dumps(self._summarize_result(result), indent=2),
        )

        try:
            # Call LLM for reflection
            response = await self.llm_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": reflection_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=300,
            )

            reflection = response.choices[0].message.content.strip()
            logger.debug(f"Reflection: {reflection}")

            self.logger.log(
                session_id,
                "REFLECT",
                {"reflection": reflection, "iteration": iteration},
                iteration,
            )

            return reflection

        except Exception as e:
            logger.error(f"Error in REFLECT phase: {e}", exc_info=True)
            fallback_reflection = f"Error in reflection: {str(e)}"
            self.logger.log(
                session_id,
                "REFLECT",
                {"error": str(e), "fallback": fallback_reflection},
                iteration,
            )
            return fallback_reflection

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {response_text}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")

    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a result for logging (to avoid huge logs).

        Args:
            result: Full result dictionary

        Returns:
            Summarized result
        """
        summary = {}

        # Handle common result structures
        if "error" in result:
            summary["error"] = result["error"]

        if "results" in result:
            summary["results_count"] = len(result["results"])
            summary["results_preview"] = result["results"][:2]  # First 2 items

        if "insights" in result:
            summary["insights_count"] = len(result["insights"])
            summary["insights_preview"] = [
                {"title": i.get("title", "")} for i in result["insights"][:2]
            ]

        if "ragas_scores" in result:
            summary["ragas_scores"] = result["ragas_scores"]

        if "week" in result:
            summary["week"] = result["week"]

        if "topics" in result:
            summary["topics"] = result["topics"]

        # If no specific fields matched, return first 500 chars of string representation
        if not summary:
            summary["preview"] = str(result)[:500]

        return summary
