from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io

from app.db.session import get_db
from app.schemas.copilot import ChatRequest, CopilotAnswer, VendorSearchResult
from app.services.audit import audit_tool
from app.services.orchestrator import execute_planned_tool, get_ai_status, plan_tool_call
from app.services.security import PermissionError
from app.tools.registry import explain_vendor_balance, search_vendor


router = APIRouter()


@router.get("/vendors", response_model=list[VendorSearchResult])
def vendors(query: str, company_id: int = 1, user_id: int = 1, db: Session = Depends(get_db)):
    try:
        return search_vendor(db, user_id=user_id, company_id=company_id, query=query)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/ai/status")
def ai_status():
    return get_ai_status()


@router.post("/copilot/chat", response_model=CopilotAnswer)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        plan = plan_tool_call(db, request)
        params = request.model_dump()
        params["planner"] = plan["planner"]
        params["tool_parameters"] = plan["parameters"]
        with audit_tool(db, request.user_id, request.company_id, request.question, plan["tool_name"], params) as audit:
            answer = execute_planned_tool(db, request.user_id, plan)
            audit["rows"] = len(answer.documents)
            audit["answer"] = answer.model_dump()
            audit["warnings"] = answer.warnings
            return answer
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/exports/vendor-balance.csv")
def export_vendor_balance(request: ChatRequest, db: Session = Depends(get_db)):
    answer = chat(request, db)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["vendor_code", "vendor_name", "as_of_date", "opening", "debit", "credit", "closing"])
    writer.writerow([
        answer.vendor_code,
        answer.vendor_name,
        answer.as_of_date,
        answer.calculation.opening_balance,
        answer.calculation.debit,
        answer.calculation.credit,
        answer.calculation.closing_balance,
    ])
    writer.writerow([])
    writer.writerow(["document_no", "document_type", "document_date", "posting_date", "status", "debit", "credit"])
    for document in answer.documents:
        writer.writerow([
            document.document_no,
            document.document_type,
            document.document_date,
            document.posting_date,
            document.status,
            document.debit,
            document.credit,
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vendor-balance.csv"},
    )
