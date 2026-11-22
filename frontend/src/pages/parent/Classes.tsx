import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Badge, Empty, Skeleton, useToast } from "../../components/ui";

interface Enrollment {
  id: number;
  student_name: string;
  batch_name: string;
  status: string;
  requested_at: string;
  decided_at: string | null;
}

export default function Classes() {
  const toast = useToast();
  const [rows, setRows] = useState<Enrollment[] | null>(null);

  useEffect(() => {
    apiFetch<Enrollment[]>("/api/enrollments")
      .then(setRows)
      .catch((e: unknown) => {
        setRows([]);
        toast.error(e instanceof Error ? e.message : "Could not load classes");
      });
  }, []);

  const grouped = useMemo(() => {
    const approved = (rows ?? []).filter((r) => r.status === "approved");
    return approved.reduce<Record<string, Enrollment[]>>((acc, r) => {
      (acc[r.student_name] ??= []).push(r);
      return acc;
    }, {});
  }, [rows]);

  const students = Object.keys(grouped);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">My classes</h1>
        <p className="text-sm text-slate-500">Batches your children are approved for.</p>
      </div>

      {rows === null ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : students.length === 0 ? (
        <Empty>No approved classes yet.</Empty>
      ) : (
        students.map((student) => (
          <section key={student} className="space-y-3">
            <h2 className="font-manrope text-lg font-semibold">{student}</h2>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {grouped[student].map((c) => (
                <Card key={c.id}>
                  <h3 className="font-manrope text-base font-semibold">{c.batch_name}</h3>
                  <div className="mt-2">
                    <Badge>Approved</Badge>
                  </div>
                  {c.decided_at && <p className="mt-2 text-xs text-slate-500">Approved on {c.decided_at}</p>}
                </Card>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
