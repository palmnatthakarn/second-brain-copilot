import json
import os
from datetime import date
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.schemas.copilot import ChatRequest, CopilotAnswer
from app.tools.registry import explain_vendor_balance, search_vendor


TOOL_REGISTRY = [
    {
        "type": "function",
        "function": {
            "name": "explain_vendor_balance",
            "description": "Calculate an AP vendor balance as of a posting date and return source documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "integer"},
                    "vendor_id": {"type": "integer"},
                    "as_of_date": {"type": "string", "format": "date"},
                },
                "required": ["company_id", "vendor_id", "as_of_date"],
                "additionalProperties": False,
            },
        },
    }
]


SYSTEM_PROMPT = """You are an AP and GL copilot planner.
Choose only one registered tool and pass parameters only.
Do not invent vendors, document numbers, SQL, balances, or explanations.
The backend owns permissions, queries, and calculations."""

load_dotenv(".env.local")


def resolve_vendor_id(db: Session, request: ChatRequest) -> int:
    if request.vendor_id is not None:
        return request.vendor_id

    matches = search_vendor(db, request.user_id, request.company_id, request.vendor_query or request.question)
    if len(matches) != 1:
        raise ValueError(f"Expected one vendor match, found {len(matches)}.")
    return matches[0].id


def plan_tool_call(db: Session, request: ChatRequest) -> dict[str, Any]:
    vendor_id = resolve_vendor_id(db, request)
    fallback = {
        "tool_name": "explain_vendor_balance",
        "parameters": {
            "company_id": request.company_id,
            "vendor_id": vendor_id,
            "as_of_date": request.as_of_date.isoformat(),
        },
        "planner": "deterministic",
    }

    try:
        from openai import OpenAI

        client = OpenAI(max_retries=0, timeout=8.0)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": request.question,
                            "company_id": request.company_id,
                            "vendor_id": vendor_id,
                            "as_of_date": request.as_of_date.isoformat(),
                        }
                    ),
                },
            ],
            tools=TOOL_REGISTRY,
            tool_choice={"type": "function", "function": {"name": "explain_vendor_balance"}},
        )
        tool_calls = response.choices[0].message.tool_calls or []
        if not tool_calls:
            return fallback

        tool_call = tool_calls[0]
        return {
            "tool_name": tool_call.function.name,
            "parameters": json.loads(tool_call.function.arguments),
            "planner": "openai",
        }
    except Exception:
        return fallback


def execute_planned_tool(db: Session, user_id: int, plan: dict[str, Any]) -> CopilotAnswer:
    if plan["tool_name"] != "explain_vendor_balance":
        raise ValueError(f"Unsupported tool: {plan['tool_name']}")

    params = plan["parameters"]
    as_of_date = params["as_of_date"]
    if isinstance(as_of_date, str):
        as_of_date = date.fromisoformat(as_of_date)

    return explain_vendor_balance(
        db=db,
        user_id=user_id,
        company_id=int(params["company_id"]),
        vendor_id=int(params["vendor_id"]),
        as_of_date=as_of_date,
    )


def get_ai_status() -> dict[str, Any]:
    sdk_available = True
    try:
        import openai
    except Exception:
        sdk_available = False
        openai = None

    return {
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "openai_sdk_available": sdk_available,
        "openai_sdk_version": getattr(openai, "__version__", None) if openai else None,
        "planner_fallback": "deterministic",
    }
