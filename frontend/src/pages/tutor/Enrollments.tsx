import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Button, Field, Select, Badge, Empty, Skeleton, useToast } from "../../components/ui";

type Enrollment = {
  id: number;
  student_name: string;
  batch_name: string;
  status: string;
  requested_at: string;
};

const FILTERS = ["all", "requested", "approved", "rejected"];
const statusLabel = (status: string) =>
  status === "requested" ? "Pending" : status === "approved" ? "Accepted" : status === "rejected" ? "Rejected" : status;

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Enrollments() {
  const { toast } = useToast();
  const [rows, setRows] = useState<Enrollment[] | null>(null);
  const [filter, setFilter] = useState("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    apiFetch<Enrollment[]>("/api/enrollments")
      .then((data) => {
        if (!cancelled) setRows(data);
      })
      .catch((e) => {
        if (!cancelled) {
          setRows([]);
          toast(errMsg(e), "error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey]);

  async function act(id: number, action: "approve" | "reject") {
    setBusyId(id);
    try {
      await apiFetch(`/api/enrollments/${id}/${action}`, { method: "POST" });
      toast(action === "approve" ? "Enrollment approved" : "Enrollment rejected", "success");
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast(errMsg(e), "error");
    } finally {
      setBusyId(null);
    }
  }

  const visible = rows?.filter((r) => filter === "all" || r.status === filter) ?? null;

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Enrollments</h1>

      <Card>
        <div className="max-w-xs">
          <Field label="Status">
            <Select value={filter} onChange={(e) => setFilter(e.target.value)}>
              {FILTERS.map((f) => (
                <option key={f} value={f}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      <Card>
        {visible === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : visible.length === 0 ? (
          <Empty>No enrollments match this filter.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Student</th>
                  <th className="py-2 pr-4">Batch</th>
                  <th className="py-2 pr-4">Requested</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((r) => (
                  <tr key={r.id} className="border-b">
                    <td className="py-2 pr-4 font-medium">{r.student_name}</td>
                    <td className="py-2 pr-4">{r.batch_name}</td>
                    <td className="py-2 pr-4">{r.requested_at}</td>
                    <td className="py-2 pr-4">
                      <Badge>{statusLabel(r.status)}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      {r.status === "requested" && (
                        <div className="flex flex-wrap gap-2">
                          <Button disabled={busyId === r.id} onClick={() => act(r.id, "approve")}>
                            Accept
                          </Button>
                          <Button
                            variant="danger"
                            disabled={busyId === r.id}
                            onClick={() => act(r.id, "reject")}
                          >
                            Reject
                          </Button>
                        </div>
                      )}
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
