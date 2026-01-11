"""State models for espagent."""

from langchain.agents import AgentState
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information extracted from text."""

    user_name: str = Field(description="User's name")
    additional_info: str = Field(
        description="Additional info about the user, such as role, task, etc."
    )


class TaskState(AgentState):
    """Agent state for task execution."""

    user_id: str
    user_info: UserInfo
    task_info: str


class SSHState(BaseModel):
    """SSH configuration state."""

    host: str = Field(description="Remote host name from local SSH configuration")
    user: str = Field(description="Remote host username")
    passwd: int = Field(description="Remote host user password")
    port: int = Field(description="Port for remote host login")
    command: str = Field(description="Command to execute on remote host")
