import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Student } from "../../lib/types";
import { Card, Button, Field, Input, Empty, Skeleton, Modal, useToast } from "../../components/ui";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Students() {
  const { toast } = useToast();
  const [students, setStudents] = useState<Student[] | null>(null);
  const [q, setQ] = useState("");
  const [grade, setGrade] = useState("");
  const [selected, setSelected] = useState<Student | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [name, setName] = useState("");
  const [newGrade, setNewGrade] = useState("");
  const [address, setAddress] = useState("");
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (grade.trim()) params.set("grade", grade.trim());
    const qs = params.toString();
    setStudents(null);
    apiFetch<Student[]>(`/api/students${qs ? `?${qs}` : ""}`)
      .then((rows) => {
        if (!cancelled) setStudents(rows);
      })
      .catch((e) => {
        if (!cancelled) {
          setStudents([]);
          toast(errMsg(e), "error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, grade, reloadKey]);

  async function addStudent(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/students", {
        method: "POST",
        body: { name, grade: newGrade, address },
      });
      toast("Student added", "success");
      setAddOpen(false);
      setName("");
      setNewGrade("");
      setAddress("");
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-manrope text-2xl font-bold">Students</h1>
        <Button onClick={() => setAddOpen(true)}>Add student</Button>
      </div>

      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Search">
            <Input placeholder="Name or parent" value={q} onChange={(e) => setQ(e.target.value)} />
          </Field>
          <Field label="Grade">
            <Input placeholder="e.g. 8" value={grade} onChange={(e) => setGrade(e.target.value)} />
          </Field>
        </div>
      </Card>

      <Card>
        {students === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : students.length === 0 ? (
          <Empty>No students found.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Grade</th>
                  <th className="py-2 pr-4">Parent</th>
                  <th className="py-2 pr-4">Parent phone</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr
                    key={String(s.id)}
                    className="cursor-pointer border-b hover:bg-slate-50"
                    onClick={() => setSelected(s)}
                  >
                    <td className="py-2 pr-4 font-medium">{s.name}</td>
                    <td className="py-2 pr-4">{s.grade}</td>
                    <td className="py-2 pr-4">{s.parent_name}</td>
                    <td className="py-2 pr-4">{s.parent_phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal open={selected !== null} onClose={() => setSelected(null)} title={selected?.name ?? "Student"}>
        {selected && (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-slate-500">Grade</dt>
            <dd>{selected.grade}</dd>
            <dt className="text-slate-500">Parent name</dt>
            <dd>{selected.parent_name}</dd>
            <dt className="text-slate-500">Parent phone</dt>
            <dd>{selected.parent_phone}</dd>
            <dt className="text-slate-500">Enrolled on</dt>
            <dd>{selected.enrolled_on}</dd>
            <dt className="text-slate-500">Public ID</dt>
            <dd className="break-all">{selected.public_id}</dd>
          </dl>
        )}
      </Modal>

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add student">
        <form onSubmit={addStudent} className="space-y-4">
          <Field label="Name">
            <Input required value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Grade">
            <Input required value={newGrade} onChange={(e) => setNewGrade(e.target.value)} />
          </Field>
          <Field label="Address">
            <Input value={address} onChange={(e) => setAddress(e.target.value)} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save student"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
