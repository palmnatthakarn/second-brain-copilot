from datetime import datetime
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(50))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="active")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    account_code: Mapped[str] = mapped_column(String(30))
    account_name: Mapped[str] = mapped_column(String(200))
    account_type: Mapped[str] = mapped_column(String(50))
    normal_balance: Mapped[str] = mapped_column(String(10))
    module: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    document_no: Mapped[str] = mapped_column(String(80), unique=True)
    document_type: Mapped[str] = mapped_column(String(30))
    document_date: Mapped[Date] = mapped_column(Date)
    posting_date: Mapped[Date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30))
    reversal_document_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reference_document_no: Mapped[str | None] = mapped_column(String(80), nullable=True)

    vendor: Mapped[Vendor] = relationship()


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    source_module: Mapped[str] = mapped_column(String(20))
    posting_date: Mapped[Date] = mapped_column(Date)
    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    memo: Mapped[str] = mapped_column(Text)

    document: Mapped[Document | None] = relationship()
    account: Mapped[Account] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    company_id: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    question: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str] = mapped_column(String(100))
    parameters_json: Mapped[str] = mapped_column(Text)
    query_hash: Mapped[str] = mapped_column(String(64))
    row_count: Mapped[int]
    elapsed_ms: Mapped[int]
    answer_json: Mapped[str] = mapped_column(Text)
    warning_json: Mapped[str] = mapped_column(Text)


class KnowledgeNote(Base):
    __tablename__ = "knowledge_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    path: Mapped[str] = mapped_column(String(500), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(80))
    tags: Mapped[str] = mapped_column(Text, default="[]")
    links: Mapped[str] = mapped_column(Text, default="[]")
    frontmatter_json: Mapped[str] = mapped_column(Text, default="{}")
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    search_text: Mapped[str] = mapped_column(Text, default="")
    embedding_json: Mapped[str] = mapped_column(Text, default="[]")
    embedding_status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeSyncEvent(Base):
    __tablename__ = "knowledge_sync_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    repository: Mapped[str] = mapped_column(Text)
    detected_count: Mapped[int]
    created_count: Mapped[int]
    updated_count: Mapped[int]
    unchanged_count: Mapped[int]
    deleted_count: Mapped[int]
    indexed_count: Mapped[int]
    embedded_count: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
