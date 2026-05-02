from typing import List, Dict, Any

RELEVANCE_THRESHOLD = 0.45


def format_faq_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No FAQ results retrieved."

    lines = []
    for i, item in enumerate(results, start=1):
        score = item.get("score", 0.0)
        confidence = "HIGH" if score >= RELEVANCE_THRESHOLD else "LOW — treat with caution"
        lines.append(
            f"[FAQ Result {i}] Confidence: {confidence} (score: {score:.3f})\n"
            f"  Question : {item.get('question', 'N/A')}\n"
            f"  Answer : {item.get('answer', 'N/A')}\n"
        )
    return "\n".join(lines)


def format_inventory_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No product results retrieved."

    lines = []
    for i, item in enumerate(results, start=1):
        score = item.get("score", 0.0)
        confidence = "HIGH" if score >= RELEVANCE_THRESHOLD else "LOW — treat with caution"
        lines.append(
            f"[Product Result {i}] Confidence: {confidence} (score: {score:.3f})\n"
            f"  Name : {item.get('name', 'N/A')}\n"
            f"  Category : {item.get('category', 'N/A')}\n"
            f"  Price : ${item.get('price', 'N/A')}\n"
            f"  Description : {item.get('description', 'N/A')}\n"
        )
    return "\n".join(lines)