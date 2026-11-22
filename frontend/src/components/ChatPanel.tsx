import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Button, Card, Textarea } from "./ui";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type ChatPanelProps = {
  title: string;
  placeholder: string;
  storageKey: string;
  send: (messages: ChatMessage[]) => Promise<{ reply: string; source: string }>;
  disclaimer?: string;
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

export default function ChatPanel({ title, placeholder, storageKey, send, disclaimer }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(storageKey));
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  // Session storage only: history is never sent to or loaded from the server.
  useEffect(() => {
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

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-manrope text-base font-semibold text-ink">{title}</h3>
        <Button variant="ghost" onClick={handleClear} disabled={messages.length === 0 && !loading}>
          Clear chat
        </Button>
      </div>

      <div ref={listRef} className="max-h-72 space-y-3 overflow-y-auto rounded-md border border-line p-3">
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
