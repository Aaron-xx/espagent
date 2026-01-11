"""Tests for espagent.cli cleanup - validates exception suppression."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from espagent.cli import cleanup


class TestCleanup:
    """Test cleanup function - validates critical exception suppression.

    The cleanup function is called during shutdown. If it raises exceptions,
    it can mask the original error that caused shutdown, making debugging
    nearly impossible.
    """

    @pytest.mark.asyncio
    async def test_cleanup_closes_pool_with_timeout(self):
        """Test cleanup calls pool.close with timeout.

        Without timeout, shutdown can hang indefinitely if a connection
        is stuck waiting for database response.
        """
        mock_pool = AsyncMock()

        await cleanup(mock_pool)

        mock_pool.close.assert_called_once_with(timeout=5.0)

    @pytest.mark.asyncio
    async def test_cleanup_handles_none_pool(self):
        """Test cleanup handles None pool without crashing.

        If agent initialization fails, pool may be None.
        Cleanup should not raise in this case.
        """
        # Should not raise
        await cleanup(None)

    @pytest.mark.asyncio
    async def test_cleanup_suppresses_exception(self):
        """Test cleanup suppresses exceptions during pool.close.

        If pool.close raises (e.g., database already closed),
        cleanup must suppress it to avoid masking original error.
        """
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=RuntimeError("DB closed"))

        # Should not raise despite error
        await cleanup(mock_pool)

    @pytest.mark.asyncio
    async def test_cleanup_suppresses_cancelled_error(self):
        """Test cleanup suppresses CancelledError.

        CancelledError is common during shutdown (Ctrl+C).
        If cleanup raises it, the shutdown flow is interrupted.
        """
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=asyncio.CancelledError())

        # Should suppress CancelledError
        await cleanup(mock_pool)

    @pytest.mark.asyncio
    async def test_cleanup_suppresses_keyboard_interrupt(self):
        """Test cleanup suppresses KeyboardInterrupt.

        KeyboardInterrupt during cleanup should not interfere
        with the shutdown process.
        """
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=KeyboardInterrupt())

        # Should suppress KeyboardInterrupt
        await cleanup(mock_pool)
