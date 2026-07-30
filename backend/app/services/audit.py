import hashlib
import json
import time
from contextlib import contextmanager
from sqlalchemy.orm import Session

from app.models.erp import AuditLog


@contextmanager
def audit_tool(db: Session, user_id: int, company_id: int, question: str, tool_name: str, parameters: dict):
    started = time.perf_counter()
    payload = {"rows": 0, "answer": {}, "warnings": []}
    try:
        yield payload
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        parameter_json = json.dumps(parameters, default=str, sort_keys=True)
        query_hash = hashlib.sha256(parameter_json.encode()).hexdigest()
        db.add(
            AuditLog(
                user_id=user_id,
                company_id=company_id,
                question=question,
                tool_name=tool_name,
                parameters_json=parameter_json,
                query_hash=query_hash,
                row_count=payload["rows"],
                elapsed_ms=elapsed_ms,
                answer_json=json.dumps(payload["answer"], default=str),
                warning_json=json.dumps(payload["warnings"], default=str),
            )
        )
        db.commit()
