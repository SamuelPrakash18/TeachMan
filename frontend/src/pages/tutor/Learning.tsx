import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Student } from "../../lib/types";
import { Card, Button, Field, Input, Select, Textarea, Badge, Empty, Skeleton, useToast } from "../../components/ui";

type Milestone = {
  id: number;
  subject: string;
  topic: string;
  status: string;
  score: number | null;
  notes: string | null;
};

const STATUSES = ["not_started", "in_progress", "completed", "needs_review"];

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Learning() {
  const { toast } = useToast();
  const [students, setStudents] = useState<Student[]>([]);
  const [studentId, setStudentId] = useState("");
  const [milestones, setMilestones] = useState<Milestone[] | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [status, setStatus] = useState("not_started");
  const [score, setScore] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    apiFetch<Student[]>("/api/students")
      .then((rows) => {
        setStudents(rows);
        if (rows.length > 0) setStudentId(String(rows[0].id));
      })
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!studentId) {
      setMilestones([]);
      return;
    }
    let cancelled = false;
    setMilestones(null);
    apiFetch<Milestone[]>(`/api/learning/milestones?student_id=${studentId}`)
      .then((rows) => {
        if (!cancelled) setMilestones(rows);
      })
      .catch((e) => {
        if (!cancelled) {
          setMilestones([]);
          toast(errMsg(e), "error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId, reloadKey]);

  async function addMilestone(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/learning/milestones", {
        method: "POST",
        body: {
          student_id: Number(studentId),
          subject,
          topic,
          status,
          score: score.trim() === "" ? null : Number(score),
          notes,
        },
      });
      toast("Milestone added", "success");
      setSubject("");
      setTopic("");
      setScore("");
      setNotes("");
      setStatus("not_started");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(m: Milestone, next: string) {
    setBusyId(m.id);
    try {
      await apiFetch(`/api/learning/milestones/${m.id}`, { method: "PUT", body: { status: next } });
      toast("Status updated", "success");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Learning progress</h1>

      <Card>
        <div className="max-w-sm">
          <Field label="Student">
            <Select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              <option value="">Select a student</option>
              {students.map((s) => (
                <option key={String(s.id)} value={String(s.id)}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      {studentId && (
        <Card>
          <h2 className="font-manrope mb-3 text-lg font-semibold">Add milestone</h2>
          <form onSubmit={addMilestone} className="grid gap-3 sm:grid-cols-2">
            <Field label="Subject">
              <Input required value={subject} onChange={(e) => setSubject(e.target.value)} />
            </Field>
            <Field label="Topic">
              <Input required value={topic} onChange={(e) => setTopic(e.target.value)} />
            </Field>
            <Field label="Status">
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Score (optional)">
              <Input type="number" step="any" value={score} onChange={(e) => setScore(e.target.value)} />
            </Field>
            <div className="sm:col-span-2">
              <Field label="Notes">
                <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
              </Field>
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? "Adding..." : "Add milestone"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {!studentId ? (
          <Empty>Select a student to see their milestones.</Empty>
        ) : milestones === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : milestones.length === 0 ? (
          <Empty>No milestones recorded for this student.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Subject</th>
                  <th className="py-2 pr-4">Topic</th>
                  <th className="py-2 pr-4">Score</th>
                  <th className="py-2 pr-4">Notes</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {milestones.map((m) => (
                  <tr key={m.id} className="border-b">
                    <td className="py-2 pr-4">{m.subject}</td>
                    <td className="py-2 pr-4">{m.topic}</td>
                    <td className="py-2 pr-4">{m.score ?? "-"}</td>
                    <td className="py-2 pr-4">{m.notes ?? "-"}</td>
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <Badge>{m.status.replace("_", " ")}</Badge>
                        <Select
                          value={m.status}
                          disabled={busyId === m.id}
                          onChange={(e) => changeStatus(m, e.target.value)}
                        >
                          {STATUSES.map((s) => (
                            <option key={s} value={s}>
                              {s.replace("_", " ")}
                            </option>
                          ))}
                        </Select>
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
