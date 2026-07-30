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

When the backend is connected to PostgreSQL, `hybrid_search_notes()` calls `hybrid_knowledge_search(...)` directly instead of recomputing cosine similarity in Python. The sync step backfills the native `embedding` column from `embedding_json` on every sync, for any row still missing it.

**Dimension mismatch warning:** the `embedding` column is `VECTOR(32)`, matching the local hash-based embedding. If `ENABLE_OPENAI_EMBEDDINGS=true` is turned on, `text-embedding-3-small` produces 1536-dim vectors that no longer fit the column. This does not error loudly — affected rows are skipped (with a warning printed to the backend log) and simply keep `embedding IS NULL`, so they drop out of hybrid search results silently. Before enabling OpenAI embeddings in Postgres, migrate the column first:

```sql
ALTER TABLE knowledge_notes ALTER COLUMN embedding TYPE VECTOR(1536);
DROP INDEX IF EXISTS knowledge_notes_embedding_idx;
CREATE INDEX knowledge_notes_embedding_idx ON knowledge_notes USING ivfflat (embedding vector_cosine_ops);
```
