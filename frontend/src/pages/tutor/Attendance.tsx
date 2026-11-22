import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Button, Field, Input, Select, Badge, Empty, Skeleton, Modal, useToast } from "../../components/ui";

type SessionRow = {
  id: number;
  batch_name: string;
  session_date: string;
  status: string;
};

type Batch = { id: number; name: string };

type Record = { student_id: number; student_name: string; status: "present" | "absent" | "excused" };

type SessionDetail = {
  session_id: number;
  session_date: string;
  batch_name: string;
  records: Record[];
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");
const todayIso = () => new Date().toISOString().slice(0, 10);

export default function Attendance() {
  const { toast } = useToast();
  const [sessions, setSessions] = useState<SessionRow[] | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [batchId, setBatchId] = useState("");
  const [sessionDate, setSessionDate] = useState(todayIso());
  const [creating, setCreating] = useState(false);

  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [marks, setMarks] = useState<Record[]>([]);
  const [saving, setSaving] = useState(false);
  const [opening, setOpening] = useState<number | null>(null);

  const loadSessions = useCallback(async () => {
    try {
      setSessions(await apiFetch<SessionRow[]>("/api/attendance/sessions"));
    } catch (e) {
      setSessions([]);
      toast(errMsg(e), "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadSessions();
    apiFetch<Batch[]>("/api/batches")
      .then((rows) => setBatches(rows))
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createSession(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await apiFetch("/api/attendance/sessions", {
        method: "POST",
        body: { batch_id: Number(batchId), session_date: sessionDate },
      });
      toast("Session created", "success");
      setCreateOpen(false);
      await loadSessions();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setCreating(false);
    }
  }

  async function openSession(id: number) {
    setOpening(id);
    try {
      const d = await apiFetch<SessionDetail>(`/api/attendance/sessions/${id}`);
      setDetail(d);
      setMarks(d.records.map((r) => ({ ...r })));
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setOpening(null);
    }
  }

  function setMark(studentId: number, status: Record["status"]) {
    setMarks((prev) => prev.map((m) => (m.student_id === studentId ? { ...m, status } : m)));
  }

  async function saveMarks() {
    if (!detail) return;
    setSaving(true);
    try {
      await apiFetch("/api/attendance/mark", {
        method: "POST",
        body: {
          session_id: detail.session_id,
          records: marks.map((m) => ({ student_id: m.student_id, status: m.status })),
        },
      });
      toast("Attendance saved", "success");
      await loadSessions();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-manrope text-2xl font-bold">Attendance</h1>
        <Button onClick={() => setCreateOpen(true)}>New session</Button>
      </div>

      <Card>
        {sessions === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : sessions.length === 0 ? (
          <Empty>No attendance sessions yet.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Batch</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id} className="border-b">
                    <td className="py-2 pr-4">{s.session_date}</td>
                    <td className="py-2 pr-4">{s.batch_name}</td>
                    <td className="py-2 pr-4">
                      <Badge>{s.status}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      <Button variant="secondary" disabled={opening === s.id} onClick={() => openSession(s.id)}>
                        {opening === s.id ? "Opening..." : "Open"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {detail && (
        <Card>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-manrope text-lg font-semibold">
              {detail.batch_name} · {detail.session_date}
            </h2>
            <Button variant="secondary" onClick={() => setDetail(null)}>
              Close
            </Button>
          </div>
          {marks.length === 0 ? (
            <Empty>No students in this batch.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="py-2 pr-4">Student</th>
                    <th className="py-2 pr-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {marks.map((m) => (
                    <tr key={m.student_id} className="border-b">
                      <td className="py-2 pr-4">{m.student_name}</td>
                      <td className="py-2 pr-4">
                        <Select
                          value={m.status}
                          onChange={(e) => setMark(m.student_id, e.target.value as Record["status"])}
                        >
                          <option value="present">Present</option>
                          <option value="absent">Absent</option>
                          <option value="excused">Excused</option>
                        </Select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {marks.length > 0 && (
            <div className="mt-4 flex justify-end">
              <Button onClick={saveMarks} disabled={saving}>
                {saving ? "Saving..." : "Save attendance"}
              </Button>
            </div>
          )}
        </Card>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New attendance session">
        <form onSubmit={createSession} className="space-y-4">
          <Field label="Batch">
            <Select required value={batchId} onChange={(e) => setBatchId(e.target.value)}>
              <option value="">Select a batch</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Session date">
            <Input type="date" required value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={creating}>
              {creating ? "Creating..." : "Create session"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
