from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeNoteOut(BaseModel):
    id: int
    slug: str
    path: str
    title: str
    category: str
    tags: list[str]
    links: list[str]
    frontmatter: dict
    excerpt: str
    content_hash: str
    embedding_status: str
    updated_at: datetime


class KnowledgeSyncResponse(BaseModel):
    repository: str
    detected: int
    created: int
    updated: int
    unchanged: int
    deleted: int
    indexed: int
    embedded: int


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeNoteOut]


class KnowledgeHybridSearchResult(KnowledgeNoteOut):
    text_score: float
    vector_score: float
    hybrid_score: float


class KnowledgeHybridSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    text_weight: float = Field(default=0.65, ge=0, le=1)
    vector_weight: float = Field(default=0.35, ge=0, le=1)


class KnowledgeHybridSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeHybridSearchResult]


class KnowledgeCaptureRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category: str = Field(default="Inbox", max_length=80)
    tags: list[str] = Field(default_factory=list)


class KnowledgeCaptureResponse(BaseModel):
    note: KnowledgeNoteOut
    wrote_markdown: bool


class KnowledgeChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    category: str | None = None
    limit: int = Field(default=6, ge=1, le=12)


class KnowledgeChatResponse(BaseModel):
    answer: str
    sources: list[KnowledgeNoteOut]
    warnings: list[str]
