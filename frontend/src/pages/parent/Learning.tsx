import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Child } from "../../lib/types";
import { Card, Field, Select, StatusBadge, Empty, Skeleton, useToast } from "../../components/ui";

interface Milestone {
  id: number;
  subject: string;
  topic: string;
  status: string;
  score: number | null;
  notes: string | null;
  updated_at: string;
}

export default function Learning() {
  const toast = useToast();
  const [children, setChildren] = useState<Child[] | null>(null);
  const [studentId, setStudentId] = useState("");
  const [milestones, setMilestones] = useState<Milestone[] | null>(null);

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
    setMilestones(null);
    apiFetch<Milestone[]>(`/api/learning/milestones?student_id=${encodeURIComponent(studentId)}`)
      .then(setMilestones)
      .catch((e: unknown) => {
        setMilestones([]);
        toast.error(e instanceof Error ? e.message : "Could not load learning progress");
      });
  }, [studentId]);

  const grouped = useMemo(() => {
    return (milestones ?? []).reduce<Record<string, Milestone[]>>((acc, m) => {
      (acc[m.subject] ??= []).push(m);
      return acc;
    }, {});
  }, [milestones]);

  const subjects = Object.keys(grouped);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Learning progress</h1>
        <p className="text-sm text-slate-500">Milestones your child has reached, grouped by subject.</p>
      </div>

      {children === null ? (
        <Skeleton className="h-12" />
      ) : children.length === 0 ? (
        <Empty>Add a child to see learning progress.</Empty>
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

          {milestones === null ? (
            <Skeleton className="h-40" />
          ) : subjects.length === 0 ? (
            <Empty>No learning milestones recorded yet.</Empty>
          ) : (
            subjects.map((subject) => (
              <section key={subject} className="space-y-3">
                <h2 className="font-manrope text-lg font-semibold">{subject}</h2>
                <Card>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b text-slate-500">
                        <tr>
                          <th className="py-2 pr-4">Topic</th>
                          <th className="py-2 pr-4">Status</th>
                          <th className="py-2 pr-4">Score</th>
                          <th className="py-2 pr-4">Notes</th>
                          <th className="py-2 pr-4">Updated</th>
                        </tr>
                      </thead>
                      <tbody>
                        {grouped[subject].map((m) => (
                          <tr key={m.id} className="border-b last:border-0">
                            <td className="py-2 pr-4">{m.topic}</td>
                            <td className="py-2 pr-4">
                              <StatusBadge status={m.status} />
                            </td>
                            <td className="py-2 pr-4">{m.score ?? "-"}</td>
                            <td className="py-2 pr-4">{m.notes ?? "-"}</td>
                            <td className="py-2 pr-4">{m.updated_at}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </section>
            ))
          )}
        </>
      )}
    </div>
  );
}
