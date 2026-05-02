import os, json

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct, Distance
from langchain_ollama.embeddings import OllamaEmbeddings

from typing import List

class ShopVectorStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url="localhost", port=6333)
        self.model = OllamaEmbeddings(model="qwen3-embedding:8b")

        self.faq_collection = "FAQ"
        self.inventory_collection = "Inventory"

    def _collection_exists(self, collection_name: str) -> bool:
        collections = self.client.get_collections().collections
        return any(c.name == collection_name for c in collections)

    def _create_collection(self, collection_name: str) -> None:
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=4096,
                distance=Distance.COSINE
            )
        )

    def _load_faq_collection(self, faq_path: str):
        if not self._collection_exists(self.faq_collection):
            self._create_collection(self.faq_collection)

        with open(faq_path, "r") as f:
            faqs = json.load(f)

        points = []

        for i,faq in enumerate(faqs):
            question = faq["question"]
            answer = faq["answer"]

            vector = self.model.embed_query(question)

            points.append(
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "question": question,
                        "answer": answer,
                    }
                )
            )

        self.client.upsert(
            collection_name=self.faq_collection,
            points=points
        )

    def _load_inventory_collection(self, inventory_path: str):
        if not self._collection_exists(self.inventory_collection):
            self._create_collection(self.inventory_collection)

        with open(inventory_path, "r") as f:
            inventory = json.load(f)

        points = []

        for i,inv in enumerate(inventory):
            id = inv["id"]
            name = inv["name"]
            category = inv["category"]
            quantity = inv["quantity"]
            price = inv["price"]
            description = inv["description"]

            vector = self.model.embed_query(description)

            points.append(
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "id": id,
                        "name": name,
                        "category": category,
                        "quantity": quantity,
                        "price": price,
                        "description": description
                    }
                )
            )

        self.client.upsert(
            collection_name=self.inventory_collection,
            points=points
        )

    def search_faq(self, query: str, limit: int = 3):
        query_vector = self.model.embed_query(query)

        results = self.client.query_points(
            collection_name=self.faq_collection,
            query=query_vector,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "question": r.payload["question"],
                "answer": r.payload["answer"],
                "score": r.score
            }
            for r in results.points
        ]

    def search_inventory(self, query: str, limit: int = 3):
        query_vector = self.model.embed_query(query)

        results = self.client.query_points(
            collection_name=self.inventory_collection,
            query=query_vector,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "id": r.payload["id"],
                "name": r.payload["name"],
                "category": r.payload["category"],
                "quantity": r.payload["quantity"],
                "price": r.payload["price"],
                "description": r.payload["description"],
                "score": r.score
            }
            for r in results.points
        ]

def get_vector_store() -> ShopVectorStore:
    return ShopVectorStore()