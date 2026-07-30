export type CopilotAnswer = {
  answer: string;
  company_id: number;
  vendor_id: number;
  vendor_code: string;
  vendor_name: string;
  as_of_date: string;
  calculation: {
    opening_balance: number;
    debit: number;
    credit: number;
    closing_balance: number;
    formula: string;
  };
  documents: Array<{
    document_no: string;
    document_type: string;
    document_date: string;
    posting_date: string;
    status: string;
    debit: number;
    credit: number;
    reversal_document_no?: string | null;
  }>;
  warnings: string[];
  sources: string[];
};

export type KnowledgeNote = {
  id: number;
  slug: string;
  path: string;
  title: string;
  category: string;
  tags: string[];
  links: string[];
  frontmatter: Record<string, unknown>;
  excerpt: string;
  content_hash: string;
  embedding_status: string;
  updated_at: string;
};

export type KnowledgeSearchResult = KnowledgeNote & {
  text_score?: number;
  vector_score?: number;
  hybrid_score?: number;
};

export type KnowledgeChatAnswer = {
  answer: string;
  sources: KnowledgeNote[];
  warnings: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? (
  typeof window === "undefined"
    ? "http://localhost:8000/api"
    : `${window.location.protocol}//${window.location.hostname}:8000/api`
);

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail ?? "Request failed");
  }

  return response.json();
}

export async function askCopilot(question: string, vendorQuery: string, asOfDate: string): Promise<CopilotAnswer> {
  const response = await fetch(`${API_BASE}/copilot/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      vendor_query: vendorQuery,
      company_id: 1,
      as_of_date: asOfDate,
      user_id: 1,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }

  return response.json();
}

export async function exportVendorBalance(question: string, vendorQuery: string, asOfDate: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/exports/vendor-balance.csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      vendor_query: vendorQuery,
      company_id: 1,
      as_of_date: asOfDate,
      user_id: 1,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Export failed" }));
    throw new Error(body.detail ?? "Export failed");
  }

  return response.blob();
}

export function syncKnowledge(): Promise<{ created: number; updated: number; deleted: number; unchanged: number }> {
  return request("/knowledge/sync");
}

export function searchKnowledge(query: string, category?: string): Promise<{ query: string; results: KnowledgeNote[] }> {
  return request("/knowledge/search", { query, category: category || null, limit: 12 });
}

export function hybridSearchKnowledge(query: string, category?: string): Promise<{ query: string; results: KnowledgeSearchResult[] }> {
  return request("/knowledge/hybrid-search", { query, category: category || null, limit: 12 });
}

export function captureKnowledge(input: { title: string; content: string; category: string; tags: string[] }): Promise<{ note: KnowledgeNote; wrote_markdown: boolean }> {
  return request("/knowledge/capture", input);
}

export function chatWithKnowledge(question: string, category?: string): Promise<KnowledgeChatAnswer> {
  return request("/knowledge/chat", { question, category: category || null, limit: 6 });
}
