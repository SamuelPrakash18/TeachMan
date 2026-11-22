import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { apiFetch, money } from "../../lib/api";
import { Card, Button, Field, Input, Select, Empty, Skeleton, Stat, useToast } from "../../components/ui";

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

type CashSnapshot = {
  opening_cash_paise: number;
  as_of_date: string;
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Forecast() {
  const { toast } = useToast();
  const [days, setDays] = useState("30");
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [openingCash, setOpeningCash] = useState("");
  const [asOf, setAsOf] = useState("");
  const [savingCash, setSavingCash] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setForecast(null);
    apiFetch<Forecast>(`/api/forecast?days=${days}`)
      .then((f) => {
        if (!cancelled) setForecast(f);
      })
      .catch((e) => {
        if (!cancelled) toast(errMsg(e), "error");
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, reloadKey]);

  useEffect(() => {
    apiFetch<CashSnapshot>("/api/forecast/cash-snapshot")
      .then((s) => {
        setOpeningCash((s.opening_cash_paise / 100).toString());
        setAsOf(s.as_of_date);
      })
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function saveSnapshot(e: React.FormEvent) {
    e.preventDefault();
    setSavingCash(true);
    try {
      await apiFetch("/api/forecast/cash-snapshot", {
        method: "PUT",
        body: {
          opening_cash_paise: Math.round(Number(openingCash) * 100),
          as_of_date: asOf,
        },
      });
      toast("Cash snapshot saved", "success");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSavingCash(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-manrope text-2xl font-bold">Cash forecast</h1>
        <div className="w-40">
          <Field label="Horizon">
            <Select value={days} onChange={(e) => setDays(e.target.value)}>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
            </Select>
          </Field>
        </div>
      </div>

      <p className="text-sm text-slate-600">
        All figures below are estimates based on the assumptions listed. They are not guaranteed.
      </p>

      {forecast === null ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
            <Card>
              <Stat label="Actual cash (today)" value={money(forecast.actual_cash_paise)} />
            </Card>
            <Card>
              <Stat label="Expected collections (estimate)" value={money(forecast.expected_collections_paise)} />
            </Card>
            <Card>
              <Stat label="Expected expenses (estimate)" value={money(forecast.expected_expenses_paise)} />
            </Card>
            <Card>
              <Stat
                label="Projected closing (estimate)"
                value={money(forecast.projected_closing_paise)}
                tone={forecast.projected_closing_paise < 0 ? "danger" : undefined}
              />
            </Card>
            <Card>
              <Stat
                label={`Lowest closing (estimate)${forecast.lowest_closing_date ? ` on ${forecast.lowest_closing_date}` : ""}`}
                value={money(forecast.lowest_closing_paise)}
                tone={forecast.lowest_closing_paise < 0 ? "danger" : undefined}
              />
            </Card>
            <Card>
              <Stat label="Shortage date (estimate)" value={forecast.shortage_date ?? "None projected"} />
            </Card>
          </div>

          <Card>
            <h2 className="font-manrope mb-3 text-lg font-semibold">Projected daily closing cash (estimate)</h2>
            {forecast.daily.length === 0 ? (
              <Empty>No forecast days to show.</Empty>
            ) : (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={forecast.daily}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(v) => money(Number(v))} />
                    <Area type="monotone" dataKey="closing_paise" name="Closing cash" stroke="#4f46e5" fill="#c7d2fe" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card>
            <h2 className="font-manrope mb-3 text-lg font-semibold">Daily breakdown (estimate)</h2>
            {forecast.daily.length === 0 ? (
              <Empty>No rows.</Empty>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 pr-4">Date</th>
                      <th className="py-2 pr-4">Collections</th>
                      <th className="py-2 pr-4">Expenses</th>
                      <th className="py-2 pr-4">Closing</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecast.daily.map((d) => (
                      <tr key={d.date} className="border-b">
                        <td className="py-2 pr-4">{d.date}</td>
                        <td className="py-2 pr-4">{money(d.expected_collections_paise)}</td>
                        <td className="py-2 pr-4">{money(d.expected_expenses_paise)}</td>
                        <td className={`py-2 pr-4 ${d.closing_paise < 0 ? "text-red-600" : ""}`}>
                          {money(d.closing_paise)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card>
            <h2 className="font-manrope mb-3 text-lg font-semibold">Assumptions</h2>
            {forecast.assumptions.length === 0 ? (
              <Empty>No assumptions recorded.</Empty>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {forecast.assumptions.map((a, idx) => (
                  <li key={idx}>{a}</li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Cash snapshot</h2>
        <form onSubmit={saveSnapshot} className="grid gap-3 sm:grid-cols-3 sm:items-end">
          <Field label="Opening cash (Rs)">
            <Input
              type="number"
              step="0.01"
              required
              value={openingCash}
              onChange={(e) => setOpeningCash(e.target.value)}
            />
          </Field>
          <Field label="As of date">
            <Input type="date" required value={asOf} onChange={(e) => setAsOf(e.target.value)} />
          </Field>
          <Button type="submit" disabled={savingCash}>
            {savingCash ? "Saving..." : "Save snapshot"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
