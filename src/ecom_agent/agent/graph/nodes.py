from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage

from ecom_agent.agent.graph.state import AIState
from ecom_agent.agent.utils.chains import get_router_chain, get_brain_chain
from ecom_agent.memory.vector_store import get_vector_store
from ecom_agent.agent.utils.formatter import format_faq_context, format_inventory_context

vector_store = get_vector_store()

def _build_enriched_query(state: AIState) -> str:
    messages = state["messages"]
    user_query = messages[-1].content.strip()

    follow_up_words = {
        "it", "its", "this", "that", "they", "them", "these", "those",
        "the product", "the price", "how much", "what color", "what size",
        "is it", "does it", "do they", "tell me more", "and the", "what about",
        "price", "cost", "how much is", "available", "any discount",
    }

    is_short = len(user_query.split()) <= 8
    is_follow_up = any(signal in user_query.lower() for signal in follow_up_words)

    if is_short or is_follow_up:
        for msg in reversed(messages[:-1]):
            if isinstance(msg, AIMessage) and msg.content.strip():
                prior_context = msg.content.strip()[:150]
                return f"{prior_context} — {user_query}"

    return user_query


async def router_node(state: AIState) -> Dict[str, Any]:
    chain = get_router_chain()
    response = await chain.ainvoke({"messages": state["messages"][-5:]})
    workflow = response.response_type.strip().lower()

    if workflow not in ("faq", "product"):
        workflow = "faq"

    return {"workflow": workflow}


async def faq_search_node(state: AIState) -> Dict[str, Any]:
    search_query = _build_enriched_query(state)
    raw_results = vector_store.search_faq(search_query, limit=3)
    formatted_context = format_faq_context(raw_results)

    chain = get_brain_chain()
    response = await chain.ainvoke({
        "messages": state["messages"],
        "memory_context": formatted_context,
    })

    return {
        "messages": state["messages"] + [AIMessage(content=response.content.strip())],
        "memory_context": raw_results,
    }


async def inventory_search_node(state: AIState) -> Dict[str, Any]:
    search_query = _build_enriched_query(state)
    raw_results = vector_store.search_inventory(search_query, limit=3)
    formatted_context = format_inventory_context(raw_results)

    chain = get_brain_chain()
    response = await chain.ainvoke({
        "messages": state["messages"],
        "memory_context": formatted_context,
    })

    return {
        "messages": state["messages"] + [AIMessage(content=response.content.strip())],
        "memory_context": raw_results,
    }