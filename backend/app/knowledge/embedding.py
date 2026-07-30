import hashlib
import json
import math
import os

from dotenv import load_dotenv
from app.core.config import get_settings

load_dotenv(".env.local")


def local_embedding(text: str, dimensions: int = 32) -> list[float]:
    buckets = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        sign = 1 if digest[1] % 2 == 0 else -1
        buckets[index] += sign
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [round(value / norm, 6) for value in buckets]


def build_embedding(text: str) -> tuple[list[float], str]:
    if not get_settings().enable_openai_embeddings:
        return local_embedding(text), "local_disabled_external"
    if not os.getenv("OPENAI_API_KEY"):
        return local_embedding(text), "local"
    try:
        from openai import OpenAI

        client = OpenAI(max_retries=0, timeout=8.0)
        response = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
        return response.data[0].embedding, "openai"
    except Exception:
        return local_embedding(text), "local_fallback"


def embedding_json(text: str) -> tuple[str, str]:
    embedding, status = build_embedding(text)
    return json.dumps(embedding), status
