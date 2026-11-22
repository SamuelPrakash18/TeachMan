import { useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Button, Textarea, Badge, Skeleton, useToast } from "../../components/ui";
import ChatPanel, { type ChatMessage } from "../../components/ChatPanel";

type AssistantAnswer = { answer: string; source: string };
type ExplanationAnswer = { text: string; source: string };

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

function sendAnalyticsChat(messages: ChatMessage[]) {
  return apiFetch<{ reply: string; source: string }>("/ai/analytics-chat", {
    method: "POST",
    body: { messages },
  });
}

export default function Assistant() {
  const { toast } = useToast();
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState<ExplanationAnswer | null>(null);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    try {
      const res = await apiFetch<AssistantAnswer>("/api/ai/assistant", {
        method: "POST",
        body: { question: question.trim() },
      });
      setAnswer(res);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setAsking(false);
    }
  }

  async function explainCashFlow() {
    setExplaining(true);
    try {
      const res = await apiFetch<ExplanationAnswer>("/api/ai/cashflow-explanation", { method: "POST" });
      setExplanation(res);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setExplaining(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Assistant</h1>

      <Card>
        <p className="mb-4 rounded-md bg-amber-50 p-3 text-sm text-amber-900">
          The AI assistant explains and drafts text only. It never changes any figures in the app.
        </p>
        <form onSubmit={ask} className="space-y-3">
          <Textarea
            rows={3}
            placeholder="Ask a question about your fees, invoices or cash flow"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={asking || !question.trim()}>
              {asking ? "Thinking..." : "Ask"}
            </Button>
          </div>
        </form>

        {asking && <Skeleton className="mt-4 h-16" />}
        {answer && !asking && (
          <div className="mt-4 space-y-2 rounded-md border p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-manrope font-semibold">Answer</h2>
              <Badge>{answer.source}</Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm">{answer.answer}</p>
          </div>
        )}
      </Card>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-manrope text-lg font-semibold">Cash flow explanation</h2>
            <p className="text-sm text-slate-600">Get a plain-language summary of the current forecast.</p>
          </div>
          <Button onClick={explainCashFlow} disabled={explaining}>
            {explaining ? "Explaining..." : "Explain cash flow"}
          </Button>
        </div>
        {explaining && <Skeleton className="mt-4 h-16" />}
        {explanation && !explaining && (
          <div className="mt-4 space-y-2 rounded-md border p-4">
            <div className="flex items-center justify-between">
              <h3 className="font-manrope font-semibold">Explanation</h3>
              <Badge>{explanation.source}</Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm">{explanation.text}</p>
          </div>
        )}
      </Card>

      <ChatPanel
        title="Analytics chat"
        placeholder="Ask about your collections, overdue invoices, expenses or cash flow..."
        storageKey="teachman_analytics_chat"
        disclaimer="Answers are generated from your TeachMan records. The AI does not change any figures; check important numbers on the Dashboard or Forecast pages."
        send={sendAnalyticsChat}
      />
    </div>
  );
}
