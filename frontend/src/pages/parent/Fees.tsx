import { useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import type { Invoice, InvoiceItem } from "../../lib/types";
import { Card, Button, Field, Input, Select, Badge, StatusBadge, Empty, Skeleton, Modal, useToast } from "../../components/ui";

interface InvoicePaymentRow {
  id: number;
  amount_paise: number;
  paid_on?: string;
  method?: string;
}

interface InvoiceDetail extends Omit<Invoice, "items"> {
  items?: InvoiceItem[];
  payments?: InvoicePaymentRow[];
}

interface Claim {
  id: number;
  invoice_number: string;
  amount_paise: number;
  upi_reference: string;
  status: string;
  submitted_at: string;
}

export default function Fees() {
  const toast = useToast();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [claims, setClaims] = useState<Claim[] | null>(null);
  const [selected, setSelected] = useState<InvoiceDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [receipt, setReceipt] = useState<string | null>(null);

  const [claimInvoiceId, setClaimInvoiceId] = useState("");
  const [claimAmount, setClaimAmount] = useState("");
  const [upiReference, setUpiReference] = useState("");
  const [submittingClaim, setSubmittingClaim] = useState(false);

  const loadInvoices = () => {
    apiFetch<Invoice[]>("/api/invoices")
      .then(setInvoices)
      .catch((e: unknown) => {
        setInvoices([]);
        toast.error(e instanceof Error ? e.message : "Could not load invoices");
      });
  };

  const loadClaims = () => {
    apiFetch<Claim[]>("/api/payments/claims")
      .then(setClaims)
      .catch((e: unknown) => {
        setClaims([]);
        toast.error(e instanceof Error ? e.message : "Could not load payment claims");
      });
  };

  useEffect(() => {
    loadInvoices();
    loadClaims();
  }, []);

  const openInvoice = (inv: Invoice) => {
    setDetailLoading(true);
    setSelected({ ...inv });
    apiFetch<InvoiceDetail>(`/api/invoices/${inv.id}`)
      .then(setSelected)
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load invoice"))
      .finally(() => setDetailLoading(false));
  };

  const showReceipt = (inv: Invoice) => {
    setReceipt(null);
    apiFetch<unknown>(`/api/invoices/${inv.id}/receipt`)
      .then((data) => setReceipt(typeof data === "string" ? data : JSON.stringify(data, null, 2)))
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load receipt"));
  };

  const outstandingInvoices = (invoices ?? []).filter((i) => i.outstanding_paise > 0);

  const submitClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    const amountPaise = Math.round(Number(claimAmount) * 100);
    if (!claimInvoiceId) {
      toast.error("Choose an invoice");
      return;
    }
    if (!Number.isFinite(amountPaise) || amountPaise <= 0) {
      toast.error("Enter a valid amount");
      return;
    }
    if (upiReference.trim().length < 4) {
      toast.error("UPI transaction reference must be at least 4 characters");
      return;
    }
    setSubmittingClaim(true);
    try {
      await apiFetch("/api/payments/claims", {
        method: "POST",
        body: {
          invoice_id: Number(claimInvoiceId),
          amount_paise: amountPaise,
          upi_reference: upiReference.trim(),
        },
      });
      toast.success("Payment submitted for your tutor to verify");
      setClaimInvoiceId("");
      setClaimAmount("");
      setUpiReference("");
      loadClaims();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not submit payment");
    } finally {
      setSubmittingClaim(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Fees and payments</h1>
        <p className="text-sm text-slate-500">Invoices for your children and your payment claims.</p>
      </div>

      <Card>
        <h2 className="font-manrope text-lg font-semibold">How to pay</h2>
        <p className="mt-2 text-sm text-slate-600">
          Pay to the UPI ID your tutor shares, then submit the transaction reference below.
        </p>
      </Card>

      <section className="space-y-3">
        <h2 className="font-manrope text-lg font-semibold">Invoices</h2>
        {invoices === null ? (
          <Skeleton className="h-40" />
        ) : invoices.length === 0 ? (
          <Empty>No invoices yet.</Empty>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Invoice</th>
                    <th className="py-2 pr-4">Student</th>
                    <th className="py-2 pr-4">Total</th>
                    <th className="py-2 pr-4">Paid</th>
                    <th className="py-2 pr-4">Outstanding</th>
                    <th className="py-2 pr-4">Due date</th>
                    <th className="py-2 pr-4">Days overdue</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv) => (
                    <tr
                      key={inv.id}
                      className="cursor-pointer border-b last:border-0 hover:bg-slate-50"
                      onClick={() => openInvoice(inv)}
                    >
                      <td className="py-2 pr-4">{inv.invoice_number}</td>
                      <td className="py-2 pr-4">{inv.student_name}</td>
                      <td className="py-2 pr-4">{money(inv.total_paise)}</td>
                      <td className="py-2 pr-4">{money(inv.paid_paise)}</td>
                      <td className="py-2 pr-4">{money(inv.outstanding_paise)}</td>
                      <td className="py-2 pr-4">{inv.due_date}</td>
                      <td className="py-2 pr-4">{inv.days_overdue}</td>
                      <td className="py-2 pr-4">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="py-2 pr-4">
                        {inv.paid_paise > 0 && (
                          <Button
                            variant="secondary"
                            onClick={(e) => {
                              e.stopPropagation();
                              showReceipt(inv);
                            }}
                          >
                            Receipt
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </section>

      {receipt !== null && (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-manrope text-lg font-semibold">Receipt</h2>
            <Button variant="primary" onClick={() => window.print()}>Print</Button>
          </div>
          <pre className="whitespace-pre-wrap rounded bg-slate-50 p-4 font-mono text-sm print:bg-white">{receipt}</pre>
        </Card>
      )}

      <section className="space-y-3">
        <h2 className="font-manrope text-lg font-semibold">Submit a payment</h2>
        <Card>
          {outstandingInvoices.length === 0 ? (
            <p className="text-sm text-slate-500">No invoices have an outstanding balance.</p>
          ) : (
            <form onSubmit={submitClaim} className="grid gap-3 sm:grid-cols-4">
              <Field label="Invoice">
                <Select value={claimInvoiceId} onChange={(e) => setClaimInvoiceId(e.target.value)}>
                  <option value="">Select an invoice</option>
                  {outstandingInvoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} ({money(inv.outstanding_paise)} due)
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Amount paid (rupees)">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={claimAmount}
                  onChange={(e) => setClaimAmount(e.target.value)}
                />
              </Field>
              <Field label="UPI transaction reference">
                <Input value={upiReference} onChange={(e) => setUpiReference(e.target.value)} />
              </Field>
              <div className="flex items-end">
                <Button type="submit" variant="primary" disabled={submittingClaim}>
                  {submittingClaim ? "Submitting..." : "Submit"}
                </Button>
              </div>
            </form>
          )}
        </Card>

        <h3 className="font-manrope text-base font-semibold">Your payment claims</h3>
        {claims === null ? (
          <Skeleton className="h-24" />
        ) : claims.length === 0 ? (
          <Empty>You have not submitted any payments.</Empty>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Invoice</th>
                    <th className="py-2 pr-4">Amount</th>
                    <th className="py-2 pr-4">UPI reference</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {claims.map((c) => (
                    <tr key={c.id} className="border-b last:border-0">
                      <td className="py-2 pr-4">{c.invoice_number}</td>
                      <td className="py-2 pr-4">{money(c.amount_paise)}</td>
                      <td className="py-2 pr-4">{c.upi_reference}</td>
                      <td className="py-2 pr-4">
                        <StatusBadge status={c.status} />
                      </td>
                      <td className="py-2 pr-4">{c.submitted_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </section>

      <Modal open={selected !== null} onClose={() => setSelected(null)} title={selected ? `Invoice ${selected.invoice_number}` : "Invoice"}>
        {selected === null || detailLoading ? (
          <Skeleton className="h-40" />
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <p>Student: {selected.student_name}</p>
              <p>Due date: {selected.due_date}</p>
              <p>Total: {money(selected.total_paise)}</p>
              <p>Paid: {money(selected.paid_paise)}</p>
              <p>Outstanding: {money(selected.outstanding_paise)}</p>
              <p className="flex items-center gap-2">Status: <StatusBadge status={selected.status} /></p>
            </div>

            <div>
              <h3 className="font-manrope text-sm font-semibold">Items</h3>
              {(selected.items ?? []).length === 0 ? (
                <p className="text-sm text-slate-500">No line items.</p>
              ) : (
                <ul className="mt-1 divide-y text-sm">
                  {(selected.items ?? []).map((it, i) => (
                    <li key={i} className="flex justify-between py-1">
                      <span>{it.description}</span>
                      <span>{money(it.amount_paise)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {(selected.payments ?? []).length > 0 && (
              <div>
                <h3 className="font-manrope text-sm font-semibold">Payments</h3>
                <ul className="mt-1 divide-y text-sm">
                  {(selected.payments ?? []).map((p) => (
                    <li key={p.id} className="flex justify-between py-1">
                      <span>
                        {p.paid_on ?? ""} {p.method ? <Badge>{p.method}</Badge> : null}
                      </span>
                      <span>{money(p.amount_paise)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
