import { useState } from "react";
import { MessageCircle, X } from "lucide-react";
import { apiFetch } from "../lib/api";
import ChatPanel, { type ChatMessage } from "./ChatPanel";

// Public endpoint: works when logged out.
function sendSupportChat(messages: ChatMessage[]) {
  return apiFetch<{ reply: string; source: string }>("/support/chat", {
    method: "POST",
    body: { messages },
  });
}

export default function SupportChat() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && (
        <div className="fixed bottom-20 left-4 z-50 w-[min(360px,calc(100vw-2rem))]">
          <div className="mb-2 flex justify-end">
            <button
              type="button"
              aria-label="Close help chat"
              onClick={() => setOpen(false)}
              className="rounded-md bg-white p-1 text-ink shadow hover:bg-brand-cream"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
          <ChatPanel
            title="TeachMan Help"
            placeholder="Ask how to use TeachMan..."
            storageKey="teachman_support_chat"
            disclaimer="Help answers are general guidance. Never share passwords or OTPs here."
            send={sendSupportChat}
          />
        </div>
      )}

      <button
        type="button"
        aria-label="Open TeachMan help chat"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-4 left-4 z-40 inline-flex items-center gap-2 rounded-full bg-brand-green px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-brand-green/90"
      >
        <MessageCircle className="h-5 w-5" aria-hidden="true" />
        Help
      </button>
    </>
  );
}
