from datetime import date
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    vendor_query: str | None = None
    vendor_id: int | None = None
    company_id: int = 1
    as_of_date: date
    user_id: int = 1


class Calculation(BaseModel):
    opening_balance: float
    debit: float
    credit: float
    closing_balance: float
    formula: str


class SourceDocument(BaseModel):
    document_no: str
    document_type: str
    document_date: date
    posting_date: date
    status: str
    debit: float
    credit: float
    reversal_document_no: str | None = None


class CopilotAnswer(BaseModel):
    answer: str
    company_id: int
    vendor_id: int
    vendor_code: str
    vendor_name: str
    as_of_date: date
    calculation: Calculation
    documents: list[SourceDocument]
    warnings: list[str]
    sources: list[str]


class VendorSearchResult(BaseModel):
    id: int
    code: str
    name: str
    company_id: int
