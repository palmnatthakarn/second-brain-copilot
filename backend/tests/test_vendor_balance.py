from datetime import date

from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.erp import Account, AuditLog, Company, Document, LedgerTransaction, User, Vendor
from scripts.seed_demo import seed
from app.tools.registry import explain_vendor_balance


ERP_TABLES = [
    Company.__table__,
    User.__table__,
    Vendor.__table__,
    Account.__table__,
    Document.__table__,
    LedgerTransaction.__table__,
    AuditLog.__table__,
]


def setup_module():
    # Only drop the ERP demo tables. knowledge_notes/knowledge_sync_events are owned by
    # infra/postgres/init/001_knowledge_pgvector.sql (pgvector column, generated search_vector,
    # indexes) and must not be recreated from the plain ORM model, which would drop those extras.
    Base.metadata.drop_all(bind=engine, tables=ERP_TABLES)
    seed()


def test_explain_vendor_balance_traces_documents():
    db = SessionLocal()
    try:
        answer = explain_vendor_balance(db, user_id=1, company_id=1, vendor_id=1, as_of_date=date(2025, 12, 31))
        assert answer.calculation.opening_balance == 80000
        assert answer.calculation.debit == 40000
        assert answer.calculation.credit == 85000
        assert answer.calculation.closing_balance == 125000
        assert any(doc.document_no == "RV-2025-010" for doc in answer.documents)
        assert answer.warnings
    finally:
        db.close()
