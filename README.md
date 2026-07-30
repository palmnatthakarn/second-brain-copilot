# AI AP & GL Copilot

MVP scaffold for an AI ERP copilot focused on AP vendor balances and GL traceability.

## Stack

- Backend: FastAPI, Pydantic, SQLAlchemy
- Frontend: Next.js, TypeScript, Tailwind CSS
- Database: SQLite for local development, PostgreSQL-ready models
- AI: Tool-calling orchestrator boundary with deterministic ERP tools

## Quick Start

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r backend\\requirements.txt
python backend\\scripts\\seed_demo.py
uvicorn app.main:app --app-dir backend --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The local OpenAI key is stored in `.env.local` as `OPENAI_API_KEY`.

If npm is blocked by local memory or paging-file limits, run the FastAPI backend and open `preview.html` directly in a browser for a dependency-free MVP preview.

## MVP Guardrails

- The AI layer selects tools and parameters only.
- Backend owns all SQL, calculations, permission checks, limits, and audit logs.
- All ERP data operations are read-only in the MVP.
- Responses include calculation details, source documents, warnings, and exportable evidence.

## Second Brain Knowledge Layer

Markdown knowledge lives in `knowledge-vault/` and can be opened with Obsidian or any Markdown editor.

Knowledge endpoints:

- `POST /api/knowledge/sync`
- `POST /api/knowledge/search`
- `POST /api/knowledge/capture`
- `POST /api/knowledge/chat`

The MVP indexes Markdown into SQL for full-text-like search. `pgvector` is part of the target architecture and can be added after embeddings are enabled.

Synchronization pipeline:

1. Detect new, changed, or deleted Markdown files by path and SHA-256 content hash.
2. Read frontmatter from `---` blocks.
3. Update the `knowledge_notes` table.
4. Build `search_text` plus an embedding vector. By default this uses a local deterministic vector so Markdown content stays on the machine. Set `ENABLE_OPENAI_EMBEDDINGS=true` only when you explicitly want external embeddings.

Run continuous sync:

```powershell
python backend\scripts\watch_markdown.py
```

PostgreSQL/pgvector setup is documented in `docs/postgres-pgvector.md`. The local API also exposes `POST /api/knowledge/hybrid-search`.
