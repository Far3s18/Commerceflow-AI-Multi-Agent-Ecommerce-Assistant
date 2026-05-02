from langgraph.graph import MessagesState
from typing import Any, List, Dict


class AIState(MessagesState):
    workflow: str
    memory_context: List[Dict[str, Any]] 