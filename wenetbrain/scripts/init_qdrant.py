#!/usr/bin/env python3
"""Initialize Qdrant collections for WenetBrain knowledge banks."""

import os

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE", "768"))

COLLECTIONS = [
    "group",
    "company_webwave",
    "team_product_webwave",
]


def init_collections():
    client = QdrantClient(url=QDRANT_URL)
    existing = {c.name for c in client.get_collections().collections}

    for name in COLLECTIONS:
        if name in existing:
            print(f"Collection '{name}' already exists — skipping.")
            continue
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )
        print(f"Created collection '{name}' with size={EMBEDDING_SIZE}.")

    # Private collections are created on-the-fly per user
    print("Qdrant initialization complete.")


if __name__ == "__main__":
    init_collections()
