"""Middleware configurations for the espagent."""

from collections.abc import Callable
from pathlib import Path

from deepagents import FilesystemMiddleware
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    LLMToolSelectorMiddleware,
    ModelRequest,
    ModelResponse,
    SummarizationMiddleware,
    ToolRetryMiddleware,
    wrap_model_call,
)

from espagent.models import large_model, llm


@wrap_model_call
async def dynamic_model_router(
    request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """根据对话上下文动态切换模型.

    Args:
        request: The model request containing state and context.
        handler: The next handler in the middleware chain.

    Returns:
        The model response after potential model switching.
    """
    state = request.state
    messages = state.get("messages", [])

    # 场景 A: 如果对话轮数超过 5 轮，切换到大模型处理复杂上下文
    if len(messages) > 5:
        print(f"--- [Middleware] 检测到长对话 ({len(messages)} msgs)，切换 ---")
        request = request.override(model=large_model)

    # 场景 B: 如果用户输入包含特定关键词 (仅作演示，实际可用分类器)
    elif messages and "复杂分析" in messages[-1].content:
        print("--- [Middleware] 检测到复杂任务，切换 ---")
        request = request.override(model=large_model)

    else:
        print("--- [Middleware] 使用默认小模型 ---")

    return await handler(request)


def get_middleware() -> list:
    """获取配置的中间件列表.

    Returns:
        List of middleware instances.
    """
    hitl_middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "write_file": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "需要人工批准才能写入文件",
            },
            "read_file": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "需要人工批准才能读取文件",
            },
            "ssh_run": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "需要人工批准才能执行SSH命令",
            },
        },
    )

    summarization_middleware = SummarizationMiddleware(
        model=llm,
        trigger=("tokens", 10000),  # 历史消息 token 数量超过 10000 时触发压缩
        keep=("messages", 20),  # 保留最近 20 条消息
        summary_prompt="请将以下对话历史进行摘要，保留关键决策点和技术细节：\n\n{messages}\n\n摘要:",
    )

    retry_middleware = ToolRetryMiddleware(
        max_retries=3,
        on_failure="continue",
        backoff_factor=1.5,
        initial_delay=0.5,
        max_delay=5.0,
        jitter=True,
    )

    tool_selector_middleware = LLMToolSelectorMiddleware(
        model=llm,
        max_tools=3,  # 最多选择3个工具
        always_include=["save_memory", "recall_memory"],  # 始终包含记忆工具
        system_prompt="分析用户查询，选择最相关的工具。优先选择直接相关的工具。",
    )

    filesystem_middleware = FilesystemMiddleware(
        backend=FilesystemBackend(
            root_dir=Path.cwd(),
            virtual_mode=True,
        ),
    )

    middlewares = [
        dynamic_model_router,
        summarization_middleware,
        filesystem_middleware,
        tool_selector_middleware,
        retry_middleware,
        hitl_middleware,
    ]

    return middlewares
