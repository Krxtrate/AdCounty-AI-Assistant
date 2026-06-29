from mcp.server.fastmcp import FastMCP
from chatbot.models import ChatRequest, Message

mcp = FastMCP("AdCounty Chatbot")

@mcp.tool()
async def ask_chatbot(query: str, product: str = "", session_id: str = "default") -> str:
    """
    Send a query through the full RAG pipeline (intent → retrieval → Ollama).
    Optionally specify a product name to scope the query.
    """
    from chatbot.app import _generate  # import here to avoid circular imports

    # Build a minimal ChatRequest that _generate expects
    messages = []
    if product:
        # Prepend a system hint so intent detection picks up the product
        messages.append(Message(role="system", content=f"Focus on product: {product}"))
    messages.append(Message(role="user", content=query))

    chat = ChatRequest(messages=messages)
    result = await _generate(chat)
    return result.get("output", "No response generated.")


@mcp.tool()
async def ask_with_history(messages: list[dict]) -> str:
    """
    Send a full conversation history through the pipeline.
    Each message is {"role": "user"|"assistant", "content": "..."}.
    """
    from chatbot.app import _generate
    from chatbot.models import ChatRequest, Message

    chat = ChatRequest(
        messages=[Message(role=m["role"], content=m["content"]) for m in messages]
    )
    result = await _generate(chat)
    return result.get("output", "No response generated.")


@mcp.tool()
async def health_check() -> dict:
    """Check if FastAPI and Ollama are both reachable."""
    import httpx
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=2)
        return {"fastapi": True, "ollama": True}
    except Exception:
        return {"fastapi": True, "ollama": False}


if __name__ == "__main__":
    mcp.run()