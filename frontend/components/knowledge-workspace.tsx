"use client";

import { useState } from "react";
import { BookOpen, MessageSquare, Plus, RefreshCw, Search, Sparkles } from "lucide-react";

import {
  captureKnowledge,
  chatWithKnowledge,
  hybridSearchKnowledge,
  searchKnowledge,
  syncKnowledge,
  type KnowledgeChatAnswer,
  type KnowledgeSearchResult,
} from "@/lib/api";

type SearchMode = "full-text" | "hybrid";

export function KnowledgeWorkspace() {
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [query, setQuery] = useState("ภาษีซื้อ");
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [question, setQuestion] = useState("ภาษีซื้อสามารถนำไปใช้เมื่อใด?");
  const [chat, setChat] = useState<KnowledgeChatAnswer | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState<"search" | "chat" | "capture" | "sync" | null>(null);

  async function runSearch() {
    setLoading("search"); setError("");
    try {
      const response = mode === "hybrid" ? await hybridSearchKnowledge(query, category) : await searchKnowledge(query, category);
      setResults(response.results);
      setStatus(`${response.results.length} notes found`);
    } catch (err) { setError(err instanceof Error ? err.message : "Search failed"); }
    finally { setLoading(null); }
  }

  async function runChat() {
    setLoading("chat"); setError("");
    try { setChat(await chatWithKnowledge(question, category)); }
    catch (err) { setError(err instanceof Error ? err.message : "Chat failed"); }
    finally { setLoading(null); }
  }

  async function capture() {
    if (!title.trim() || !content.trim()) { setError("Title and content are required."); return; }
    setLoading("capture"); setError("");
    try {
      const response = await captureKnowledge({ title, content, category: category || "Inbox", tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean) });
      setTitle(""); setContent(""); setTags("");
      setStatus(`Saved to ${response.note.path}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Capture failed"); }
    finally { setLoading(null); }
  }

  async function sync() {
    setLoading("sync"); setError("");
    try {
      const response = await syncKnowledge();
      setStatus(`Synced: ${response.created} created, ${response.updated} updated, ${response.deleted} deleted.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Sync failed"); }
    finally { setLoading(null); }
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div><h1 className="text-xl font-semibold">Second Brain</h1><p className="text-sm text-slate-600">Markdown knowledge shared with Obsidian.</p></div>
          <button className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium disabled:opacity-60" onClick={sync} disabled={loading === "sync"}>
            <RefreshCw size={16} className={loading === "sync" ? "animate-spin" : ""} /> {loading === "sync" ? "Syncing" : "Sync Markdown"}
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(330px,0.8fr)]">
        <div className="space-y-5">
          <section className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="flex items-center gap-2 text-base font-semibold"><Search size={17} /> Knowledge search</h2><p className="mt-1 text-sm text-slate-600">Search your local Markdown repository.</p></div><div className="inline-flex rounded-md border border-line p-1"><button className={`rounded px-3 py-1.5 text-sm ${mode === "full-text" ? "bg-panel font-medium" : "text-slate-600"}`} onClick={() => setMode("full-text")}>Full-text</button><button className={`rounded px-3 py-1.5 text-sm ${mode === "hybrid" ? "bg-panel font-medium" : "text-slate-600"}`} onClick={() => setMode("hybrid")}><Sparkles className="mr-1 inline" size={14} /> Hybrid</button></div></div>
            <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_150px_auto]"><input className="h-10 rounded-md border border-line px-3" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && runSearch()} placeholder="Search notes" /><input className="h-10 rounded-md border border-line px-3" value={category} onChange={(event) => setCategory(event.target.value)} placeholder="Category" /><button className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60" onClick={runSearch} disabled={loading === "search"}><Search size={16} /> Search</button></div>
          </section>

          <section className="overflow-hidden rounded-md border border-line bg-white">
            <div className="border-b border-line px-5 py-3 text-sm font-semibold">Results {status ? <span className="ml-2 font-normal text-slate-500">{status}</span> : null}</div>
            {results.length ? <div className="divide-y divide-line">{results.map((note) => <article key={note.id} className="p-5"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="font-semibold">{note.title}</p><p className="mt-1 text-xs text-slate-500">{note.category} · {note.path}</p></div>{note.hybrid_score !== undefined ? <span className="rounded bg-panel px-2 py-1 text-xs font-medium">Score {note.hybrid_score.toFixed(2)}</span> : null}</div><p className="mt-3 text-sm text-slate-700">{note.excerpt}</p>{note.tags.length ? <div className="mt-3 flex flex-wrap gap-2">{note.tags.map((tag) => <span key={tag} className="rounded bg-teal-50 px-2 py-1 text-xs text-teal-800">#{tag}</span>)}</div> : null}</article>)}</div> : <div className="p-8 text-center text-sm text-slate-600">Search your Markdown notes to see matching knowledge here.</div>}
          </section>

          <section className="rounded-md border border-line bg-white p-5"><h2 className="flex items-center gap-2 text-base font-semibold"><MessageSquare size={17} /> Ask your knowledge</h2><div className="mt-4 flex gap-3"><input className="h-10 min-w-0 flex-1 rounded-md border border-line px-3" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => event.key === "Enter" && runChat()} /><button className="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60" onClick={runChat} disabled={loading === "chat"}><MessageSquare size={16} /> Ask</button></div>{chat ? <div className="mt-4 rounded-md bg-panel p-4 text-sm"><p className="whitespace-pre-wrap leading-6">{chat.answer}</p>{chat.sources.length ? <p className="mt-3 text-xs text-slate-600">Sources: {chat.sources.map((source) => source.title).join(", ")}</p> : null}</div> : null}</section>
        </div>

        <aside className="h-fit rounded-md border border-line bg-white p-5"><h2 className="flex items-center gap-2 text-base font-semibold"><Plus size={17} /> Capture knowledge</h2><p className="mt-1 text-sm text-slate-600">Creates a Markdown note in your Obsidian vault.</p><label className="mt-4 block text-sm font-medium">Title</label><input className="mt-2 h-10 w-full rounded-md border border-line px-3" value={title} onChange={(event) => setTitle(event.target.value)} /><label className="mt-4 block text-sm font-medium">Tags</label><input className="mt-2 h-10 w-full rounded-md border border-line px-3" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="accounting, vat" /><label className="mt-4 block text-sm font-medium">Note</label><textarea className="mt-2 min-h-48 w-full resize-y rounded-md border border-line p-3" value={content} onChange={(event) => setContent(event.target.value)} placeholder="Write knowledge to preserve in Markdown..." /><button className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60" onClick={capture} disabled={loading === "capture"}><BookOpen size={16} /> {loading === "capture" ? "Saving" : "Save to knowledge"}</button>{error ? <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}</aside>
      </div>
    </main>
  );
}
