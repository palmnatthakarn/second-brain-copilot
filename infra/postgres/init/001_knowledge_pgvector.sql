CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_notes (
  id BIGSERIAL PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  links JSONB NOT NULL DEFAULT '[]'::jsonb,
  frontmatter_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  search_text TEXT NOT NULL DEFAULT '',
  search_vector TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(category, '')), 'B') ||
    setweight(to_tsvector('simple', coalesce(search_text, '')), 'C')
  ) STORED,
  embedding VECTOR(32),
  embedding_status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS knowledge_notes_search_vector_idx
  ON knowledge_notes USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS knowledge_notes_category_idx
  ON knowledge_notes (category);

CREATE INDEX IF NOT EXISTS knowledge_notes_embedding_idx
  ON knowledge_notes USING IVFFLAT (embedding vector_cosine_ops)
  WITH (lists = 16);

CREATE TABLE IF NOT EXISTS knowledge_sync_events (
  id BIGSERIAL PRIMARY KEY,
  repository TEXT NOT NULL,
  detected_count INTEGER NOT NULL,
  created_count INTEGER NOT NULL,
  updated_count INTEGER NOT NULL,
  unchanged_count INTEGER NOT NULL,
  deleted_count INTEGER NOT NULL,
  indexed_count INTEGER NOT NULL,
  embedded_count INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION hybrid_knowledge_search(
  query_text TEXT,
  query_embedding VECTOR(32),
  category_filter TEXT DEFAULT NULL,
  text_weight DOUBLE PRECISION DEFAULT 0.65,
  vector_weight DOUBLE PRECISION DEFAULT 0.35,
  match_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  path TEXT,
  title TEXT,
  category TEXT,
  text_score DOUBLE PRECISION,
  vector_score DOUBLE PRECISION,
  hybrid_score DOUBLE PRECISION
) AS $$
  SELECT
    n.id,
    n.path,
    n.title,
    n.category,
    ts_rank_cd(n.search_vector, plainto_tsquery('simple', query_text))::DOUBLE PRECISION AS text_score,
    (1 - (n.embedding <=> query_embedding))::DOUBLE PRECISION AS vector_score,
    (
      text_weight * ts_rank_cd(n.search_vector, plainto_tsquery('simple', query_text)) +
      vector_weight * (1 - (n.embedding <=> query_embedding))
    )::DOUBLE PRECISION AS hybrid_score
  FROM knowledge_notes n
  WHERE (category_filter IS NULL OR n.category = category_filter)
    AND n.embedding IS NOT NULL
  ORDER BY hybrid_score DESC
  LIMIT match_limit;
$$ LANGUAGE SQL STABLE;
