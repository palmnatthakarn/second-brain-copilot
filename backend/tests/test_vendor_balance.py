from datetime import date

from app.db.session import SessionLocal, engine
from app.models.base import Base
from scripts.seed_demo import seed
from app.tools.registry import explain_vendor_balance


def setup_module():
    Base.metadata.drop_all(bind=engine)
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
