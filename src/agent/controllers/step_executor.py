"""
Step Executor

Executes individual phases of the SENSE → PLAN → ACT → OBSERVE → REFLECT cycle.
"""

import json
import logging
import os
import uuid
from typing import Dict, Any
from openai import AsyncOpenAI

from agent.logger import AgentLogger
from agent.tools import ToolRegistry
from src.agent.utils.response_parser import (
    parse_json_response,
    summarize_result,
    format_iteration_history,
)

logger = logging.getLogger(__name__)


class StepExecutor:
    """
    Executes individual agent steps.

    Handles SENSE, PLAN, ACT, OBSERVE, and REFLECT phases of the agent loop.
    """

    def __init__(
        self,
        tools: ToolRegistry,
        llm_client: AsyncOpenAI,
        agent_logger: AgentLogger,
        system_prompt: str,
        planning_prompt_template: str,
        reflection_prompt_template: str,
        llm_model: str,
        temperature: float,
    ):
        """
        Initialize step executor.

        Args:
            tools: Tool registry for executing tools
            llm_client: OpenAI client for LLM calls
            agent_logger: Logger for agent activities
            system_prompt: System prompt for LLM
            planning_prompt_template: Template for planning prompts
            reflection_prompt_template: Template for reflection prompts
            llm_model: LLM model to use
            temperature: Temperature for LLM calls
        """
        self.tools = tools
        self.llm_client = llm_client
        self.logger = agent_logger
        self.system_prompt = system_prompt
        self.planning_prompt_template = planning_prompt_template
        self.reflection_prompt_template = reflection_prompt_template
        self.llm_model = llm_model
        self.temperature = temperature

    async def sense(
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

    async def plan(
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
        iteration_history_str = format_iteration_history(
            context.get("iteration_history", [])
        )

        # Add environment info (for web search approval workflow)
        skip_approval = os.getenv("SKIP_WEB_SEARCH_APPROVAL", "false")
        env_info = f"\n\n## Environment Variables\n\nSKIP_WEB_SEARCH_APPROVAL = {skip_approval}"

        planning_prompt = (
            self.planning_prompt_template.format(
                goal=goal,
                context=json.dumps(context.get("user_context", {}), indent=2),
                iteration_history=iteration_history_str,
                tool_schemas=tool_schemas,
            )
            + env_info
        )

        try:
            # Call LLM for planning
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": planning_prompt},
                ],
                temperature=self.temperature,
                max_tokens=500,
            )

            response_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM planning response: {response_text}")

            # Parse JSON response
            plan = parse_json_response(response_text)

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
            # Fallback plan on error
            return {
                "action_type": "COMPLETE",
                "reasoning": f"Error in planning: {str(e)}",
                "output": {"error": str(e), "type": "planning_error"},
            }

    async def act(
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

    def observe(
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
            "result_summary": summarize_result(result),
        }

        if has_error:
            observation["error"] = result["error"]

        self.logger.log(session_id, "OBSERVE", observation, iteration)

    async def reflect(
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
            result=json.dumps(summarize_result(result), indent=2),
        )

        try:
            # Call LLM for reflection
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": reflection_prompt},
                ],
                temperature=self.temperature,
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

    async def generate_partial_result(
        self, goal: str, context: Dict[str, Any], session_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Generate a partial result when max iterations reached.

        Creates a digest with whatever content was gathered, along with
        warnings about what was missing and assumptions made.

        Args:
            goal: Original user goal
            context: Current context with iteration history
            session_id: Session UUID

        Returns:
            Partial result dictionary with digest and warnings
        """
        logger.info("Generating partial result from gathered content")

        # Collect all search results from iteration history
        all_results = []
        search_iterations = []
        sources = []

        for hist in context.get("iteration_history", []):
            if hist.get("tool") == "search-content":
                search_iterations.append(hist["iteration"])

        # Extract actual search results from the agent's tool execution context
        if "search_results" in context:
            all_results = context.get("search_results", [])
            # Extract sources with citations
            for result in all_results[:10]:  # Limit to 10 sources
                if isinstance(result, dict):
                    sources.append(
                        {
                            "title": result.get("title", "Untitled"),
                            "url": result.get("url", ""),
                            "snippet": result.get("snippet", "")[:150],
                            "published_at": result.get("published_at", ""),
                        }
                    )

        # Use LLM to synthesize whatever we found
        synthesis_prompt = f"""
You are helping create a learning digest, but the agent reached maximum iterations before completing.

Goal: {goal}

User Context: {json.dumps(context.get("user_context", {}), indent=2)}

Iterations Completed: {len(context.get("iteration_history", []))}

Search Attempts: {search_iterations}

Last Reflection: {context.get("last_reflection", "None")}

Sources Found ({len(sources)} items):
{json.dumps(sources, indent=2) if sources else "No sources found"}

TASK: Generate a partial learning digest with:
1. A warning message explaining what happened
2. Any insights you can provide based on the goal, context, and sources (even if limited)
3. Recommendations for what the user should search for manually
4. Acknowledgment of what was missing or assumed
5. If sources were found, mention them and what they cover

Format your response as JSON:
{{
  "warning": "Message about partial results and what was assumed",
  "insights": ["Insight 1 based on available sources", "Insight 2", ...],
  "sources_summary": "Brief summary of what the {len(sources)} sources cover (if any)",
  "recommendations": ["What to search for", ...],
  "missing": ["What couldn't be found", ...],
  "assumptions": ["What was assumed due to lack of data", ...],
  "status": "partial"
}}
"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": synthesis_prompt},
                ],
                temperature=self.temperature,
                max_tokens=800,
            )

            response_text = response.choices[0].message.content.strip()
            partial_result = parse_json_response(response_text)

            # Add sources to the result
            partial_result["sources"] = sources[:10]
            partial_result["search_iterations"] = search_iterations

            self.logger.log(
                session_id,
                "PARTIAL_RESULT",
                {
                    "sources_count": len(sources),
                    "search_iterations": search_iterations,
                    "status": "partial",
                },
                len(context.get("iteration_history", [])),
            )

            return partial_result

        except Exception as e:
            logger.error(f"Error generating partial result: {e}", exc_info=True)
            # Return a basic fallback
            return {
                "warning": "Agent reached maximum iterations without completing the goal.",
                "insights": ["Unable to generate insights due to error in synthesis."],
                "recommendations": ["Please try running the query again or simplify the goal."],
                "error": str(e),
                "status": "partial",
                "sources": sources[:10],
            }
