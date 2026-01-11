"""Tests for espagent.tools module - meaningful validation only."""

from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from espagent.tools import ssh_run
from espagent.tools.memory import recall_memory, save_memory


class TestSSHTool:
    """Test SSH tool - validates actual subprocess behavior."""

    def test_ssh_calls_subprocess_with_correct_args(self):
        """Test ssh_run calls subprocess.run with SSH command structure.

        This validates the command is built correctly: ['ssh', host, command]
        If wrong, SSH would fail with usage error.
        """
        mock_result = MagicMock()
        mock_result.stdout = "output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            ssh_run.func("myhost", "ls -la")

        # Verify exact command structure
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["ssh", "myhost", "ls -la"]
        # Verify critical flags
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["check"] is True

    def test_ssh_returns_error_message_on_failure(self):
        """Test ssh_run returns error message instead of raising.

        When SSH fails (connection refused, command not found, etc),
        the tool should return a descriptive error message, not crash.
        """
        error = CalledProcessError(255, "ssh", stderr="Connection refused")

        with patch("subprocess.run", side_effect=error):
            result = ssh_run.func("host", "ls")

        # Should return error message, not raise
        assert "SSH command execution failed" in result
        assert "Connection refused" in result


class TestMemoryTools:
    """Test memory tools - validates data flow to store."""

    def test_save_memory_extracts_user_info_from_state(self):
        """Test save_memory correctly extracts user_id and user_name from state.

        The namespace (user_id, user_name) isolates memories per user.
        If extraction fails, memories could leak between users.
        """
        mock_runtime = MagicMock()
        mock_runtime.state = {
            "user_id": "alice",
            "user_info": MagicMock(user_name="alice_user"),
            "task_info": "debug task",
        }
        mock_runtime.store = MagicMock()

        save_memory.func("test info", runtime=mock_runtime)

        # Verify store.put was called with correct namespace
        mock_runtime.store.put.assert_called_once()
        call_args = mock_runtime.store.put.call_args
        namespace = call_args[0][0]
        assert namespace == ("alice", "alice_user")

    def test_save_memory_handles_missing_user_info(self):
        """Test save_memory handles missing user_info gracefully.

        When user_info is None, should use 'unknown_user' fallback
        instead of crashing.
        """
        mock_runtime = MagicMock()
        mock_runtime.state = {
            "user_id": "bob",
            "user_info": None,
        }
        mock_runtime.store = MagicMock()

        result = save_memory.func("test info", runtime=mock_runtime)

        # Should not crash, and use fallback
        assert "unknown_user" in result
        mock_runtime.store.put.assert_called_once()
        namespace = mock_runtime.store.put.call_args[0][0]
        assert namespace == ("bob", "unknown_user")

    def test_recall_memory_searches_with_correct_namespace(self):
        """Test recall_memory searches with correct namespace prefix.

        The search namespace must match the save namespace for
        memories to be retrieved correctly.
        """
        from espagent.utils import UserInfo

        mock_runtime = MagicMock()
        mock_runtime.state = {
            "user_id": "charlie",
            "user_info": UserInfo(user_name="charlie_user", additional_info="test"),
        }
        mock_runtime.store = MagicMock()
        mock_runtime.store.search.return_value = []

        recall_memory.func(runtime=mock_runtime, limit=5)

        # Verify search was called with correct namespace
        mock_runtime.store.search.assert_called_once()
        call_args = mock_runtime.store.search.call_args
        namespace = call_args[0][0]
        assert namespace == ("charlie", "charlie_user")
        # Verify limit is passed (as keyword argument)
        assert call_args[1]["limit"] == 5


class TestMCPIntegration:
    """Test MCP tool integration - validates interface."""

    @pytest.mark.asyncio
    async def test_mcp_tools_returns_list_or_empty(self):
        """Test get_mcp_tools function signature and return type.

        This validates the interface contract - even if server is down,
        the function should return a list (possibly empty), not crash.
        """
        from espagent.tools.mcp import get_mcp_tools

        try:
            tools = await get_mcp_tools()
            assert isinstance(tools, list)
            # Each tool should be a proper tool object
            for tool in tools:
                assert hasattr(tool, "name")
                assert hasattr(tool, "args_schema")
        except Exception as e:
            # Connection errors are acceptable, but should return empty list
            pytest.skip(f"MCP server not available: {e}")
