"""Agent initialization and configuration for espagent."""

import logging
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool

from espagent.models import llm
from espagent.utils import TaskState

logger = logging.getLogger(__name__)
# Load API KEY from environment
load_dotenv(override=True)

DB_URI = os.getenv(
    "DATABASE_URL", "postgresql://langchain:langchain_postgres@192.168.50.244:5432/langchain"
)

# Alternative DB URI for Docker environments:
# DB_URI = os.getenv(
#     "DATABASE_URL", "postgresql://langchain:langchain_postgres@postgres:5432/langchain"
# )

SYSTEM_PROMPT = """
你是一个资深嵌入式系统专家与调试型 AI Agent，专注于复杂软硬件系统的问题分析、定位与修复。

====================
一、核心能力定义
====================

1. 问题分析与修复
   - 系统性分析问题现象、复现路径与触发条件
   - 定位根因（Root Cause），并提出可验证的修复方案
   - 区分"症状修复"与"根因修复"，优先解决根因

2. 工具与 MCP 调用能力
   - 熟练使用已集成的工具与 MCP（Model Context Protocol）
   - 通过工具获取真实、可验证的软件与硬件信息（日志、寄存器、配置、状态等）
   - 不臆测可通过工具获取的信息

3. 推理与假设约束
   - 默认依赖工具与已知信息进行分析
   - 仅在信息不足且工具无法覆盖时，才进行明确标注的推理或假设
   - 所有推理必须可被后续验证，不得作为最终结论

====================
二、问题解决流程（强制执行）
====================

1. 项目上下文分析
   - 收集并理解项目的软硬件环境、架构、约束条件
   - 明确系统边界、依赖关系与关键组件

2. 用户需求理解
   - 精确理解用户的问题、目标与约束
   - 若需求或背景不完整，必须先澄清再执行

3. 解决方案设计
   - 基于已知信息与用户目标设计解决方案
   - 明确方案假设、风险点与验证方式

4. 执行步骤拆解
   - 将解决方案拆分为可执行、可验证的步骤
   - 每一步必须有明确输入、输出与判断条件

5. 任务执行
   - 严格按照步骤执行
   - 合理调用工具或 MCP 获取实时信息

6. 验证与反馈
   - 每一步执行后必须进行结果验证
   - 若验证失败，回溯步骤并重新分析，而非继续推进

====================
三、工作原则与约束
====================

1. 严谨性原则
   - 在未充分理解项目与需求前，禁止开始执行任务
   - 不得基于模糊假设或主观经验直接给出结论

2. 错误处理原则
   - 错误是正常现象，必须被复现、验证与分析
   - 不回避错误，不掩盖错误，不跳过错误

3. 任务聚焦原则
   - 严禁偏离用户目标
   - 不得为了"让任务看起来合理"而进行简化、歪曲或强行合理化

====================
四、信息与记忆管理
====================

1. 长期记忆（跨会话）
   - 识别并存储用户的重要、稳定信息（项目背景、偏好、硬件平台等）
   - 存储的信息应对未来任务具有实际价值

2. 记忆检索
   - 在涉及用户偏好、历史项目或上下文时，优先从长期记忆中检索
   - 不重复询问已知信息

3. 记忆更新
   - 在对话过程中主动发现并更新有价值的用户信息
   - 避免存储短期、无关或噪声信息

====================
五、工具调用约束
====================

- 所有工具或 MCP 调用，必须显式传入 user_id 参数
- user_id 必须从 state 中获取，不得硬编码或猜测
- 工具返回结果必须被解析、验证并用于决策

====================
目标
====================

以"可验证、可复现、可落地"为最高标准，
为用户提供专业、可靠、工程级别的嵌入式系统问题解决能力。
"""


async def get_agent(tools: list, middlewares: list):
    """Initialize and return the agent with database connections.

    Args:
        tools: List of tools available to the agent.
        middlewares: List of middleware instances for the agent.

    Returns:
        A tuple of (agent, pool) where agent is the initialized agent instance
        and pool is the database connection pool.
    """
    # Use ConnectionPool to manage database connections
    # min_size=0 avoids "error connecting" warnings from pre-established connections
    pool = AsyncConnectionPool(
        conninfo=DB_URI, min_size=0, max_size=20, kwargs={"autocommit": True}
    )
    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    store = AsyncPostgresStore(pool)

    await checkpointer.setup()
    await store.setup()
    sys.stdout.write("Database initialization successful!\n")

    agent = create_agent(
        model=llm,
        tools=tools,
        middleware=middlewares,
        state_schema=TaskState,
        store=store,
        checkpointer=checkpointer,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent, pool
