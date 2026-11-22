import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { Button, Card, Textarea } from "./ui";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type ChatPanelProps = {
  title: string;
  placeholder: string;
  storageKey: string;
  send: (messages: ChatMessage[]) => Promise<{ reply: string; source: string }>;
  disclaimer?: string;
  fill?: boolean;
};

const MAX_SENT_MESSAGES = 20;

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== "object") {
    return false;
  }
  const v = value as Record<string, unknown>;
  return (v.role === "user" || v.role === "assistant") && typeof v.content === "string";
}

function loadMessages(storageKey: string): ChatMessage[] {
  // An empty key means in-memory only: never read from sessionStorage.
  if (!storageKey) {
    return [];
  }
  try {
    const raw = sessionStorage.getItem(storageKey);
    if (!raw) {
      return [];
    }
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isChatMessage);
  } catch {
    return [];
  }
}

export default function ChatPanel({
  title,
  placeholder,
  storageKey,
  send,
  disclaimer,
  fill = false,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(storageKey));
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Grow the fill-mode input with its content, up to 160px.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) {
      return;
    }
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  // Session storage only: history is never sent to or loaded from the server.
  useEffect(() => {
    // An empty key means in-memory only: never write to sessionStorage.
    if (!storageKey) {
      return;
    }
    try {
      if (messages.length === 0) {
        sessionStorage.removeItem(storageKey);
      } else {
        sessionStorage.setItem(storageKey, JSON.stringify(messages));
      }
    } catch {
      // Storage may be unavailable (private mode or quota); the chat still works in memory.
    }
  }, [messages, storageKey]);

  // Keep the newest message in view.
  useEffect(() => {
    const list = listRef.current;
    if (list) {
      list.scrollTop = list.scrollHeight;
    }
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) {
      return;
    }
    const next: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const res = await send(next.slice(-MAX_SENT_MESSAGES));
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Something went wrong";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, that did not work: " + detail },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  function handleClear() {
    setMessages([]);
    setInput("");
  }

  if (fill) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <div className="flex items-center justify-between gap-2 border-b border-line px-1 pb-2">
          <h3 className="font-manrope text-base font-semibold text-ink">{title}</h3>
          <Button variant="ghost" onClick={handleClear} disabled={messages.length === 0 && !loading}>
            Clear chat
          </Button>
        </div>

        <div ref={listRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 py-3">
          {messages.length === 0 && !loading && (
            <p className="text-sm text-muted">Ask a question to get started.</p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "ml-auto max-w-[85%] rounded-2xl bg-brand-green text-white px-4 py-2"
                  : "mr-auto max-w-[85%] rounded-2xl bg-white border border-line text-ink px-4 py-2"
              }
            >
              <span className="sr-only">{m.role === "user" ? "You" : "Assistant"}</span>
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          ))}
          {loading && (
            <p role="status" className="text-sm text-muted">
              Thinking...
            </p>
          )}
        </div>

        <div className="flex items-end gap-2 border-t border-line pt-3">
          <textarea
            ref={textareaRef}
            rows={1}
            aria-label={title}
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="max-h-40 min-h-[44px] flex-1 resize-none rounded-xl border border-line px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue"
          />
          <button
            type="button"
            aria-label="Send message"
            onClick={() => void handleSend()}
            disabled={loading || !input.trim()}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-green text-white disabled:opacity-40"
          >
            <Send className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {disclaimer && <p className="mt-2 text-center text-xs text-muted">{disclaimer}</p>}
      </div>
    );
  }

  return (
    <Card className={fill ? "flex h-full flex-col border-0 shadow-none" : undefined}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-manrope text-base font-semibold text-ink">{title}</h3>
        <Button variant="ghost" onClick={handleClear} disabled={messages.length === 0 && !loading}>
          Clear chat
        </Button>
      </div>

      <div
        ref={listRef}
        className={`${fill ? "min-h-0 flex-1" : "max-h-72"} space-y-3 overflow-y-auto rounded-md border border-line p-3`}
      >
        {messages.length === 0 && !loading && (
          <p className="text-sm text-muted">Ask a question to get started.</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-lg p-3 text-sm ${
              m.role === "user" ? "ml-auto bg-brand-green/10 text-ink" : "mr-auto bg-brand-cream text-ink"
            }`}
          >
            <p className="mb-1 text-xs font-semibold text-muted">
              {m.role === "user" ? "You" : "Assistant"}
            </p>
            <p className="whitespace-pre-wrap">{m.content}</p>
          </div>
        ))}
        {loading && (
          <p role="status" className="text-sm text-muted">
            Thinking...
          </p>
        )}
      </div>

      <div className="mt-3 space-y-2">
        <Textarea
          rows={2}
          aria-label={title}
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="flex justify-end">
          <Button variant="primary" onClick={() => void handleSend()} disabled={loading || !input.trim()}>
            Send
          </Button>
        </div>
      </div>

      {disclaimer && <p className="mt-3 text-xs text-muted">{disclaimer}</p>}
    </Card>
  );
}
