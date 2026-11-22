import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, StatusBadge, Empty, Skeleton, useToast } from "../../components/ui";

interface Enrollment {
  id: number;
  student_name: string;
  batch_name: string;
  status: string;
  requested_at: string;
  decided_at: string | null;
}

export default function Enrollments() {
  const toast = useToast();
  const [rows, setRows] = useState<Enrollment[] | null>(null);

  useEffect(() => {
    apiFetch<Enrollment[]>("/api/enrollments")
      .then(setRows)
      .catch((e: unknown) => {
        setRows([]);
        toast.error(e instanceof Error ? e.message : "Could not load enrollments");
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Enrollment requests</h1>
        <p className="text-sm text-slate-500">Status of every batch request you have made.</p>
      </div>

      {rows === null ? (
        <Skeleton className="h-40" />
      ) : rows.length === 0 ? (
        <Empty>You have not requested any enrollments yet.</Empty>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Student</th>
                  <th className="py-2 pr-4">Batch</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Requested</th>
                  <th className="py-2 pr-4">Decided</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-2 pr-4">{r.student_name}</td>
                    <td className="py-2 pr-4">{r.batch_name}</td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-2 pr-4">{r.requested_at}</td>
                    <td className="py-2 pr-4">{r.decided_at ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
