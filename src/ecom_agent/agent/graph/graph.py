from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ecom_agent.agent.graph.state import AIState
from ecom_agent.agent.graph.edges import select_workflow
from ecom_agent.agent.graph.nodes import router_node, faq_search_node, inventory_search_node


def create_graph_workflow() -> StateGraph:
    graph = StateGraph(AIState)

    graph.add_node("router_node", router_node)
    graph.add_node("faq_search_node", faq_search_node)
    graph.add_node("inventory_search_node", inventory_search_node)

    graph.add_edge(START, "router_node")
    graph.add_conditional_edges("router_node", select_workflow)
    graph.add_edge("faq_search_node", END)
    graph.add_edge("inventory_search_node", END)

    return graph


def get_graph_builder():
    memory = MemorySaver()
    compiled_graph = create_graph_workflow().compile(checkpointer=memory)
    return compiled_graph