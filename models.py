"""LLM model configurations for espagent."""

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://open.bigmodel.cn/api/coding/paas/v4",
    model="glm-4.6",
    temperature=0,
)

small_model = ChatOpenAI(
    base_url="https://open.bigmodel.cn/api/coding/paas/v4",
    model="glm-4.5",
    temperature=0,
)

large_model = llm
