from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.session import SessionLocal
from app.knowledge.service import sync_markdown_repository


def watch(interval_seconds: int = 5) -> None:
    print(f"Watching Markdown repository every {interval_seconds}s. Press Ctrl+C to stop.")
    while True:
        db = SessionLocal()
        try:
            result = sync_markdown_repository(db)
            changed = result["created"] + result["updated"] + result["deleted"]
            if changed:
                print(result)
        finally:
            db.close()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    watch()
