import { useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import { Card, Button, Field, Input, Select, Badge, Empty, Skeleton, Modal, useToast } from "../../components/ui";

type Batch = {
  id: number;
  name: string;
  course_label: string;
  monthly_fee_paise: number;
  capacity: number;
  enrolled_count: number;
  seats_left: number;
  teaching_mode: string;
  status: string;
};

type Course = {
  id: number;
  subject: string;
  grade: string;
  is_active: boolean;
  batch_count: number;
};

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const MODES = ["offline", "online", "hybrid"];

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Batches() {
  const { toast } = useToast();
  const [batches, setBatches] = useState<Batch[] | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const [courseId, setCourseId] = useState("");
  const [name, setName] = useState("");
  const [fee, setFee] = useState("");
  const [capacity, setCapacity] = useState("20");
  const [teachingMode, setTeachingMode] = useState("offline");
  const [weekday, setWeekday] = useState("0");
  const [startTime, setStartTime] = useState("16:00");
  const [endTime, setEndTime] = useState("17:00");
  const [location, setLocation] = useState("");

  useEffect(() => {
    let cancelled = false;
    setBatches(null);
    apiFetch<Batch[]>("/api/batches")
      .then((rows) => {
        if (!cancelled) setBatches(rows);
      })
      .catch((e) => {
        if (!cancelled) {
          setBatches([]);
          toast(errMsg(e), "error");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey]);

  useEffect(() => {
    apiFetch<Course[]>("/api/courses")
      .then((rows) => setCourses(rows))
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createBatch(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/batches", {
        method: "POST",
        body: {
          course_id: Number(courseId),
          name,
          monthly_fee_paise: Math.round(Number(fee) * 100),
          capacity: Number(capacity),
          teaching_mode: teachingMode,
          status: "active",
          schedules: [
            {
              weekday: Number(weekday),
              start_time: startTime,
              end_time: endTime,
              location,
            },
          ],
        },
      });
      toast("Batch created", "success");
      setOpen(false);
      setName("");
      setFee("");
      setLocation("");
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
        <h1 className="font-manrope text-2xl font-bold">Batches</h1>
        <Button onClick={() => setOpen(true)}>New batch</Button>
      </div>

      <Card>
        {batches === null ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : batches.length === 0 ? (
          <Empty>No batches yet. Create one to start enrolling students.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-4">Batch</th>
                  <th className="py-2 pr-4">Course</th>
                  <th className="py-2 pr-4">Monthly fee</th>
                  <th className="py-2 pr-4">Enrolled / capacity</th>
                  <th className="py-2 pr-4">Seats left</th>
                  <th className="py-2 pr-4">Mode</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((b) => (
                  <tr key={b.id} className="border-b">
                    <td className="py-2 pr-4 font-medium">{b.name}</td>
                    <td className="py-2 pr-4">{b.course_label}</td>
                    <td className="py-2 pr-4">{money(b.monthly_fee_paise)}</td>
                    <td className="py-2 pr-4">
                      {b.enrolled_count} / {b.capacity}
                    </td>
                    <td className="py-2 pr-4">{b.seats_left}</td>
                    <td className="py-2 pr-4 capitalize">{b.teaching_mode}</td>
                    <td className="py-2 pr-4">
                      <Badge>{b.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal open={open} onClose={() => setOpen(false)} title="New batch">
        <form onSubmit={createBatch} className="space-y-4">
          <Field label="Course">
            <Select required value={courseId} onChange={(e) => setCourseId(e.target.value)}>
              <option value="">Select a course</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.subject} ({c.grade})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Batch name">
            <Input required value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Monthly fee (Rs)">
              <Input type="number" min="0" step="0.01" required value={fee} onChange={(e) => setFee(e.target.value)} />
            </Field>
            <Field label="Capacity">
              <Input type="number" min="1" required value={capacity} onChange={(e) => setCapacity(e.target.value)} />
            </Field>
          </div>
          <Field label="Teaching mode">
            <Select value={teachingMode} onChange={(e) => setTeachingMode(e.target.value)}>
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </Select>
          </Field>
          <fieldset className="space-y-3 rounded-md border p-3">
            <legend className="px-1 text-sm font-medium">Schedule</legend>
            <Field label="Weekday">
              <Select value={weekday} onChange={(e) => setWeekday(e.target.value)}>
                {WEEKDAYS.map((d, i) => (
                  <option key={d} value={i}>
                    {d}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Start time">
                <Input type="time" required value={startTime} onChange={(e) => setStartTime(e.target.value)} />
              </Field>
              <Field label="End time">
                <Input type="time" required value={endTime} onChange={(e) => setEndTime(e.target.value)} />
              </Field>
            </div>
            <Field label="Location">
              <Input value={location} onChange={(e) => setLocation(e.target.value)} />
            </Field>
          </fieldset>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Creating..." : "Create batch"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
