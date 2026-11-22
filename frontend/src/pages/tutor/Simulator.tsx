import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { apiFetch, money } from "../../lib/api";
import type { Invoice } from "../../lib/types";
import { Card, Button, Field, Input, Select, Empty, Skeleton, Stat, useToast } from "../../components/ui";

type Scenario = {
  projected_closing_paise: number;
  lowest_closing_paise: number;
  lowest_closing_date: string | null;
  shortage_date: string | null;
};

type SimulationResult = {
  original: Scenario;
  simulated: Scenario;
  comparison: { closing_difference_paise?: number; [key: string]: unknown };
  recommendations: string[];
  daily_original: { date: string; closing_paise: number }[];
  daily_simulated: { date: string; closing_paise: number }[];
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Simulator() {
  const { toast } = useToast();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [invoiceId, setInvoiceId] = useState("");
  const [delayDays, setDelayDays] = useState("30");
  const [days, setDays] = useState("30");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);

  useEffect(() => {
    apiFetch<Invoice[]>("/api/invoices")
      .then((rows) => setInvoices(rows.filter((i) => i.outstanding_paise > 0)))
      .catch((e) => {
        setInvoices([]);
        toast(errMsg(e), "error");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runSimulation(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    try {
      const res = await apiFetch<SimulationResult>("/api/forecast/simulate", {
        method: "POST",
        body: {
          invoice_id: invoiceId,
          delay_days: Number(delayDays),
          days: Number(days),
        },
      });
      setResult(res);
      toast("Simulation complete", "success");
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setRunning(false);
    }
  }

  function reset() {
    setResult(null);
  }

  const chartData = result
    ? result.daily_original.map((d, idx) => ({
        date: d.date,
        original: d.closing_paise,
        simulated: result.daily_simulated[idx]?.closing_paise ?? null,
      }))
    : [];

  const difference = result ? result.simulated.projected_closing_paise - result.original.projected_closing_paise : 0;

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Payment delay simulator</h1>
      <p className="text-sm text-slate-600">
        This is a what-if scenario. It estimates the effect of late payment and saves nothing.
      </p>

      <Card>
        <form onSubmit={runSimulation} className="grid gap-3 sm:grid-cols-4 sm:items-end">
          <Field label="Outstanding invoice">
            <Select required value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)}>
              <option value="">Select an invoice</option>
              {(invoices ?? []).map((inv) => (
                <option key={String(inv.id)} value={String(inv.id)}>
                  {inv.invoice_number} · {money(inv.outstanding_paise)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Delay (days)">
            <Input
              type="number"
              min={0}
              max={180}
              required
              value={delayDays}
              onChange={(e) => setDelayDays(e.target.value)}
            />
          </Field>
          <Field label="Horizon">
            <Select value={days} onChange={(e) => setDays(e.target.value)}>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
            </Select>
          </Field>
          <div className="flex gap-2">
            <Button type="submit" disabled={running || !invoiceId}>
              {running ? "Running..." : "Run simulation"}
            </Button>
            <Button variant="secondary" type="button" onClick={reset} disabled={!result}>
              Reset
            </Button>
          </div>
        </form>
        {invoices === null && <Skeleton className="mt-3 h-8" />}
        {invoices !== null && invoices.length === 0 && (
          <p className="mt-3 text-sm text-slate-600">No invoices have an outstanding balance.</p>
        )}
      </Card>

      {result && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Card>
              <Stat label="Original projected closing" value={money(result.original.projected_closing_paise)} />
            </Card>
            <Card>
              <Stat label="Simulated projected closing" value={money(result.simulated.projected_closing_paise)} />
            </Card>
            <Card>
              <Stat
                label="Difference"
                value={money(difference)}
                tone={difference < 0 ? "danger" : undefined}
              />
            </Card>
            <Card>
              <Stat label="Simulated shortage date" value={result.simulated.shortage_date ?? "None projected"} />
            </Card>
            <Card>
              <Stat label="Original lowest closing" value={money(result.original.lowest_closing_paise)} />
            </Card>
            <Card>
              <Stat label="Simulated lowest closing" value={money(result.simulated.lowest_closing_paise)} />
            </Card>
            <Card>
              <Stat label="Original shortage date" value={result.original.shortage_date ?? "None projected"} />
            </Card>
            <Card>
              <Stat
                label="Simulated lowest closing date"
                value={result.simulated.lowest_closing_date ?? "-"}
              />
            </Card>
          </div>

          <Card>
            <h2 className="font-manrope mb-3 text-lg font-semibold">Closing cash: original vs simulated</h2>
            {chartData.length === 0 ? (
              <Empty>No daily data returned.</Empty>
            ) : (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(v) => money(Number(v))} />
                    <Legend />
                    <Line type="monotone" dataKey="original" name="Original" stroke="#4f46e5" dot={false} />
                    <Line type="monotone" dataKey="simulated" name="Simulated" stroke="#dc2626" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card>
            <h2 className="font-manrope mb-3 text-lg font-semibold">Recommendations</h2>
            {result.recommendations.length === 0 ? (
              <Empty>No recommendations for this scenario.</Empty>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {result.recommendations.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
