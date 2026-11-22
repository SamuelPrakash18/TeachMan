import { useCallback, useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import type { Expense } from "../../lib/types";
import { Card, Button, Field, Input, Select, Textarea, Badge, Empty, Skeleton, useToast } from "../../components/ui";

const CATEGORIES = ["rent", "electricity", "internet", "salary", "materials", "transport", "other"];

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");
const todayIso = () => new Date().toISOString().slice(0, 10);

export default function Expenses() {
  const { toast } = useToast();
  const [expenses, setExpenses] = useState<Expense[] | null>(null);
  const [status, setStatus] = useState("all");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("other");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState(todayIso());
  const [recurring, setRecurring] = useState(false);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (status !== "all") params.set("status", status);
    if (overdueOnly) params.set("overdue", "true");
    const qs = params.toString();
    try {
      setExpenses(await apiFetch<Expense[]>(`/api/expenses${qs ? `?${qs}` : ""}`));
    } catch (e) {
      setExpenses([]);
      toast(errMsg(e), "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, overdueOnly]);

  useEffect(() => {
    setExpenses(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load, reloadKey]);

  async function addExpense(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/expenses", {
        method: "POST",
        body: {
          title,
          category,
          amount_paise: Math.round(Number(amount) * 100),
          due_date: dueDate,
          is_recurring: recurring,
          notes,
        },
      });
      toast("Expense added", "success");
      setTitle("");
      setAmount("");
      setNotes("");
      setRecurring(false);
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSaving(false);
    }
  }

  async function markPaid(id: string) {
    setBusyId(id);
    try {
      await apiFetch(`/api/expenses/${id}/mark-paid`, { method: "POST", body: { paid_on: todayIso() } });
      toast("Marked as paid", "success");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  async function removeExpense(id: string) {
    if (!window.confirm("Delete this unpaid expense?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/api/expenses/${id}`, { method: "DELETE" });
      toast("Expense deleted", "success");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Expenses</h1>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Add expense</h2>
        <form onSubmit={addExpense} className="grid gap-3 sm:grid-cols-2">
          <Field label="Title">
            <Input required value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Category">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Amount (Rs)">
            <Input type="number" min="0" step="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} />
          </Field>
          <Field label="Due date">
            <Input type="date" required value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={recurring} onChange={(e) => setRecurring(e.target.checked)} />
            Recurring monthly
          </label>
          <Field label="Notes">
            <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </Field>
          <div className="sm:col-span-2 flex justify-end">
            <Button type="submit" disabled={saving}>
              {saving ? "Adding..." : "Add expense"}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <div className="mb-4 grid gap-3 sm:grid-cols-2 sm:items-end">
          <Field label="Status">
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All</option>
              <option value="unpaid">Unpaid</option>
              <option value="paid">Paid</option>
            </Select>
          </Field>
          <label className="flex items-center gap-2 pb-2 text-sm">
            <input type="checkbox" checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} />
            Overdue only
          </label>
        </div>

        {expenses === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : expenses.length === 0 ? (
          <Empty>No expenses match these filters.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Title</th>
                  <th className="py-2 pr-4">Category</th>
                  <th className="py-2 pr-4">Amount</th>
                  <th className="py-2 pr-4">Due</th>
                  <th className="py-2 pr-4">Paid on</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((x) => (
                  <tr key={String(x.id)} className="border-b">
                    <td className="py-2 pr-4 font-medium">{x.title}</td>
                    <td className="py-2 pr-4 capitalize">{x.category}</td>
                    <td className="py-2 pr-4">{money(x.amount_paise)}</td>
                    <td className="py-2 pr-4">{x.due_date}</td>
                    <td className="py-2 pr-4">{x.paid_on ?? "-"}</td>
                    <td className="py-2 pr-4">
                      <Badge>{x.status}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-wrap gap-2">
                        {x.status !== "paid" && (
                          <>
                            <Button disabled={busyId === x.id} onClick={() => markPaid(x.id)}>
                              Mark paid
                            </Button>
                            <Button variant="danger" disabled={busyId === x.id} onClick={() => removeExpense(x.id)}>
                              Delete
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
