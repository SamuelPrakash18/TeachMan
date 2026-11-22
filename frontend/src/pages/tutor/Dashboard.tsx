import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { apiFetch, money } from "../../lib/api";
import type { Invoice } from "../../lib/types";
import { Card, Button, StatusBadge, Empty, Skeleton, Stat, Modal, useToast } from "../../components/ui";

type ForecastDay = {
  date: string;
  expected_collections_paise: number;
  expected_expenses_paise: number;
  closing_paise: number;
};

type Forecast = {
  actual_cash_paise: number;
  expected_collections_paise: number;
  expected_expenses_paise: number;
  projected_closing_paise: number;
  lowest_closing_paise: number;
  lowest_closing_date: string | null;
  shortage_date: string | null;
  daily: ForecastDay[];
  assumptions: string[];
};

type InvoiceRow = Invoice & { student_name?: string; days_overdue?: number };

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Dashboard() {
  const { toast } = useToast();
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [invoices, setInvoices] = useState<InvoiceRow[] | null>(null);
  const [reminder, setReminder] = useState<{ student: string; text: string } | null>(null);
  const [drafting, setDrafting] = useState<InvoiceRow["id"] | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [f, inv] = await Promise.all([
          apiFetch<Forecast>("/api/forecast?days=30"),
          apiFetch<InvoiceRow[]>("/api/invoices"),
        ]);
        if (!cancelled) {
          setForecast(f);
          setInvoices(inv);
        }
      } catch (e) {
        if (!cancelled) toast(errMsg(e), "error");
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function draftReminder(inv: InvoiceRow) {
    setDrafting(inv.id);
    try {
      const res = await apiFetch<{ text: string }>("/api/ai/reminder", {
        method: "POST",
        body: { invoice_id: inv.id, tone: "friendly" },
      });
      setReminder({ student: inv.student_name ?? inv.invoice_number, text: res.text });
    } catch (e) {
      toast(errMsg(e), "error");
    } finally {
      setDrafting(null);
    }
  }

  function copyText(text: string) {
    navigator.clipboard.writeText(text).then(
      () => toast("Copied to clipboard", "success"),
      () => toast("Could not copy", "error"),
    );
  }

  if (!forecast || !invoices) {
    return (
      <div className="space-y-6">
        <h1 className="font-manrope text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const outstandingTotal = invoices.reduce((s, i) => s + i.outstanding_paise, 0);
  const overdue = invoices.filter((i) => i.status === "overdue");
  const overdueTotal = overdue.reduce((s, i) => s + i.outstanding_paise, 0);

  const actions: string[] = [];
  if (forecast.shortage_date) {
    actions.push(
      `Cash is projected to fall below zero on ${forecast.shortage_date}. Chase payments or defer expenses before then.`,
    );
  }
  if (overdue.length > 0) {
    actions.push(`${overdue.length} invoice(s) are overdue. Send reminders to recover ${money(overdueTotal)}.`);
  }
  if (forecast.expected_expenses_paise > forecast.expected_collections_paise) {
    actions.push("Expected expenses over the next 30 days are higher than expected collections.");
  }
  if (outstandingTotal > 0 && overdue.length === 0) {
    actions.push(`${money(outstandingTotal)} is outstanding and nothing is overdue yet. Follow up on invoices due soon.`);
  }
  if (actions.length === 0) {
    actions.push("No cash risks detected in the next 30 days.");
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Dashboard</h1>

      {forecast.shortage_date && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          Cash shortage expected on <strong>{forecast.shortage_date}</strong>. Review the action list below.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <Card>
          <Stat label="Outstanding total" value={money(outstandingTotal)} />
        </Card>
        <Card>
          <Stat label="Overdue invoices" value={String(overdue.length)} />
        </Card>
        <Card>
          <Stat label="Expected collections (30 days, estimate)" value={money(forecast.expected_collections_paise)} />
        </Card>
        <Card>
          <Stat label="Expected expenses (30 days, estimate)" value={money(forecast.expected_expenses_paise)} />
        </Card>
        <Card>
          <Stat
            label="Projected closing (estimate)"
            value={money(forecast.projected_closing_paise)}
            tone={forecast.projected_closing_paise < 0 ? "danger" : undefined}
          />
        </Card>
        <Card>
          <Stat label="Actual cash on hand" value={money(forecast.actual_cash_paise)} />
        </Card>
      </div>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Action list</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {actions.map((a, idx) => (
            <li key={idx}>{a}</li>
          ))}
        </ul>
      </Card>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Projected daily closing cash</h2>
        {forecast.daily.length === 0 ? (
          <Empty>No forecast data yet.</Empty>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecast.daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(v) => money(Number(v))} />
                <Legend />
                <Line type="monotone" dataKey="closing_paise" name="Closing cash" stroke="#4f46e5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Overdue invoices</h2>
        {overdue.length === 0 ? (
          <Empty>No overdue invoices.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Student</th>
                  <th className="py-2 pr-4">Invoice</th>
                  <th className="py-2 pr-4">Outstanding</th>
                  <th className="py-2 pr-4">Due date</th>
                  <th className="py-2 pr-4">Days overdue</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {overdue.map((inv) => (
                  <tr key={String(inv.id)} className="border-b">
                    <td className="py-2 pr-4">{inv.student_name ?? "-"}</td>
                    <td className="py-2 pr-4">{inv.invoice_number}</td>
                    <td className="py-2 pr-4">{money(inv.outstanding_paise)}</td>
                    <td className="py-2 pr-4">{inv.due_date}</td>
                    <td className="py-2 pr-4">{inv.days_overdue ?? "-"}</td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="py-2 pr-4">
                      <Button
                        variant="secondary"
                        disabled={drafting === inv.id}
                        onClick={() => draftReminder(inv)}
                      >
                        {drafting === inv.id ? "Drafting..." : "Draft reminder"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal open={reminder !== null} onClose={() => setReminder(null)} title={`Reminder for ${reminder?.student ?? ""}`}>
        <div className="space-y-4">
          <p className="whitespace-pre-wrap rounded-md border bg-slate-50 p-3 text-sm">{reminder?.text}</p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setReminder(null)}>
              Close
            </Button>
            <Button onClick={() => reminder && copyText(reminder.text)}>Copy</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
