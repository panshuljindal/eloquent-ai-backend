from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

from pinecone import Pinecone


class PineconeHelper:
    def __init__(self) -> None:
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
        """Query vector DB and return concatenated textual context snippets."""
        query_payload: Dict[str, Any] = {
            "inputs": {"text": query_text},
            "top_k": top_k,
        }
        result: Dict[str, Any] = self._index.search(query=query_payload, namespace=self._namespace)  # type: ignore[no-any-return]
        docs = ""
        for hit in result.get("result", {}).get("hits", []):
            fields = hit.get("fields", {})
            docs += (
                f"Source: {hit.get('_id','unknown')}\n"
                f"Category: {fields.get('category','unknown')}\n"
                f"Text: {fields.get('text','')}\n\n"
            )
        return docs

@lru_cache
def get_pinecone_helper() -> PineconeHelper:
    return PineconeHelper()