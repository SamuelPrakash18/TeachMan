import { useCallback, useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import type { Payment } from "../../lib/types";
import { Card, Button, Badge, Empty, Skeleton, useToast } from "../../components/ui";

type Claim = {
  id: number;
  invoice_number: string;
  parent_name: string;
  amount_paise: number;
  upi_reference: string | null;
  status: string;
  submitted_at: string;
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Payments() {
  const { toast } = useToast();
  const [payments, setPayments] = useState<Payment[] | null>(null);
  const [claims, setClaims] = useState<Claim[] | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadPayments = useCallback(async () => {
    try {
      setPayments(await apiFetch<Payment[]>("/api/payments"));
    } catch (e) {
      setPayments([]);
      toast(errMsg(e), "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadClaims = useCallback(async () => {
    try {
      setClaims(await apiFetch<Claim[]>("/api/payments/claims?status=pending"));
    } catch (e) {
      setClaims([]);
      toast(errMsg(e), "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadPayments();
    loadClaims();
  }, [loadPayments, loadClaims]);

  async function act(id: number, action: "approve" | "reject") {
    setBusyId(id);
    try {
      await apiFetch(`/api/payments/claims/${id}/${action}`, { method: "POST" });
      toast(action === "approve" ? "Claim approved" : "Claim rejected", "success");
      await Promise.all([loadClaims(), loadPayments()]);
    } catch (e) {
      toast(errMsg(e), "error");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Payments</h1>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Pending parent claims</h2>
        {claims === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
          </div>
        ) : claims.length === 0 ? (
          <Empty>No pending claims.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Invoice</th>
                  <th className="py-2 pr-4">Parent</th>
                  <th className="py-2 pr-4">Amount</th>
                  <th className="py-2 pr-4">UPI reference</th>
                  <th className="py-2 pr-4">Submitted</th>
                  <th className="py-2 pr-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {claims.map((c) => (
                  <tr key={c.id} className="border-b">
                    <td className="py-2 pr-4">{c.invoice_number}</td>
                    <td className="py-2 pr-4">{c.parent_name}</td>
                    <td className="py-2 pr-4">{money(c.amount_paise)}</td>
                    <td className="py-2 pr-4">{c.upi_reference ?? "-"}</td>
                    <td className="py-2 pr-4">{c.submitted_at}</td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-wrap gap-2">
                        <Button disabled={busyId === c.id} onClick={() => act(c.id, "approve")}>
                          Approve
                        </Button>
                        <Button variant="danger" disabled={busyId === c.id} onClick={() => act(c.id, "reject")}>
                          Reject
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Recorded payments</h2>
        {payments === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : payments.length === 0 ? (
          <Empty>No payments recorded yet.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Paid on</th>
                  <th className="py-2 pr-4">Amount</th>
                  <th className="py-2 pr-4">Method</th>
                  <th className="py-2 pr-4">Reference</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={String(p.id)} className="border-b">
                    <td className="py-2 pr-4">{p.paid_on}</td>
                    <td className="py-2 pr-4">{money(p.amount_paise)}</td>
                    <td className="py-2 pr-4">
                      <Badge>{p.method}</Badge>
                    </td>
                    <td className="py-2 pr-4">{p.reference ?? "-"}</td>
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
