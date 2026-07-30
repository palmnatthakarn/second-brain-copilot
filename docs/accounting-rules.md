# Accounting Rules

## AP Balance

Accounts payable is normally a credit-balance account.

```text
closing_balance = opening_balance + credit - debit
```

Opening balance is separated from current-period movement by document type or ledger memo. In production this should be controlled by fiscal period metadata.

## Date Rules

- Document date is the business document date.
- Posting date is the accounting recognition date.
- The balance calculation uses posting date.
- The UI still displays document date because users reconcile from source documents.

## Reversal Rules

If a document has `status = reversed`, `reversal_document_no`, or another document references it, the answer must include a warning and show both original and reversal evidence when available.

## Hallucination Guardrail

The copilot may not invent numbers, documents, or explanations. If tool output is incomplete, the response must warn that the result cannot be concluded reliably.
