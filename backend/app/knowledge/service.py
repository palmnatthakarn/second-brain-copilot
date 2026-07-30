import json
import hashlib
import math
import re
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.knowledge.embedding import embedding_json
from app.knowledge.markdown import (
    excerpt,
    extract_links,
    extract_tags,
    markdown_document,
    note_category,
    note_title,
    parse_frontmatter,
    slugify,
)
from app.models.erp import KnowledgeNote, KnowledgeSyncEvent
from app.schemas.knowledge import KnowledgeCaptureRequest, KnowledgeHybridSearchResult, KnowledgeNoteOut


def repository_root() -> Path:
    configured = Path(get_settings().markdown_repository_path)
    if configured.is_absolute():
        return configured
    return Path.cwd() / configured


def search_terms(query: str) -> list[str]:
    """Return useful keywords from short English or Thai search questions."""
    normalized = re.sub(r"[?!.,;:]+", " ", query.lower()).strip()
    terms = [term for term in normalized.split() if term]
    thai_question_words = (
        "สามารถ", "นำไปใช้", "เมื่อใด", "อย่างไร", "อะไร", "หรือไม่",
        "ได้ไหม", "ได้หรือไม่", "ช่วย", "บอก", "หน่อย",
    )
    compact = normalized.replace(" ", "")
    for word in thai_question_words:
        compact = compact.replace(word, "")
    if len(compact) >= 2:
        terms.append(compact)
    return list(dict.fromkeys(terms))


def to_note_out(note: KnowledgeNote) -> KnowledgeNoteOut:
    return KnowledgeNoteOut(
        id=note.id,
        slug=note.slug,
        path=note.path,
        title=note.title,
        category=note.category,
        tags=json.loads(note.tags or "[]"),
        links=json.loads(note.links or "[]"),
        frontmatter=json.loads(note.frontmatter_json or "{}"),
        excerpt=excerpt(note.content),
        content_hash=note.content_hash,
        embedding_status=note.embedding_status,
        updated_at=note.updated_at,
    )


def sync_markdown_repository(db: Session) -> dict:
    root = repository_root()
    root.mkdir(parents=True, exist_ok=True)
    stats = {
        "repository": str(root),
        "detected": 0,
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "deleted": 0,
        "indexed": 0,
        "embedded": 0,
    }
    seen_paths: set[str] = set()
    existing = {note.path: note for note in db.execute(select(KnowledgeNote)).scalars().all()}

    for path in root.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root).as_posix()
        seen_paths.add(relative_path)
        stats["detected"] += 1
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        note = existing.get(relative_path)
        if note and note.content_hash == content_hash:
            stats["unchanged"] += 1
            continue

        now = datetime.now(UTC).replace(tzinfo=None)
        frontmatter, body = parse_frontmatter(content)
        search_text = "\n".join([note_title(path, content), note_category(root, path), " ".join(extract_tags(content)), body])
        vector_json, vector_status = embedding_json(search_text)
        if note is None:
            note = KnowledgeNote(slug=slugify(relative_path), path=relative_path, created_at=now)
            db.add(note)
            stats["created"] += 1
        else:
            stats["updated"] += 1

        note.title = note_title(path, content)
        note.category = note_category(root, path)
        note.tags = json.dumps(extract_tags(content), ensure_ascii=False)
        note.links = json.dumps(extract_links(content), ensure_ascii=False)
        note.frontmatter_json = json.dumps(frontmatter, ensure_ascii=False)
        note.content = content
        note.content_hash = content_hash
        note.search_text = search_text
        note.embedding_json = vector_json
        note.embedding_status = vector_status
        note.updated_at = now
        stats["indexed"] += 1
        stats["embedded"] += 1

    for relative_path, note in existing.items():
        if relative_path not in seen_paths:
            db.delete(note)
            stats["deleted"] += 1

    if stats["created"] or stats["updated"] or stats["deleted"]:
        db.add(KnowledgeSyncEvent(
            repository=stats["repository"],
            detected_count=stats["detected"],
            created_count=stats["created"],
            updated_count=stats["updated"],
            unchanged_count=stats["unchanged"],
            deleted_count=stats["deleted"],
            indexed_count=stats["indexed"],
            embedded_count=stats["embedded"],
        ))
    db.commit()
    return stats


def search_notes(db: Session, query: str, category: str | None = None, limit: int = 10) -> list[KnowledgeNoteOut]:
    terms = search_terms(query)
    statement = select(KnowledgeNote).where(KnowledgeNote.category != "Templates")
    if category:
        statement = statement.where(KnowledgeNote.category == category)
    if terms:
        filters = []
        for term in terms:
            pattern = f"%{term}%"
            filters.append(KnowledgeNote.title.ilike(pattern))
            filters.append(KnowledgeNote.content.ilike(pattern))
            filters.append(KnowledgeNote.tags.ilike(pattern))
            filters.append(KnowledgeNote.search_text.ilike(pattern))
        statement = statement.where(or_(*filters))
    statement = statement.order_by(KnowledgeNote.updated_at.desc()).limit(limit)
    return [to_note_out(note) for note in db.execute(statement).scalars().all()]


def _text_score(note: KnowledgeNote, terms: list[str]) -> float:
    if not terms:
        return 0.0
    haystack = " ".join([note.title, note.category, note.tags, note.search_text]).lower()
    hits = sum(1 for term in terms if term in haystack)
    title_bonus = sum(1 for term in terms if term in note.title.lower()) * 0.5
    return min(1.0, (hits + title_bonus) / max(len(terms), 1))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size])) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right[:size])) or 1.0
    return max(0.0, min(1.0, (dot / (left_norm * right_norm) + 1) / 2))


def hybrid_search_notes(
    db: Session,
    query: str,
    category: str | None = None,
    limit: int = 10,
    text_weight: float = 0.65,
    vector_weight: float = 0.35,
) -> list[KnowledgeHybridSearchResult]:
    from app.knowledge.embedding import build_embedding

    terms = [term.lower() for term in query.split() if term.strip()]
    query_embedding, _ = build_embedding(query)
    statement = select(KnowledgeNote)
    if category:
        statement = statement.where(KnowledgeNote.category == category)
    notes = db.execute(statement).scalars().all()
    scored: list[KnowledgeHybridSearchResult] = []
    for note in notes:
        text_score = _text_score(note, terms)
        vector_score = _cosine_similarity(query_embedding, json.loads(note.embedding_json or "[]"))
        hybrid_score = text_weight * text_score + vector_weight * vector_score
        scored.append(
            KnowledgeHybridSearchResult(
                **to_note_out(note).model_dump(),
                text_score=round(text_score, 4),
                vector_score=round(vector_score, 4),
                hybrid_score=round(hybrid_score, 4),
            )
        )
    return sorted(scored, key=lambda item: item.hybrid_score, reverse=True)[:limit]


def capture_note(db: Session, request: KnowledgeCaptureRequest) -> KnowledgeNoteOut:
    root = repository_root()
    target_dir = root / request.category
    target_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(request.title)
    path = target_dir / f"{slug}.md"
    counter = 2
    while path.exists():
        path = target_dir / f"{slug}-{counter}.md"
        counter += 1

    content = markdown_document(request.title, request.content, request.tags)
    path.write_text(content, encoding="utf-8")
    sync_markdown_repository(db)
    relative_path = path.relative_to(root).as_posix()
    note = db.execute(select(KnowledgeNote).where(KnowledgeNote.path == relative_path)).scalar_one()
    return to_note_out(note)


def answer_from_notes(question: str, notes: list[KnowledgeNoteOut]) -> tuple[str, list[str]]:
    if not notes:
        return "I could not find enough Markdown knowledge to answer reliably.", [
            "No matching Markdown notes were found. Capture or sync more notes first."
        ]
    summaries = []
    for note in notes[:3]:
        summaries.append(f"{note.title}\n{note.excerpt}")
    return "สรุปจาก Markdown ที่เกี่ยวข้อง:\n\n" + "\n\n".join(summaries), []
