import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Button, Field, Input, Badge, Empty, Skeleton, useToast } from "../../components/ui";

type Course = {
  id: number;
  subject: string;
  grade: string;
  is_active: boolean;
  batch_count: number;
};

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Courses() {
  const { toast } = useToast();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [subject, setSubject] = useState("");
  const [grade, setGrade] = useState("");
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      setCourses(await apiFetch<Course[]>("/api/courses"));
    } catch (e) {
      setCourses([]);
      toast(errMsg(e), "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function addCourse(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/courses", { method: "POST", body: { subject, grade } });
      toast("Course added", "success");
      setSubject("");
      setGrade("");
      await load();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(c: Course) {
    setBusyId(c.id);
    try {
      await apiFetch(`/api/courses/${c.id}`, { method: "PUT", body: { is_active: !c.is_active } });
      toast(c.is_active ? "Course deactivated" : "Course activated", "success");
      await load();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  async function removeCourse(c: Course) {
    if (!window.confirm(`Delete course "${c.subject}" (${c.grade})?`)) return;
    setBusyId(c.id);
    try {
      await apiFetch(`/api/courses/${c.id}`, { method: "DELETE" });
      toast("Course deleted", "success");
      await load();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Courses</h1>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Add course</h2>
        <form onSubmit={addCourse} className="grid gap-3 sm:grid-cols-3 sm:items-end">
          <Field label="Subject">
            <Input required value={subject} onChange={(e) => setSubject(e.target.value)} />
          </Field>
          <Field label="Grade">
            <Input required value={grade} onChange={(e) => setGrade(e.target.value)} />
          </Field>
          <Button type="submit" disabled={saving}>
            {saving ? "Adding..." : "Add course"}
          </Button>
        </form>
      </Card>

      <Card>
        {courses === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : courses.length === 0 ? (
          <Empty>No courses yet. Add one above.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Subject</th>
                  <th className="py-2 pr-4">Grade</th>
                  <th className="py-2 pr-4">Batches</th>
                  <th className="py-2 pr-4">Active</th>
                  <th className="py-2 pr-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {courses.map((c) => (
                  <tr key={c.id} className="border-b">
                    <td className="py-2 pr-4 font-medium">{c.subject}</td>
                    <td className="py-2 pr-4">{c.grade}</td>
                    <td className="py-2 pr-4">{c.batch_count}</td>
                    <td className="py-2 pr-4">
                      <Badge>{c.is_active ? "Active" : "Inactive"}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          disabled={busyId === c.id}
                          onClick={() => toggleActive(c)}
                        >
                          {c.is_active ? "Deactivate" : "Activate"}
                        </Button>
                        <Button variant="danger" disabled={busyId === c.id} onClick={() => removeCourse(c)}>
                          Delete
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
    </div>
  );
}
