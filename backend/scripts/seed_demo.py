from datetime import date
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.session import engine, SessionLocal
from app.knowledge.service import sync_markdown_repository
from app.models.base import Base
from app.models.erp import Account, Company, Document, LedgerTransaction, User, Vendor


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Company.id).where(Company.id == 1)):
            sync_markdown_repository(db)
            return

        company = Company(id=1, code="TH01", name="Siam Manufacturing Co., Ltd.")
        other_company = Company(id=2, code="TH02", name="Bangkok Retail Co., Ltd.")
        db.add_all([company, other_company])
        db.flush()
        db.add_all([
            User(id=1, email="accountant@example.com", role="Accountant", company_id=1),
            User(id=2, email="viewer.other@example.com", role="Viewer", company_id=2),
        ])
        ap = Account(
            id=1,
            company_id=1,
            account_code="2100",
            account_name="Accounts Payable",
            account_type="liability",
            normal_balance="credit",
            module="AP",
            description="Trade payables from supplier invoices.",
        )
        purchase = Account(
            id=2,
            company_id=1,
            account_code="5100",
            account_name="Purchases",
            account_type="expense",
            normal_balance="debit",
            module="GL",
            description="Purchase expense clearing account.",
        )
        db.add_all([ap, purchase])
        vendors = [
            Vendor(id=1, company_id=1, code="V-ABC", name="ABC Supply Co., Ltd."),
            Vendor(id=2, company_id=1, code="V-NOVA", name="Nova Packaging"),
            Vendor(id=3, company_id=2, code="V-OTHER", name="Other Company Vendor"),
        ]
        db.add_all(vendors)
        db.flush()
        docs = [
            Document(id=1, company_id=1, vendor_id=1, document_no="OPEN-2025-ABC", document_type="opening", document_date=date(2025, 1, 1), posting_date=date(2025, 1, 1), status="posted"),
            Document(id=2, company_id=1, vendor_id=1, document_no="PI-2025-001", document_type="purchase_invoice", document_date=date(2025, 12, 1), posting_date=date(2025, 12, 2), status="posted"),
            Document(id=3, company_id=1, vendor_id=1, document_no="PV-2025-001", document_type="payment", document_date=date(2025, 12, 15), posting_date=date(2025, 12, 15), status="posted"),
            Document(id=4, company_id=1, vendor_id=1, document_no="PI-2025-002", document_type="purchase_invoice", document_date=date(2025, 12, 20), posting_date=date(2025, 12, 22), status="reversed", reversal_document_no="RV-2025-010"),
            Document(id=5, company_id=1, vendor_id=1, document_no="RV-2025-010", document_type="reversal", document_date=date(2025, 12, 23), posting_date=date(2025, 12, 23), status="posted", reference_document_no="PI-2025-002"),
            Document(id=6, company_id=1, vendor_id=2, document_no="PI-2025-050", document_type="purchase_invoice", document_date=date(2025, 12, 5), posting_date=date(2025, 12, 5), status="posted"),
        ]
        db.add_all(docs)
        db.flush()
        db.add_all([
            LedgerTransaction(company_id=1, vendor_id=1, document_id=1, account_id=1, source_module="AP", posting_date=date(2025, 1, 1), debit=0, credit=80000, memo="opening balance"),
            LedgerTransaction(company_id=1, vendor_id=1, document_id=2, account_id=1, source_module="AP", posting_date=date(2025, 12, 2), debit=0, credit=70000, memo="supplier invoice"),
            LedgerTransaction(company_id=1, vendor_id=1, document_id=3, account_id=1, source_module="AP", posting_date=date(2025, 12, 15), debit=25000, credit=0, memo="supplier payment"),
            LedgerTransaction(company_id=1, vendor_id=1, document_id=4, account_id=1, source_module="AP", posting_date=date(2025, 12, 22), debit=0, credit=15000, memo="supplier invoice reversed later"),
            LedgerTransaction(company_id=1, vendor_id=1, document_id=5, account_id=1, source_module="AP", posting_date=date(2025, 12, 23), debit=15000, credit=0, memo="reversal document"),
            LedgerTransaction(company_id=1, vendor_id=2, document_id=6, account_id=1, source_module="AP", posting_date=date(2025, 12, 5), debit=0, credit=42000, memo="supplier invoice"),
        ])
        db.commit()
        sync_markdown_repository(db)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seeded demo ERP data.")
