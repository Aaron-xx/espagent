"""Human-in-the-loop interaction handler."""

import json

from langgraph.graph.state import Command


class HumanInTheLoop:
    """Minimal HITL processor - handles user interaction and decisions only."""

    async def handle_interrupt(
        self,
        agent,
        snapshot,
        thread_config: dict,
    ) -> bool:
        """Handle a single interrupt event.

        Args:
            agent: LangGraph agent
            snapshot: Agent state snapshot
            thread_config: Thread configuration

        Returns:
            True if execution was resumed, False otherwise
        """
        if not snapshot.tasks:
            return False

        # Get pending tool calls for approval
        last_msg = snapshot.values["messages"][-1]
        if not (hasattr(last_msg, "tool_calls") and last_msg.tool_calls):
            return False

        tool_calls = last_msg.tool_calls
        decisions = []

        # Process each tool call individually
        for idx, tool_call in enumerate(tool_calls, 1):
            print(f"\n[Tool {idx}/{len(tool_calls)}] {tool_call['name']}")
            print(f"Args: {json.dumps(tool_call['args'], indent=2, ensure_ascii=False)}")

            decision = self._get_decision(tool_call)
            if decision:
                decisions.append(decision)

        # Resume execution
        if decisions:
            print("\n[System]: Continuing execution...\n")
            async for chunk in agent.astream(
                Command(resume={"decisions": decisions}),
                config=thread_config,
                stream_mode="values",
            ):
                msg = chunk["messages"][-1]
                if msg.type == "ai" and msg.content:
                    print(f"🤖 {msg.content}", end="", flush=True)
            return True

        return False

    def _get_decision(self, tool_call: dict) -> dict | None:
        """Get user's approve/edit/reject decision.

        Args:
            tool_call: The tool call dict containing name and args

        Returns:
            Decision dict or None
        """
        while True:
            choice = input("\n(y)approve / (e)dit / (n)reject: ").strip().lower()

            if choice == "y":
                return {"type": "approve"}

            elif choice == "e":
                print(
                    f"\nCurrent args: {json.dumps(tool_call['args'], indent=2, ensure_ascii=False)}"
                )
                edited_json = input("Enter edited args (JSON format): ").strip()

                try:
                    edited_args = json.loads(edited_json)
                    return {
                        "type": "edit",
                        "edited_action": {"name": tool_call["name"], "args": edited_args},
                    }
                except json.JSONDecodeError:
                    print("❌ JSON format error, please retry")
                    continue

            elif choice == "n":
                reason = input("Rejection reason (optional): ").strip()
                return {
                    "type": "reject",
                    "message": reason or "Rejected by administrator",
                }

            else:
                print("❌ Invalid input")
