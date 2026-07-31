import os

from app.config import get_settings


def configure_langsmith() -> None:
    """Enables LangSmith tracing for every LangChain/LangGraph call in this process.

    LangChain's tracing reads LANGCHAIN_* from the process environment rather
    than any constructor kwarg, so — same as the Tavily key — it has to be
    exported here rather than passed into individual clients. Call this once,
    before any graph or LLM object is built, so the first real call is
    already traced. A no-op when no key is configured.
    """

    settings = get_settings()
    if not settings.langsmith_api_key:
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
