from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from ecom_agent.agent.utils.prompts import ROUTER_PROMPT, BRAIN_PROMPT
from ecom_agent.agent.utils.model_factory import get_text_model


class RouterResponse(BaseModel):
    response_type: str = Field(description="Return only 'faq' or 'product'.")


def get_router_chain():
    model = get_text_model(temperature=0.1).with_structured_output(RouterResponse)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_PROMPT),
        ("placeholder", "{messages}"),
    ])
    return prompt | model


def get_brain_chain():
    model = get_text_model(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", BRAIN_PROMPT),
        ("placeholder", "{messages}"),
    ])
    return prompt | model