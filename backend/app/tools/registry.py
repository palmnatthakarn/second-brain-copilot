from datetime import date
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.erp import Document, LedgerTransaction, Vendor
from app.schemas.copilot import Calculation, CopilotAnswer, SourceDocument, VendorSearchResult
from app.services.security import assert_company_scope


AP_ACCOUNT_CODE = "2100"


def search_vendor(db: Session, user_id: int, company_id: int, query: str) -> list[VendorSearchResult]:
    assert_company_scope(db, user_id, company_id)
    term = f"%{query.lower()}%"
    rows = db.execute(
        select(Vendor)
        .where(Vendor.company_id == company_id)
        .where(or_(func.lower(Vendor.name).like(term), func.lower(Vendor.code).like(term)))
        .order_by(Vendor.code)
        .limit(20)
    ).scalars()
    return [VendorSearchResult(id=v.id, code=v.code, name=v.name, company_id=v.company_id) for v in rows]


def explain_vendor_balance(
    db: Session,
    user_id: int,
    company_id: int,
    vendor_id: int,
    as_of_date: date,
) -> CopilotAnswer:
    assert_company_scope(db, user_id, company_id)
    vendor = db.get(Vendor, vendor_id)
    if not vendor or vendor.company_id != company_id:
        raise ValueError("Vendor not found in the requested company.")

    rows = db.execute(
        select(LedgerTransaction)
        .join(LedgerTransaction.account)
        .where(LedgerTransaction.company_id == company_id)
        .where(LedgerTransaction.vendor_id == vendor_id)
        .where(LedgerTransaction.posting_date <= as_of_date)
        .where(LedgerTransaction.account.has(account_code=AP_ACCOUNT_CODE))
        .order_by(LedgerTransaction.posting_date, LedgerTransaction.id)
    ).scalars().all()

    opening_rows = [r for r in rows if r.memo.lower().startswith("opening")]
    movement_rows = [r for r in rows if r not in opening_rows]
    opening = sum(float(r.credit) - float(r.debit) for r in opening_rows)
    debit = sum(float(r.debit) for r in movement_rows)
    credit = sum(float(r.credit) for r in movement_rows)
    closing = opening + credit - debit

    documents = [
        SourceDocument(
            document_no=r.document.document_no if r.document else "NO-DOC",
            document_type=r.document.document_type if r.document else "manual",
            document_date=r.document.document_date if r.document else r.posting_date,
            posting_date=r.posting_date,
            status=r.document.status if r.document else "missing_document",
            debit=float(r.debit),
            credit=float(r.credit),
            reversal_document_no=r.document.reversal_document_no if r.document else None,
        )
        for r in movement_rows
    ]

    warnings = []
    if not rows:
        warnings.append("No AP ledger transactions found for this vendor and date.")
    if any(d.status == "reversed" or d.reversal_document_no for d in documents):
        warnings.append("One or more documents were reversed. Review reversal documents before relying on the balance.")
    if any(d.document_no == "NO-DOC" for d in documents):
        warnings.append("Some ledger transactions have no source document reference.")

    return CopilotAnswer(
        answer=f"{vendor.name} ({vendor.code}) has AP balance {closing:,.2f} as of {as_of_date}.",
        company_id=company_id,
        vendor_id=vendor.id,
        vendor_code=vendor.code,
        vendor_name=vendor.name,
        as_of_date=as_of_date,
        calculation=Calculation(
            opening_balance=opening,
            debit=debit,
            credit=credit,
            closing_balance=closing,
            formula="closing_balance = opening_balance + credit - debit for AP normal credit balance",
        ),
        documents=documents,
        warnings=warnings,
        sources=["ledger_transactions", "documents", "vendors", "accounts"],
    )


def find_reversal_document(db: Session, user_id: int, company_id: int, document_no: str) -> list[dict]:
    assert_company_scope(db, user_id, company_id)
    rows = db.execute(
        select(Document)
        .where(Document.company_id == company_id)
        .where(or_(Document.document_no == document_no, Document.reference_document_no == document_no))
    ).scalars().all()
    return [
        {
            "document_no": row.document_no,
            "status": row.status,
            "reversal_document_no": row.reversal_document_no,
            "reference_document_no": row.reference_document_no,
        }
        for row in rows
    ]
