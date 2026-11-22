import { useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import type { Invoice, Student } from "../../lib/types";
import {
  Card,
  Button,
  Field,
  Input,
  Select,
  Textarea,
  Empty,
  Skeleton,
  Modal,
  StatusBadge,
  useToast,
} from "../../components/ui";

type InvoiceItem = {
  description: string;
  quantity: number;
  unit_paise: number;
};

type InvoiceDetail = Invoice & { items: InvoiceItem[] };

type DraftItem = { description: string; quantity: string; unit: string };

const STATUSES = ["all", "issued", "partially_paid", "overdue", "paid", "cancelled"];
const METHODS = ["cash", "upi", "bank", "other"];

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");
const todayIso = () => new Date().toISOString().slice(0, 10);

export default function Invoices() {
  const { toast } = useToast();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [status, setStatus] = useState("all");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [q, setQ] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const [selected, setSelected] = useState<InvoiceDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("cash");
  const [payRef, setPayRef] = useState("");
  const [payDate, setPayDate] = useState(todayIso());
  const [busy, setBusy] = useState(false);

  const [createOpen, setCreateOpen] = useState(false);
  const [students, setStudents] = useState<Student[]>([]);
  const [studentId, setStudentId] = useState("");
  const [invoiceDate, setInvoiceDate] = useState(todayIso());
  const [dueDate, setDueDate] = useState(todayIso());
  const [draftItems, setDraftItems] = useState<DraftItem[]>([{ description: "", quantity: "1", unit: "" }]);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams();
    if (status !== "all") params.set("status", status);
    if (overdueOnly) params.set("overdue", "true");
    if (q.trim()) params.set("q", q.trim());
    const qs = params.toString();
    setInvoices(null);
    apiFetch<Invoice[]>(`/api/invoices${qs ? `?${qs}` : ""}`)
      .then((rows) => {
        if (!cancelled) setInvoices(rows);
      })
      .catch((e) => {
        if (!cancelled) {
          setInvoices([]);
          toast(errMsg(e), "error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, overdueOnly, q, reloadKey]);

  useEffect(() => {
    apiFetch<Student[]>("/api/students")
      .then((rows) => setStudents(rows))
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openInvoice(id: Invoice["id"]) {
    setDetailLoading(true);
    setPayAmount("");
    setPayRef("");
    setPayMethod("cash");
    setPayDate(todayIso());
    try {
      const d = await apiFetch<InvoiceDetail>(`/api/invoices/${id}`);
      setSelected(d);
    } catch (e) {
      toast(errMsg(e), "error");
    } finally {
      setDetailLoading(false);
    }
  }

  function refresh() {
    setReloadKey((k) => k + 1);
  }

  async function recordPayment(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      await apiFetch("/api/payments", {
        method: "POST",
        body: {
          invoice_id: selected.id,
          amount_paise: Math.round(Number(payAmount) * 100),
          method: payMethod,
          reference: payRef.trim() === "" ? null : payRef.trim(),
          paid_on: payDate,
        },
      });
      toast("Payment recorded", "success");
      setSelected(null);
      refresh();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function cancelInvoice() {
    if (!selected) return;
    if (!window.confirm(`Cancel invoice ${selected.invoice_number}?`)) return;
    setBusy(true);
    try {
      await apiFetch(`/api/invoices/${selected.id}/cancel`, { method: "POST" });
      toast("Invoice cancelled", "success");
      setSelected(null);
      refresh();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusy(false);
    }
  }

  function updateDraft(idx: number, patch: Partial<DraftItem>) {
    setDraftItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  }

  async function createInvoice(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await apiFetch("/api/invoices", {
        method: "POST",
        body: {
          student_id: Number(studentId),
          invoice_date: invoiceDate,
          due_date: dueDate,
          items: draftItems.map((it) => ({
            description: it.description,
            quantity: Number(it.quantity),
            unit_paise: Math.round(Number(it.unit) * 100),
          })),
        },
      });
      toast("Invoice created", "success");
      setCreateOpen(false);
      setStudentId("");
      setDraftItems([{ description: "", quantity: "1", unit: "" }]);
      refresh();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-manrope text-2xl font-bold">Invoices</h1>
        <Button onClick={() => setCreateOpen(true)}>New invoice</Button>
      </div>

      <Card>
        <div className="grid gap-3 sm:grid-cols-3 sm:items-end">
          <Field label="Status">
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Search">
            <Input placeholder="Student or invoice number" value={q} onChange={(e) => setQ(e.target.value)} />
          </Field>
          <label className="flex items-center gap-2 pb-2 text-sm">
            <input type="checkbox" checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} />
            Overdue only
          </label>
        </div>
      </Card>

      <Card>
        {invoices === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : invoices.length === 0 ? (
          <Empty>No invoices match these filters.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Invoice</th>
                  <th className="py-2 pr-4">Student</th>
                  <th className="py-2 pr-4">Total</th>
                  <th className="py-2 pr-4">Outstanding</th>
                  <th className="py-2 pr-4">Due date</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr
                    key={String(inv.id)}
                    className="cursor-pointer border-b hover:bg-slate-50"
                    onClick={() => openInvoice(inv.id)}
                  >
                    <td className="py-2 pr-4 font-medium">{inv.invoice_number}</td>
                    <td className="py-2 pr-4">{inv.student_name}</td>
                    <td className="py-2 pr-4">{money(inv.total_paise)}</td>
                    <td className="py-2 pr-4">{money(inv.outstanding_paise)}</td>
                    <td className="py-2 pr-4">{inv.due_date}</td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={inv.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        open={selected !== null || detailLoading}
        onClose={() => setSelected(null)}
        title={selected ? `Invoice ${selected.invoice_number}` : "Loading invoice"}
      >
        {selected && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-slate-500">Student</span>
              <span>{selected.student_name}</span>
              <span className="text-slate-500">Total</span>
              <span>{money(selected.total_paise)}</span>
              <span className="text-slate-500">Outstanding</span>
              <span>{money(selected.outstanding_paise)}</span>
              <span className="text-slate-500">Status</span>
              <span>
                <StatusBadge status={selected.status} />
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="py-2 pr-4">Item</th>
                    <th className="py-2 pr-4">Qty</th>
                    <th className="py-2 pr-4">Unit</th>
                    <th className="py-2 pr-4">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.items.map((it, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="py-2 pr-4">{it.description}</td>
                      <td className="py-2 pr-4">{it.quantity}</td>
                      <td className="py-2 pr-4">{money(it.unit_paise)}</td>
                      <td className="py-2 pr-4">{money(it.quantity * it.unit_paise)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selected.status !== "cancelled" && selected.status !== "paid" && (
              <>
                <form onSubmit={recordPayment} className="space-y-3 rounded-md border p-3">
                  <h3 className="font-manrope font-semibold">Record payment</h3>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field label="Amount (Rs)">
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        value={payAmount}
                        onChange={(e) => setPayAmount(e.target.value)}
                      />
                    </Field>
                    <Field label="Method">
                      <Select value={payMethod} onChange={(e) => setPayMethod(e.target.value)}>
                        {METHODS.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Reference">
                      <Input value={payRef} onChange={(e) => setPayRef(e.target.value)} />
                    </Field>
                    <Field label="Paid on">
                      <Input type="date" required value={payDate} onChange={(e) => setPayDate(e.target.value)} />
                    </Field>
                  </div>
                  <div className="flex flex-wrap justify-between gap-2">
                    <Button variant="danger" type="button" disabled={busy} onClick={cancelInvoice}>
                      Cancel invoice
                    </Button>
                    <Button type="submit" disabled={busy}>
                      {busy ? "Saving..." : "Record payment"}
                    </Button>
                  </div>
                </form>
              </>
            )}
          </div>
        )}
      </Modal>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New invoice">
        <form onSubmit={createInvoice} className="space-y-4">
          <Field label="Student">
            <Select required value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              <option value="">Select a student</option>
              {students.map((s) => (
                <option key={String(s.id)} value={String(s.id)}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Invoice date">
              <Input type="date" required value={invoiceDate} onChange={(e) => setInvoiceDate(e.target.value)} />
            </Field>
            <Field label="Due date">
              <Input type="date" required value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </Field>
          </div>

          <div className="space-y-2">
            <h3 className="font-manrope text-sm font-semibold">Items</h3>
            {draftItems.map((it, idx) => (
              <div key={idx} className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end">
                <Field label="Description">
                  <Input
                    required
                    value={it.description}
                    onChange={(e) => updateDraft(idx, { description: e.target.value })}
                  />
                </Field>
                <Field label="Quantity">
                  <Input
                    type="number"
                    min="1"
                    required
                    value={it.quantity}
                    onChange={(e) => updateDraft(idx, { quantity: e.target.value })}
                  />
                </Field>
                <Field label="Unit (Rs)">
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    value={it.unit}
                    onChange={(e) => updateDraft(idx, { unit: e.target.value })}
                  />
                </Field>
                <Button
                  variant="secondary"
                  type="button"
                  disabled={draftItems.length === 1}
                  onClick={() => setDraftItems((prev) => prev.filter((_, i) => i !== idx))}
                >
                  Remove
                </Button>
              </div>
            ))}
            <Button
              variant="secondary"
              type="button"
              onClick={() => setDraftItems((prev) => [...prev, { description: "", quantity: "1", unit: "" }])}
            >
              Add item
            </Button>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Creating..." : "Create invoice"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
