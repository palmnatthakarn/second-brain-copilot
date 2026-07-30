# PostgreSQL And pgvector

The production target uses PostgreSQL plus pgvector for hybrid search.

## Local Container

`docker-compose.yml` uses:

```yaml
image: pgvector/pgvector:pg16
```

Init SQL:

```text
infra/postgres/init/001_knowledge_pgvector.sql
```

It creates:

- `knowledge_notes`
- `knowledge_sync_events`
- generated `search_vector`
- GIN full-text index
- IVFFLAT vector index
- `hybrid_knowledge_search(...)`

## API

```text
POST /api/knowledge/hybrid-search
```

Local SQLite development computes hybrid scoring in Python from `search_text` and `embedding_json`.

PostgreSQL production can move scoring into `hybrid_knowledge_search(...)` and store embeddings in `VECTOR(32)`. If external embeddings are enabled later, change the vector dimension to the model dimension, such as `VECTOR(1536)` for `text-embedding-3-small`.
