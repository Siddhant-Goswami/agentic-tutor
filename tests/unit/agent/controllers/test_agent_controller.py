"""
Tests for Agent Controller

Tests the main agent orchestration logic.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.agent.models.agent_config import AgentConfig
from src.agent.models.agent_result import AgentResult
from src.agent.controllers.agent_controller import AgentController


@pytest.fixture
def agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        max_iterations=5,
        llm_model="gpt-4o-mini",
        temperature=0.3,
        log_level="INFO",
    )


@pytest.fixture
def mock_tools():
    """Create mock tool registry."""
    tools = Mock()
    tools.tools = {f"tool-{i}": Mock() for i in range(7)}
    tools.execute_tool = AsyncMock(return_value={"result": "success"})
    tools.get_tool_schemas_for_prompt = Mock(return_value="mock schemas")
    return tools


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock()
    response = Mock()
    response.choices = [Mock(message=Mock(content='{"action_type": "COMPLETE", "output": {}}'))]
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def agent_controller(agent_config, monkeypatch):
    """Create agent controller with mocked dependencies."""
    # Mock the imports in AgentController
    with patch("src.agent.controllers.agent_controller.ToolRegistry") as mock_registry, \
         patch("src.agent.controllers.agent_controller.AsyncOpenAI") as mock_openai, \
         patch("src.agent.controllers.agent_controller.AgentLogger") as mock_logger, \
         patch("builtins.open", create=True) as mock_open:

        # Setup mock file reads for prompts
        mock_file = MagicMock()
        mock_file.read.return_value = "mock prompt"
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        # Setup mock tool registry
        mock_registry_instance = Mock()
        mock_registry_instance.tools = {}
        mock_registry_instance.execute_tool = AsyncMock(return_value={"result": "success"})
        mock_registry_instance.get_tool_schemas_for_prompt = Mock(return_value="schemas")
        mock_registry.return_value = mock_registry_instance

        # Setup mock OpenAI client
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance

        # Setup mock logger
        mock_logger_instance = Mock()
        mock_logger_instance.start_session = Mock()
        mock_logger_instance.log = Mock()
        mock_logger_instance.get_logs = Mock(return_value=[])
        mock_logger_instance.complete_session = Mock()
        mock_logger.return_value = mock_logger_instance

        controller = AgentController(
            config=agent_config,
            supabase_url="http://test",
            supabase_key="test-key",
            openai_api_key="test-key",
        )

        return controller


class TestAgentController:
    """Tests for AgentController."""

    def test_init(self, agent_controller, agent_config):
        """Test controller initialization."""
        assert agent_controller.config == agent_config
        assert agent_controller.logger is not None
        assert agent_controller.tools is not None
        assert agent_controller.llm_client is not None
        assert agent_controller.executor is not None

    @pytest.mark.asyncio
    async def test_handle_completion(self, agent_controller):
        """Test handling successful completion."""
        session_id = uuid.uuid4()
        plan = {
            "action_type": "COMPLETE",
            "output": {"digest": "test digest"},
            "reasoning": "Goal achieved"
        }

        result = agent_controller._handle_completion(plan, session_id, 3, "completed")

        assert isinstance(result, AgentResult)
        assert result.status == "completed"
        assert result.output == {"digest": "test digest"}
        assert result.iteration_count == 3

    @pytest.mark.asyncio
    async def test_handle_clarification(self, agent_controller):
        """Test handling clarification request."""
        session_id = uuid.uuid4()
        plan = {
            "action_type": "CLARIFY",
            "question": "Which topic?",
            "reasoning": "Need more info"
        }

        result = agent_controller._handle_clarification(plan, session_id, 2)

        assert isinstance(result, AgentResult)
        assert result.status == "needs_clarification"
        assert result.output["question"] == "Which topic?"
        assert result.output["type"] == "clarification_needed"

    @pytest.mark.asyncio
    async def test_handle_plan_approval(self, agent_controller):
        """Test handling plan approval request."""
        session_id = uuid.uuid4()
        plan = {
            "action_type": "PLAN_APPROVAL",
            "research_plan": {"queries": ["test query"]},
            "reasoning": "Need approval for web search"
        }

        result = agent_controller._handle_plan_approval(plan, session_id, 1)

        assert isinstance(result, AgentResult)
        assert result.status == "needs_approval"
        assert result.output["type"] == "plan_approval_needed"
        assert "research_plan" in result.output

    @pytest.mark.asyncio
    async def test_handle_timeout(self, agent_controller):
        """Test handling timeout (max iterations reached)."""
        session_id = uuid.uuid4()
        context = {
            "user_id": "test-user",
            "iteration_history": [],
            "search_results": []
        }

        # Mock the generate_partial_result method
        agent_controller.executor.generate_partial_result = AsyncMock(
            return_value={
                "warning": "Partial results",
                "insights": ["insight 1"],
                "status": "partial"
            }
        )

        result = await agent_controller._handle_timeout("test goal", context, session_id, 5)

        assert isinstance(result, AgentResult)
        assert result.status == "timeout"
        assert result.iteration_count == 5
        assert "warning" in result.output

    def test_handle_error(self, agent_controller):
        """Test handling execution error."""
        session_id = uuid.uuid4()
        error = RuntimeError("Test error")

        result = agent_controller._handle_error(error, session_id, 3)

        assert isinstance(result, AgentResult)
        assert result.status == "failed"
        assert "error" in result.output
        assert "Test error" in result.output["error"]


class TestAgentControllerIntegration:
    """Integration tests for AgentController."""

    @pytest.mark.asyncio
    async def test_run_immediate_completion(self, agent_controller):
        """Test run method with immediate completion."""
        # Mock executor to return COMPLETE action
        agent_controller.executor.sense = AsyncMock(
            return_value={"user_id": "test", "user_context": {}, "iteration_history": []}
        )
        agent_controller.executor.plan = AsyncMock(
            return_value={
                "action_type": "COMPLETE",
                "output": {"digest": "test"},
                "reasoning": "Done"
            }
        )

        result = await agent_controller.run("test goal", "test-user")

        assert isinstance(result, AgentResult)
        assert result.status == "completed"
        assert result.iteration_count == 1

    @pytest.mark.asyncio
    async def test_run_with_clarification(self, agent_controller):
        """Test run method requesting clarification."""
        agent_controller.executor.sense = AsyncMock(
            return_value={"user_id": "test", "user_context": {}, "iteration_history": []}
        )
        agent_controller.executor.plan = AsyncMock(
            return_value={
                "action_type": "CLARIFY",
                "question": "Which topic?",
                "reasoning": "Unclear"
            }
        )

        result = await agent_controller.run("vague goal", "test-user")

        assert isinstance(result, AgentResult)
        assert result.status == "needs_clarification"
        assert "question" in result.output

    @pytest.mark.asyncio
    async def test_run_with_max_iterations(self, agent_controller):
        """Test run method reaching max iterations."""
        agent_controller.config.max_iterations = 2

        agent_controller.executor.sense = AsyncMock(
            return_value={"user_id": "test", "user_context": {}, "iteration_history": []}
        )
        agent_controller.executor.plan = AsyncMock(
            return_value={
                "action_type": "TOOL_CALL",
                "tool": "search-content",
                "args": {"query": "test"}
            }
        )
        agent_controller.executor.act = AsyncMock(
            return_value={"results": []}
        )
        agent_controller.executor.observe = Mock()
        agent_controller.executor.reflect = AsyncMock(
            return_value="Still searching"
        )
        agent_controller.executor.generate_partial_result = AsyncMock(
            return_value={"warning": "Timeout", "status": "partial"}
        )

        result = await agent_controller.run("complex goal", "test-user")

        assert isinstance(result, AgentResult)
        assert result.status == "timeout"
        assert result.iteration_count == 2
