import { useEffect, useState } from "react";
import { MessageSquare, X } from "lucide-react";
import { apiFetch } from "../lib/api";
import ChatPanel, { type ChatMessage } from "./ChatPanel";

// Tutor-only analytics assistant. Messages live in React state only and are never stored.
export default function AnalyticsChatBubble() {
  const [open, setOpen] = useState(false);

  // Escape closes the panel while it is open.
  useEffect(() => {
    if (!open) {
      return;
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  function send(messages: ChatMessage[]) {
    return apiFetch<{ reply: string; source: string }>("/ai/analytics-chat", {
      method: "POST",
      body: { messages },
    });
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-4 z-50 flex h-[min(520px,70vh)] w-[min(380px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-line bg-white shadow-lg">
          <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
            <h2 className="font-manrope text-base font-semibold text-ink">Analytics chat</h2>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close analytics chat"
              className="rounded-md p-1 text-muted hover:bg-brand-cream"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
          <div className="flex min-h-0 flex-1 flex-col p-3">
            <ChatPanel
              title="Analytics chat"
              placeholder="Ask about dues, overdue invoices, collections, expenses or cash flow..."
              storageKey=""
              disclaimer="Answers come from your TeachMan records. The AI does not change any figures. Chat is not saved and clears when you reload."
              send={send}
              fill
            />
          </div>
        </div>
      )}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Open analytics chat"
        aria-expanded={open}
        className="fixed bottom-4 right-4 z-40 inline-flex items-center gap-2 rounded-full bg-brand-green px-4 py-3 text-sm font-semibold text-white shadow-lg hover:opacity-90"
      >
        <MessageSquare className="h-5 w-5" aria-hidden="true" />
        Analytics
      </button>
    </>
  );
}
