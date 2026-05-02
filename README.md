# Commerceflow AI - MultiAgent Ecommerce Assistant


<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C?style=for-the-badge&logo=qdrant&logoColor=white"/>
  <img src="https://img.shields.io/badge/Ollama-Local%20LLM-000000?style=for-the-badge&logo=ollama&logoColor=white"/>
  <img src="https://img.shields.io/badge/Chainlit-UI-FF4B4B?style=for-the-badge&logo=chainlit&logoColor=white"/>
</p>

<p align="center">
  A production-grade, locally-hosted AI customer service agent for e-commerce platforms.<br/>
  Handles product discovery, store policies, and multi-turn conversations — with zero hallucinated prices.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Agent](#running-the-agent)
- [Capabilities](#capabilities)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Overview

EcomAgent is a locally-hosted AI customer service system built for e-commerce. It uses a **LangGraph state machine** to route user queries between two RAG pipelines — a product catalog search and an FAQ knowledge base — then generates accurate, context-rich responses using a local LLM via Ollama.

**Key guarantees:**
- Prices and product details are always sourced from your database — never generated from model weights
- Follow-up questions (e.g. *"how much is it?"*) are resolved against conversation history before searching
- Low-confidence RAG results are flagged and handled transparently, not silently hallucinated over
- All inference runs locally — no data leaves your machine

---

## Architecture

```
User Message
     │
     ▼
┌─────────────────┐
│   Router Node   │  ← Classifies intent: "faq" or "product"
│  (qwen2.5:7b)   │    using structured output (RouterResponse)
└────────┬────────┘
         │
   ┌─────┴──────┐
   ▼            ▼
┌──────┐   ┌──────────┐
│ FAQ  │   │ Inventory │   ← Conditional edge via select_workflow()
│ Node │   │   Node    │
└──┬───┘   └────┬──────┘
   │             │
   ▼             ▼
┌─────────────────────┐
│  _build_enriched_   │   ← Detects follow-up queries, prepends
│     query()         │     conversation context before searching
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Qdrant Vector DB  │   ← Semantic search (cosine similarity)
│  FAQ | Inventory    │     qwen3-embedding:8b embeddings
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Brain Chain      │   ← Formats retrieved context, applies
│   (qwen2.5:7b)      │     hard accuracy rules, generates answer
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Chainlit UI       │   ← Streams response to user
│  (MemorySaver)      │     Thread-safe, session-persistent
└─────────────────────┘
```

---

## How It Works

### 1. Routing
Every user message is classified by a dedicated router chain using **structured output** (`RouterResponse` via Pydantic). This guarantees the output is always `"faq"` or `"product"` — never a free-form string that could break the conditional edge.

### 2. Query Enrichment
Before hitting Qdrant, the agent runs `_build_enriched_query()`. This detects vague follow-up questions (short queries, pronouns, price words) and prepends context from the previous AI message. This prevents the most common RAG failure mode: sending *"how much is it?"* to the vector store with no product name, getting a wrong match, and hallucinating a price.

```
User turn 1: "Do you have wireless headphones?"
Agent reply: "Yes, the Astra X1 Wireless Headphones are..."

User turn 2: "How much is it?"
Enriched query: "Astra X1 Wireless Headphones... — How much is it?"
               └── Qdrant now finds the correct product at HIGH confidence
```

### 3. Retrieval & Confidence Scoring
Qdrant returns the top-3 results by cosine similarity. Each result is labeled `HIGH` (score ≥ 0.45) or `LOW` in the formatted context string passed to the brain. The brain prompt has explicit handling rules for each confidence tier — it never silently treats a 0.21-score result as authoritative.

### 4. Brain Chain
The brain receives:
- A formatted, human-readable context block (not a raw Python list)
- The full conversation history
- Hard accuracy rules: prices must be copied character-for-character from retrieved data; if absent, output a fixed fallback phrase — never generate a number from training weights

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Orchestration** | LangGraph | State machine, conditional routing, memory |
| **LLM** | Ollama + qwen2.5:7b | Router and brain inference (local) |
| **Embeddings** | Ollama + qwen3-embedding:8b | Semantic vector generation (local) |
| **Vector DB** | Qdrant | FAQ and inventory semantic search |
| **UI** | Chainlit | Chat interface with session management |
| **Framework** | LangChain | Prompt templates, chains, structured output |
| **Validation** | Pydantic | Router output schema enforcement |

---

## Project Structure

```
ecom_agent/
├── agent/
│   ├── graph/
│   │   ├── graph.py          # StateGraph assembly and compilation
│   │   ├── nodes.py          # router_node, faq_search_node, inventory_search_node
│   │   ├── edges.py          # select_workflow() conditional routing logic
│   │   └── state.py          # AIState (MessagesState + workflow + memory_context)
│   └── utils/
│       ├── chains.py         # get_router_chain(), get_brain_chain()
│       ├── prompts.py        # ROUTER_PROMPT, BRAIN_PROMPT
│       └── model_factory.py  # get_text_model()
├── memory/
│   └── vector_store.py       # ShopVectorStore: Qdrant client, search_faq(), search_inventory()
├── data/
│   ├── faq.json              # FAQ entries: {question, answer}
│   └── inventory.json        # Product catalog: {id, name, category, price, description, quantity}
└── app.py                    # Chainlit entry point
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- [Qdrant](https://qdrant.tech) running locally (Docker recommended)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ecom-agent.git
cd ecom-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull required Ollama models

```bash
ollama pull qwen2.5:7b
ollama pull qwen3-embedding:8b
```

### 5. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 6. Load data into Qdrant

```bash
python -m ecom_agent.memory.vector_store
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `QDRANT_URL` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `LLM_MODEL` | `qwen2.5:7b` | Ollama model for router and brain |
| `EMBEDDING_MODEL` | `qwen3-embedding:8b` | Ollama model for embeddings |
| `RELEVANCE_THRESHOLD` | `0.45` | Minimum cosine score to treat a result as HIGH confidence |
| `ROUTER_TEMPERATURE` | `0.1` | Router LLM temperature (keep low for deterministic routing) |
| `BRAIN_TEMPERATURE` | `0.3` | Brain LLM temperature |

---

## Running the Agent

```bash
chainlit run ecom_agent/app.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Capabilities

### Active

| Capability | Examples |
|---|---|
| **Product search** | *"Do you have wireless headphones?"*, *"Show me laptops under $800"* |
| **Product details** | *"What are the specs of the Astra X1?"*, *"What colors does it come in?"* |
| **Recommendations** | *"What's a good headphone for commuting?"* |
| **Price lookup** | *"How much is it?"*, *"What's the price of the X1?"* |
| **Store policies** | *"What is your return policy?"*, *"How long does shipping take?"* |
| **Support questions** | *"Can I cancel my order?"*, *"What payment methods do you accept?"* |
| **Multi-turn follow-ups** | *"Tell me more"*, *"What about the color?"*, *"And the price?"* |

### Roadmap

| Capability | Status |
|---|---|
| `create_order` | Planned |
| `track_order` | Planned |
| `return_order` | Planned |

When a user asks for a future capability, the agent acknowledges the request, explains it's not yet active, and redirects to the closest available help.

---

## Design Decisions

### Why LangGraph over a simple chain?
A linear chain can't branch. Routing FAQ vs. product queries requires a conditional graph with separate retrieval nodes. LangGraph's `StateGraph` with `add_conditional_edges` handles this cleanly, and `MemorySaver` gives persistent multi-turn memory per session with zero extra infrastructure.

### Why structured output for the router?
Free-form LLM output for routing is brittle. Using `.with_structured_output(RouterResponse)` with a Pydantic schema guarantees the router always returns exactly `"faq"` or `"product"` — no string parsing, no edge case where `"FAQ"` or `"product\n"` breaks the conditional edge.

### Why format memory_context to a string before the prompt?
Passing a raw `List[Dict]` into a LangChain prompt template causes `str()` to be called on it, producing an unreadable dict dump inside the system message. The brain model then tries to parse Python object notation as natural language and fails. Pre-formatting to a labeled, human-readable block gives the model clean signal to reason over.

### Why query enrichment instead of a separate context-tracking node?
A dedicated context-tracking node would add latency and another LLM call per turn. Query enrichment is a deterministic heuristic (check word count + pronoun list, prepend 150 chars of the last AI message) — O(1), no extra inference, and covers the vast majority of follow-up patterns in e-commerce conversations.

### Why a hard `RULE A` for prices instead of a soft instruction?
Soft instructions (*"never invent data"*) are interpreted probabilistically by LLMs. When retrieved data was weak, the model filled the gap with a plausible training-data price. Hard procedural rules (*"copy character-for-character; if absent, output this exact phrase"*) remove the ambiguity and leave the model no inference path to a fabricated number.

---

## Known Limitations

- **Model size**: `qwen2.5:7b` is capable but will occasionally misroute ambiguous queries. A 14B or 32B model improves routing accuracy significantly.
- **Embedding drift**: FAQ and inventory embeddings are generated at load time. If you update `faq.json` or `inventory.json`, re-run the loader script — Qdrant will not auto-update.
- **Follow-up enrichment is heuristic**: The enrichment function uses word count and a fixed keyword list. Complex multi-entity follow-ups (*"which of those two is cheaper?"*) may not enrich correctly.
- **No auth layer**: Chainlit is running unauthenticated. Add Chainlit's built-in auth or a reverse proxy before any public deployment.
- **Single language**: Prompts and enrichment heuristics are English-only.

---

## Roadmap

- [ ] `track_order` node — query order management system by order ID
- [ ] `create_order` node — guided checkout flow via tool calls
- [ ] `return_order` node — initiate return requests against order DB
- [ ] Streaming responses — token-by-token output in Chainlit
- [ ] Re-ranker — add a cross-encoder re-ranking step after Qdrant retrieval for higher precision
- [ ] Multi-language routing — detect user language and respond in kind
- [ ] Admin dashboard — view retrieval scores, routing decisions, and session logs in real time
- [ ] Evaluation suite — automated test runner against the 20-question test matrix

---
