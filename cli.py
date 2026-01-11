"""CLI interface for espagent interactive console."""

import asyncio
import logging
import os
import pwd
import sys
import warnings

from espagent.agent import get_agent
from espagent.middlewares import get_middleware
from espagent.tools import get_mcp_tools, recall_memory, save_memory
from espagent.utils import HumanInTheLoop, UserInfo

warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=".*AsyncConnectionPool.*deprecated.*",
)

logger = logging.getLogger(__name__)


async def cleanup(pool=None) -> None:
    """Clean up all resources in the correct order.

    This method should be called from all exit points:
    - Normal exit (/exit command)
    - Keyboard interrupt (Ctrl+C)
    - EOF (Ctrl+D)

    Args:
        pool: The AsyncConnectionPool to close

    Note:
        This function never raises exceptions - all errors are logged and suppressed.
    """
    if pool is not None:
        try:
            # Use timeout to avoid blocking indefinitely during shutdown
            await pool.close(timeout=5.0)
        except BaseException as e:
            # Catch ALL exceptions including CancelledError, KeyboardInterrupt, etc.
            # We never want to raise from cleanup as it could mask the original exception
            logger.info(f"Pool close: {type(e).__name__} (suppressed during shutdown)")

    logger.info("CLI application cleaned up")


async def cli_main() -> None:
    """Main CLI entry point for the interactive agent console."""
    current_user = pwd.getpwuid(os.getuid()).pw_name

    userinfo = UserInfo(
        user_name=current_user,
        additional_info="我将进行嵌入式任务",
    )

    thread_config = {
        "configurable": {
            "thread_id": current_user,
            "user_id": current_user,
            "user_info": userinfo,
        },
    }

    all_mcp_tools = await get_mcp_tools()

    # Unpack MCP tools list using spread operator to avoid nested list structure
    tools = [save_memory, recall_memory, *all_mcp_tools]
    middlewares = get_middleware()
    agent, pool = await get_agent(tools=tools, middlewares=middlewares)
    hitl = HumanInTheLoop()

    try:
        while True:
            try:
                print("User > ", end="", flush=True)
                line = sys.stdin.readline()

                # EOF reached (stdin closed)
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                payload = {"messages": [{"role": "user", "content": line}]}
                async for chunk in agent.astream(
                    payload,
                    config=thread_config,
                    stream_mode="values",
                ):
                    last_msg = chunk["messages"][-1]
                    if last_msg.type == "ai" and last_msg.content:
                        print(f"🤖 Agent: {last_msg.content}", end="", flush=True)
                    elif last_msg.type == "tool" and last_msg.content:
                        print(f"🤖 Tool: {last_msg.content}", end="", flush=True)
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool_call in last_msg.tool_calls:
                            print(f"   🔧 [Calling tool]: {tool_call['name']}")

                snapshot = await agent.aget_state(config=thread_config)
                await hitl.handle_interrupt(agent, snapshot, thread_config)
                sys.stdout.write("\n")
            # except asyncio.CancelledError:
            #     print("\nbye")
            #     break
            except KeyboardInterrupt:
                break

            except EOFError:
                break
    finally:
        sys.stdout.write("\nbye\n")
        # Ensure cleanup is executed in all cases
        await cleanup(pool)


def main() -> None:
    """Entry point for espagent console command."""
    import os

    # Change to project directory (this file's directory)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(cli_main())
