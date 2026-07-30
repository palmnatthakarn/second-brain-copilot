from app.db.session import SessionLocal
from app.knowledge.service import hybrid_search_notes, search_notes, sync_markdown_repository


def test_sync_and_search_markdown_repository():
    db = SessionLocal()
    try:
        result = sync_markdown_repository(db)
        second_result = sync_markdown_repository(db)
        notes = search_notes(db, "เจ้าหนี้ GL", limit=5)
        hybrid_notes = hybrid_search_notes(db, "เจ้าหนี้ GL", limit=5)
        assert result["detected"] >= 1
        assert result["indexed"] >= 0
        assert second_result["unchanged"] >= 1
        assert any("AP" in note.title or "Accounts Payable" in note.title for note in notes)
        assert hybrid_notes
        assert hybrid_notes[0].hybrid_score >= hybrid_notes[-1].hybrid_score
    finally:
        db.close()
