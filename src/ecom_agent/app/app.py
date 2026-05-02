import uuid
from typing import Any, Dict, List

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage

from ecom_agent.agent.graph.graph import get_graph_builder

app = get_graph_builder()


def _format_faq_context_ui(memory_context: List[Dict[str, Any]]) -> str:
    if not memory_context:
        return "_No FAQ matches found._"
    lines = []
    for i, item in enumerate(memory_context, start=1):
        score = item.get("score", 0.0)
        lines.append(
            f"**{i}. {item.get('question', 'N/A')}**\n"
            f"- Answer: {item.get('answer', 'N/A')}\n"
            f"- Relevance score: `{score:.4f}`"
        )
    return "\n\n".join(lines)


def _format_inventory_context_ui(memory_context: List[Dict[str, Any]]) -> str:
    if not memory_context:
        return "_No product matches found._"
    lines = []
    for i, item in enumerate(memory_context, start=1):
        score = item.get("score", 0.0)
        lines.append(
            f"**{i}. {item.get('name', 'N/A')}**\n"
            f"- Category: {item.get('category', 'N/A')}\n"
            f"- Price: `{item.get('price', 'N/A')}`\n"
            f"- Description: {item.get('description', 'N/A')}\n"
            f"- Relevance score: `{score:.4f}`"
        )
    return "\n\n".join(lines)


def build_reply(response: Dict[str, Any]) -> str:
    messages = response.get("messages", [])

    if not messages:
        return "I'm sorry, I wasn't able to generate a response. Please try again."

    last_message = messages[-1]

    if isinstance(last_message, AIMessage):
        return last_message.content.strip()

    return str(last_message).strip()


def build_debug_info(response: Dict[str, Any]) -> str:
    workflow = response.get("workflow", "unknown")
    memory_context = response.get("memory_context", [])

    if workflow == "faq":
        context_block = _format_faq_context_ui(memory_context)
    elif workflow == "product":
        context_block = _format_inventory_context_ui(memory_context)
    else:
        context_block = "_No context available._"

    return (
        f"---\n"
        f"**Route:** `{workflow}`\n\n"
        f"**Retrieved context:**\n{context_block}"
    )


@cl.on_chat_start
async def start():
    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)
    await cl.Message(
        content="Hello! Ask me anything about our products, shipping, returns, refunds, or store policies."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    try:
        thread_id = cl.user_session.get("thread_id")
        if not thread_id:
            thread_id = str(uuid.uuid4())
            cl.user_session.set("thread_id", thread_id)

        user_text = message.content.strip()
        if not user_text:
            await cl.Message(content="Please type a question and I'll do my best to help!").send()
            return

        response = await app.ainvoke(
            {"messages": [HumanMessage(content=user_text)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        answer = build_reply(response)
        await cl.Message(content=answer).send()

    except Exception as e:
        await cl.Message(
            content=(
                "I'm having trouble processing your request right now. "
                "Please try again in a moment.\n\n"
                f"_(Error: {str(e)})_"
            )
        ).send()
        raise