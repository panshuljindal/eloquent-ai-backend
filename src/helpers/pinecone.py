import os
from functools import lru_cache
from typing import Any, Dict
from pinecone import Pinecone


class PineconeHelper:
    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")
        host = os.getenv("PINECONE_HOST")
        namespace = os.getenv("PINECONE_NAMESPACE", "__default__")
        if not api_key:
            raise RuntimeError("Missing PINECONE_API_KEY environment variable")
        if not host:
            raise RuntimeError("Missing PINECONE_HOST environment variable")
        self._namespace = namespace
        self._client = Pinecone(api_key=api_key)
        self._index = self._client.Index(host=host)

    def query(self, query_text: str, top_k: int = 10) -> str:
        query_payload = {
            "inputs": {"text": query_text},
            "top_k": top_k,
        }
        result =self._index.search(query=query_payload, namespace=self._namespace)
        docs = ""
        for hit in result['result']['hits']:
            docs += f"Source: {hit['_id']}\nCategory: {hit['fields']['category']}\nText: {hit['fields']['text']}\n\n"
        return docs


@lru_cache
def get_pinecone_helper() -> PineconeHelper:
    return PineconeHelper()