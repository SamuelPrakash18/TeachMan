import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Child } from "../../lib/types";
import { Card, Field, Select, Stat, StatusBadge, Empty, Skeleton, useToast } from "../../components/ui";

interface AttendanceRecord {
  session_date: string;
  batch_name: string;
  status: string;
}

interface AttendanceSummary {
  total: number;
  present: number;
  absent: number;
  excused: number;
  percent_present: number;
  records: AttendanceRecord[];
}

export default function Attendance() {
  const toast = useToast();
  const [children, setChildren] = useState<Child[] | null>(null);
  const [studentId, setStudentId] = useState("");
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<Child[]>("/api/parent/children")
      .then((list) => {
        setChildren(list);
        if (list.length > 0) setStudentId(String(list[0].id));
      })
      .catch((e: unknown) => {
        setChildren([]);
        toast.error(e instanceof Error ? e.message : "Could not load children");
      });
  }, []);

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    setSummary(null);
    apiFetch<AttendanceSummary>(`/api/attendance/students/${studentId}`)
      .then(setSummary)
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load attendance"))
      .finally(() => setLoading(false));
  }, [studentId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Attendance</h1>
        <p className="text-sm text-slate-500">Read-only attendance record for your child.</p>
      </div>

      {children === null ? (
        <Skeleton className="h-12" />
      ) : children.length === 0 ? (
        <Empty>Add a child to see attendance.</Empty>
      ) : (
        <>
          <Card>
            <Field label="Child">
              <Select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
                {children.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </Select>
            </Field>
          </Card>

          {loading || summary === null ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {[0, 1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                <Card><Stat label="Sessions" value={String(summary.total)} /></Card>
                <Card><Stat label="Present" value={String(summary.present)} /></Card>
                <Card><Stat label="Absent" value={String(summary.absent)} /></Card>
                <Card><Stat label="Excused" value={String(summary.excused)} /></Card>
                <Card><Stat label="Attendance" value={`${summary.percent_present}%`} /></Card>
              </div>

              {summary.records.length === 0 ? (
                <Empty>No attendance records yet.</Empty>
              ) : (
                <Card>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b text-slate-500">
                        <tr>
                          <th className="py-2 pr-4">Date</th>
                          <th className="py-2 pr-4">Batch</th>
                          <th className="py-2 pr-4">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.records.map((r, i) => (
                          <tr key={`${r.session_date}-${i}`} className="border-b last:border-0">
                            <td className="py-2 pr-4">{r.session_date}</td>
                            <td className="py-2 pr-4">{r.batch_name}</td>
                            <td className="py-2 pr-4">
                              <StatusBadge status={r.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
