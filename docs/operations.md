# Second Brain Operations

## Daily operation

- Start PostgreSQL with `docker compose up -d` from `D:\postgres-pgvector`.
- Run FastAPI from `D:\Dashboard\AI phat`.
- Install the watcher Scheduled Task once with `powershell -ExecutionPolicy Bypass -File backend\scripts\install_watcher_task.ps1`.

## Backup

Run `powershell -ExecutionPolicy Bypass -File D:\postgres-pgvector\scripts\backup.ps1`.
Backups are stored in `D:\postgres-pgvector\backups` in PostgreSQL custom format.

## Restore

Stop FastAPI and the watcher before restoring. Restore replaces database contents:

`powershell -ExecutionPolicy Bypass -File D:\postgres-pgvector\scripts\restore.ps1 -BackupFile <path-to-dump> -ConfirmRestore`

## Security

- `D:\postgres-pgvector\.env` and `D:\Dashboard\AI phat\.env.local` contain secrets and must not be committed.
- PostgreSQL listens only on `127.0.0.1`.
- Grant access to the PostgreSQL port only through a secured tunnel when remote administration is necessary.
