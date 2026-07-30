"use client";

import { useState } from "react";
import { AlertTriangle, Calculator, Download, Search, Send } from "lucide-react";

import { askCopilot, exportVendorBalance, type CopilotAnswer } from "@/lib/api";

const money = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function CopilotWorkspace() {
  const [question, setQuestion] = useState("What is this vendor balance and which documents make it up?");
  const [vendorQuery, setVendorQuery] = useState("ABC");
  const [asOfDate, setAsOfDate] = useState("2025-12-31");
  const [answer, setAnswer] = useState<CopilotAnswer | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError("");
    try {
      setAnswer(await askCopilot(question, vendorQuery, asOfDate));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function downloadExport() {
    setError("");
    try {
      const blob = await exportVendorBalance(question, vendorQuery, asOfDate);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `vendor-balance-${vendorQuery}-${asOfDate}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  const chartData = answer
    ? [
        { name: "Opening", value: answer.calculation.opening_balance },
        { name: "Debit", value: answer.calculation.debit },
        { name: "Credit", value: answer.calculation.credit },
        { name: "Closing", value: answer.calculation.closing_balance },
      ]
    : [];

  return (
    <main className="min-h-screen">
      <div className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold">AI AP & GL Copilot</h1>
            <p className="text-sm text-slate-600">Read-only AP balance explanation with document traceability.</p>
          </div>
          <a
            className="inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium"
            href="http://localhost:8000/docs"
          >
            <Search size={16} /> API
          </a>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <section className="rounded-md border border-line bg-white p-4">
          <label className="text-sm font-medium" htmlFor="vendor">
            Vendor
          </label>
          <input
            id="vendor"
            className="mt-2 h-10 w-full rounded-md border border-line px-3"
            value={vendorQuery}
            onChange={(event) => setVendorQuery(event.target.value)}
          />

          <label className="mt-4 block text-sm font-medium" htmlFor="date">
            As of date
          </label>
          <input
            id="date"
            type="date"
            className="mt-2 h-10 w-full rounded-md border border-line px-3"
            value={asOfDate}
            onChange={(event) => setAsOfDate(event.target.value)}
          />

          <label className="mt-4 block text-sm font-medium" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            className="mt-2 min-h-28 w-full resize-none rounded-md border border-line p-3"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />

          <button
            className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60"
            onClick={submit}
            disabled={loading}
          >
            <Send size={16} /> {loading ? "Analyzing" : "Ask Copilot"}
          </button>
          {error ? <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        </section>

        <section className="space-y-5">
          {answer ? (
            <>
              <div className="rounded-md border border-line bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm text-slate-600">{answer.vendor_name} · {answer.vendor_code}</p>
                    <h2 className="mt-1 text-2xl font-semibold">{money.format(answer.calculation.closing_balance)}</h2>
                    <p className="mt-2 text-sm text-slate-700">{answer.answer}</p>
                  </div>
                  <button
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium"
                    onClick={downloadExport}
                  >
                    <Download size={16} /> Export
                  </button>
                </div>
              </div>

              <div className="grid gap-5 xl:grid-cols-2">
                <div className="rounded-md border border-line bg-white p-5">
                  <h3 className="flex items-center gap-2 text-sm font-semibold"><Calculator size={16} /> Calculation</h3>
                  <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    {Object.entries(answer.calculation).filter(([key]) => key !== "formula").map(([key, value]) => (
                      <div key={key} className="border-b border-line pb-2">
                        <dt className="capitalize text-slate-500">{key.replace("_", " ")}</dt>
                        <dd className="font-semibold">{money.format(Number(value))}</dd>
                      </div>
                    ))}
                  </dl>
                  <p className="mt-3 text-xs text-slate-600">{answer.calculation.formula}</p>
                </div>

                <div className="rounded-md border border-line bg-white p-5">
                  <h3 className="text-sm font-semibold">Movement Chart</h3>
                  <div className="mt-5 space-y-4">
                    {chartData.map((item) => {
                      const max = Math.max(...chartData.map((entry) => Math.abs(entry.value)), 1);
                      const width = `${Math.max(8, (Math.abs(item.value) / max) * 100)}%`;
                      return (
                        <div key={item.name} className="grid grid-cols-[72px_1fr_96px] items-center gap-3 text-sm">
                          <span className="text-slate-600">{item.name}</span>
                          <div className="h-8 rounded bg-slate-100">
                            <div className="h-8 rounded bg-accent" style={{ width }} />
                          </div>
                          <span className="text-right font-medium">{money.format(item.value)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {answer.warnings.length ? (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  <h3 className="flex items-center gap-2 font-semibold"><AlertTriangle size={16} /> Warnings</h3>
                  <ul className="mt-2 list-disc pl-5">
                    {answer.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                </div>
              ) : null}

              <div id="documents" className="overflow-hidden rounded-md border border-line bg-white">
                <table className="w-full min-w-[760px] border-collapse text-sm">
                  <thead className="bg-panel text-left">
                    <tr>
                      <th className="p-3">Document</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Document Date</th>
                      <th className="p-3">Posting Date</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Debit</th>
                      <th className="p-3 text-right">Credit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {answer.documents.map((document) => (
                      <tr key={`${document.document_no}-${document.posting_date}`} className="border-t border-line">
                        <td className="p-3 font-medium">{document.document_no}</td>
                        <td className="p-3">{document.document_type}</td>
                        <td className="p-3">{document.document_date}</td>
                        <td className="p-3">{document.posting_date}</td>
                        <td className="p-3">{document.status}</td>
                        <td className="p-3 text-right">{money.format(document.debit)}</td>
                        <td className="p-3 text-right">{money.format(document.credit)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="rounded-md border border-line bg-white p-8 text-center text-slate-600">
              Ask about vendor ABC as of 2025-12-31 to load the seeded AP trace.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
