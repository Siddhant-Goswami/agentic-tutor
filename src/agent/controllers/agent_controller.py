"""
Agent Controller

Main autonomous agent orchestrator implementing SENSE → PLAN → ACT → OBSERVE → REFLECT loop.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional
from openai import AsyncOpenAI

from src.agent.utils.logger import AgentLogger
from src.agent.tools.registry import ToolRegistry
from src.agent.models.agent_config import AgentConfig
from src.agent.models.agent_result import AgentResult
from src.agent.controllers.step_executor import StepExecutor

logger = logging.getLogger(__name__)


class AgentController:
    """
    Autonomous agent controller.

    Orchestrates SENSE → PLAN → ACT → OBSERVE → REFLECT loop to achieve user goals.
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

        # Initialize tools
        self.tools = ToolRegistry(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )

        # Initialize LLM client
        self.llm_client = AsyncOpenAI(api_key=openai_api_key)

        # Load prompts from agent/prompts directory
        # Navigate from src/agent/controllers/ up to project root, then to agent/prompts
        prompts_dir = Path(__file__).parent.parent.parent.parent / "agent" / "prompts"
        with open(prompts_dir / "system.txt", "r") as f:
            system_prompt = f.read()
        with open(prompts_dir / "planning.txt", "r") as f:
            planning_prompt_template = f.read()
        with open(prompts_dir / "reflection.txt", "r") as f:
            reflection_prompt_template = f.read()

        # Initialize step executor
        self.executor = StepExecutor(
            tools=self.tools,
            llm_client=self.llm_client,
            agent_logger=self.logger,
            system_prompt=system_prompt,
            planning_prompt_template=planning_prompt_template,
            reflection_prompt_template=reflection_prompt_template,
            llm_model=self.config.llm_model,
            temperature=self.config.temperature,
        )

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
                logger.info(
                    f"=== Iteration {iteration}/{self.config.max_iterations} ==="
                )

                # SENSE: Gather user context (only on first iteration)
                if iteration == 1:
                    context = await self.executor.sense(
                        user_id, context, session_id, iteration
                    )

                # PLAN: Decide next action
                plan = await self.executor.plan(goal, context, session_id, iteration)

                # Check if we should complete
                if plan.get("action_type") == "COMPLETE":
                    return self._handle_completion(
                        plan, session_id, iteration, status="completed"
                    )

                # Check if we need clarification
                if plan.get("action_type") == "CLARIFY":
                    return self._handle_clarification(plan, session_id, iteration)

                # Check if we need plan approval for web search
                if plan.get("action_type") == "PLAN_APPROVAL":
                    return self._handle_plan_approval(plan, session_id, iteration)

                # ACT: Execute the planned action
                result = await self.executor.act(plan, session_id, iteration)

                # OBSERVE: Log the result
                self.executor.observe(plan, result, session_id, iteration)

                # Store search results in context for partial digest generation
                if plan.get("tool") == "search-content" and "results" in result:
                    if "search_results" not in context:
                        context["search_results"] = []
                    context["search_results"].extend(result.get("results", []))

                # REFLECT: Evaluate progress
                reflection = await self.executor.reflect(
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
            return await self._handle_timeout(goal, context, session_id, iteration)

        except Exception as e:
            return self._handle_error(e, session_id, iteration)

    def _handle_completion(
        self,
        plan: dict,
        session_id: uuid.UUID,
        iteration: int,
        status: str = "completed",
    ) -> AgentResult:
        """Handle successful completion."""
        output = plan.get("output", {})
        self.logger.log(
            session_id,
            "COMPLETE",
            {"output": output, "reasoning": plan.get("reasoning", "")},
            iteration,
        )
        self.logger.complete_session(session_id, status, output)

        return AgentResult(
            output=output,
            logs=self.logger.get_logs(session_id),
            iteration_count=iteration,
            status=status,
            session_id=str(session_id),
        )

    def _handle_clarification(
        self, plan: dict, session_id: uuid.UUID, iteration: int
    ) -> AgentResult:
        """Handle clarification request."""
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

    def _handle_plan_approval(
        self, plan: dict, session_id: uuid.UUID, iteration: int
    ) -> AgentResult:
        """Handle plan approval request."""
        research_plan = plan.get("research_plan", {})
        self.logger.log(
            session_id,
            "PLAN_APPROVAL",
            {"research_plan": research_plan, "reasoning": plan.get("reasoning", "")},
            iteration,
        )
        self.logger.complete_session(
            session_id, "needs_approval", {"research_plan": research_plan}
        )

        return AgentResult(
            output={
                "research_plan": research_plan,
                "type": "plan_approval_needed",
                "message": "Web search requires your approval",
            },
            logs=self.logger.get_logs(session_id),
            iteration_count=iteration,
            status="needs_approval",
            session_id=str(session_id),
        )

    async def _handle_timeout(
        self, goal: str, context: dict, session_id: uuid.UUID, iteration: int
    ) -> AgentResult:
        """Handle timeout (max iterations reached)."""
        logger.warning(f"Max iterations ({self.config.max_iterations}) reached")

        # Try to generate a partial result with what we have
        partial_output = await self.executor.generate_partial_result(
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

    def _handle_error(
        self, error: Exception, session_id: uuid.UUID, iteration: int
    ) -> AgentResult:
        """Handle execution error."""
        logger.error(f"Agent execution failed: {error}", exc_info=True)
        self.logger.log(session_id, "ERROR", {"error": str(error)})
        self.logger.complete_session(session_id, "failed")

        return AgentResult(
            output={"error": str(error)},
            logs=self.logger.get_logs(session_id),
            iteration_count=iteration,
            status="failed",
            session_id=str(session_id),
        )
