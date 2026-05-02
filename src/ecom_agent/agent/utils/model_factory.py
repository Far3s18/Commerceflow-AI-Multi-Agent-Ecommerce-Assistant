from langchain_ollama import ChatOllama

def get_text_model(temperature: float = 0.3) -> ChatOllama:
    return ChatOllama(
        model="qwen2.5:7b",
        temperature=temperature,
    )