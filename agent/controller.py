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

                # OBSERVE: Log the result and store in context
                self._observe(plan, result, session_id, iteration)

                # Store search results in context for partial digest generation
                if plan.get("tool") == "search-content" and "results" in result:
                    if "search_results" not in context:
                        context["search_results"] = []
                    context["search_results"].extend(result.get("results", []))

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

            # Max iterations reached - generate best-effort output
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached")

            # Try to generate a partial result with what we have
            partial_output = await self._generate_partial_result(
                goal, context, session_id
            )

            self.logger.log(
                session_id,
                "COMPLETE",
                {
                    "status": "timeout",
                    "message": f"Max iterations ({self.config.max_iterations}) reached",
                    "partial_output": partial_output,
                },
            )
            self.logger.complete_session(session_id, "timeout", partial_output)

            return AgentResult(
                output=partial_output,
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

    async def _generate_partial_result(
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
        # This will be stored in the context if the agent executed search-content
        if "search_results" in context:
            all_results = context.get("search_results", [])
            # Extract sources with citations
            for result in all_results[:10]:  # Limit to 10 sources
                if isinstance(result, dict):
                    sources.append({
                        "title": result.get("title", "Untitled"),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", "")[:150],
                        "published_at": result.get("published_at", ""),
                    })

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
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": synthesis_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=800,
            )

            response_text = response.choices[0].message.content.strip()
            partial_result = self._parse_json_response(response_text)

            # Add metadata and sources
            partial_result["iterations_used"] = len(context.get("iteration_history", []))
            partial_result["max_iterations"] = self.config.max_iterations
            partial_result["goal"] = goal
            partial_result["sources"] = sources  # Include citation links

            return partial_result

        except Exception as e:
            logger.error(f"Error generating partial result: {e}", exc_info=True)

            # Fallback partial result
            return {
                "warning": f"⚠️ Agent reached maximum iterations ({self.config.max_iterations}) without fully completing your goal.",
                "insights": [
                    f"Your learning goal was: {goal}",
                    f"You are currently on Week {context.get('user_context', {}).get('week', 'N/A')}",
                    f"Topics: {', '.join(context.get('user_context', {}).get('topics', []))}",
                ],
                "sources_summary": f"Found {len(sources)} potential sources, but could not synthesize them into a complete digest.",
                "recommendations": [
                    "Try breaking down your goal into smaller, more specific requests",
                    "Search directly for specific topics you want to learn about",
                    "Use the search-content tool with more specific queries",
                ],
                "missing": [
                    "Could not find sufficient relevant content within iteration limit",
                    "May need to refine search criteria or add more content sources",
                ],
                "assumptions": [
                    "Assumed intermediate difficulty level based on user profile",
                    "Could not verify content quality due to iteration limit",
                ],
                "status": "partial",
                "iterations_used": len(context.get("iteration_history", [])),
                "max_iterations": self.config.max_iterations,
                "goal": goal,
                "sources": sources,  # Include citations even in fallback
            }

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
