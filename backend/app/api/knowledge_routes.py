from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.knowledge.service import answer_from_notes, capture_note, hybrid_search_notes, search_notes, sync_markdown_repository
from app.schemas.knowledge import (
    KnowledgeCaptureRequest,
    KnowledgeCaptureResponse,
    KnowledgeChatRequest,
    KnowledgeChatResponse,
    KnowledgeHybridSearchRequest,
    KnowledgeHybridSearchResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSyncResponse,
)


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/sync", response_model=KnowledgeSyncResponse)
def sync_knowledge(db: Session = Depends(get_db)):
    return sync_markdown_repository(db)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(request: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    return KnowledgeSearchResponse(
        query=request.query,
        results=search_notes(db, request.query, request.category, request.limit),
    )


@router.post("/hybrid-search", response_model=KnowledgeHybridSearchResponse)
def hybrid_search_knowledge(request: KnowledgeHybridSearchRequest, db: Session = Depends(get_db)):
    return KnowledgeHybridSearchResponse(
        query=request.query,
        results=hybrid_search_notes(
            db=db,
            query=request.query,
            category=request.category,
            limit=request.limit,
            text_weight=request.text_weight,
            vector_weight=request.vector_weight,
        ),
    )


@router.post("/capture", response_model=KnowledgeCaptureResponse)
def capture_knowledge(request: KnowledgeCaptureRequest, db: Session = Depends(get_db)):
    return KnowledgeCaptureResponse(note=capture_note(db, request), wrote_markdown=True)


@router.post("/chat", response_model=KnowledgeChatResponse)
def chat_with_knowledge(request: KnowledgeChatRequest, db: Session = Depends(get_db)):
    sources = search_notes(db, request.question, request.category, request.limit)
    answer, warnings = answer_from_notes(request.question, sources)
    return KnowledgeChatResponse(answer=answer, sources=sources, warnings=warnings)
