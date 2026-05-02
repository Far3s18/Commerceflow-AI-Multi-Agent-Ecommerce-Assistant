from ecom_agent.agent.graph.state import AIState
from typing import Literal

def select_workflow(state: AIState) -> Literal["faq_search_node", "inventory_search_node"]:
    workflow = state.get("workflow", "faq")
 
    if workflow == "faq":
        return "faq_search_node"
 
    return "inventory_search_node"
