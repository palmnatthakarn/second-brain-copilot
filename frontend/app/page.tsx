"use client";

import { useState } from "react";
import { CopilotWorkspace } from "@/components/copilot-workspace";
import { KnowledgeWorkspace } from "@/components/knowledge-workspace";

export default function Page() {
  const [workspace, setWorkspace] = useState<"copilot" | "knowledge">("copilot");
  return (
    <>
      <nav className="fixed bottom-5 left-1/2 z-10 flex -translate-x-1/2 gap-1 rounded-md border border-line bg-white p-1 shadow-sm">
        <button className={`rounded px-3 py-2 text-sm ${workspace === "copilot" ? "bg-panel font-semibold" : "text-slate-600"}`} onClick={() => setWorkspace("copilot")}>AP Copilot</button>
        <button className={`rounded px-3 py-2 text-sm ${workspace === "knowledge" ? "bg-panel font-semibold" : "text-slate-600"}`} onClick={() => setWorkspace("knowledge")}>Second Brain</button>
      </nav>
      {workspace === "copilot" ? <CopilotWorkspace /> : <KnowledgeWorkspace />}
    </>
  );
}
