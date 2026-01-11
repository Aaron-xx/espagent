"""Memory tools for storing and retrieving user information across sessions."""

import time
from typing import Any

from langchain.tools import ToolRuntime, tool

from espagent.utils import UserInfo


@tool
def save_memory(
    info: str,
    runtime: ToolRuntime = None,
) -> str:
    """Save user information and task info to cross-session memory.

    This tool persists information to the PostgreSQL Store, which can be shared
    across different sessions. Memory is isolated by user_id and user_name
    (based on user_id and user_name in the context).

    Args:
        info: The information content and task information to remember

    Returns:
        Confirmation message containing memory ID and username

    Example:
        save_memory("User Alice is a Python engineer", "Alice")
        save_memory("Developing ML recommendation system project", "Bob")
    """
    state = runtime.state
    if state is None:
        return "Error: context unavailable"

    user_id = state.get("user_id", "unknown_user")
    user_info: UserInfo = state.get("user_info", None)
    task_info = state.get("task_info", None)

    user_name = user_info.user_name if user_info else "unknown_user"

    store = runtime.store
    # Create namespace: (user_id, category)
    namespace = (user_id, user_name)

    # Generate memory ID (using timestamp)
    memory_id = f"mem_{int(time.time())}"

    # Store to BaseStore (auto-persisted)
    store.put(
        namespace,
        memory_id,
        {
            "info": info,
            "user_name": user_name,
            "task_info": task_info,
            "timestamp": time.time(),
        },
    )

    return f"Memory saved [{user_name}]: {info}"


@tool
def recall_memory(
    query: str | None = None,
    limit: int = 10,
    runtime: ToolRuntime = None,
) -> str:
    """Retrieve user information from cross-session memory.

    Retrieves previously saved memories, supports filtering by username.

    Args:
        query: Optional search keyword (not yet implemented, reserved parameter)
        limit: Maximum number of memories to return (default: 10)

    Returns:
        Formatted memory list, or message if not found

    Example:
        recall_memory()  # Get all general category memories
        recall_memory(None, 5)  # Get recent 5 project memories
    """
    state = runtime.state
    if state is None:
        return "Error: state unavailable"

    user_id = state.get("user_id", "anonymous")
    user_info: UserInfo = state.get(
        "user_info", UserInfo(user_name="anonymous", additional_info="")
    )
    user_name = user_info.user_name

    # Get store directly from runtime (injected by LangGraph)
    store = runtime.store

    if store is None:
        return "Error: Store not configured, cannot retrieve memory"

    # Search namespace prefix: (user_id, user_name)
    namespace_prefix = (user_id, user_name)

    try:
        items = store.search(namespace_prefix, limit=limit)

        if not items:
            return f"No memories found for user '{user_name}'"

        # Format results
        results = []
        for item in items:
            info = item.value.get("info", "N/A")
            task_info = item.value.get("task_info", "N/A")
            results.append(f"- {user_name}: {info}\n- Task info: {task_info}")

        return f"Found {len(results)} memories for user '{user_name}':\n" + "\n".join(results)

    except Exception as e:
        return f"Error retrieving memories for user '{user_name}': {str(e)}"


def get_memory_tools() -> list[Any]:
    """Get all memory tools.

    Returns:
        List of memory tools: [save_memory, recall_memory]
    """
    return [save_memory, recall_memory]
