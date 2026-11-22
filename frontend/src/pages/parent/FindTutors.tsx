import { useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import type { Child } from "../../lib/types";
import { Card, Button, Field, Input, Select, Badge, Empty, Skeleton, useToast } from "../../components/ui";

interface TutorCard {
  id: number;
  tuition_name: string;
  display_name: string;
  district: string;
  subjects: string | string[];
  grades: string | string[];
  teaching_mode: string;
}

interface PublicBatch {
  id: number;
  name: string;
  tutor_name: string;
  course_label: string;
  monthly_fee_paise: number;
  seats_left: number;
  teaching_mode: string;
  schedules: string[];
}

const listText = (v: string | string[]) => (Array.isArray(v) ? v.join(", ") : v);

export default function FindTutors() {
  const toast = useToast();
  const [subject, setSubject] = useState("");
  const [grade, setGrade] = useState("");
  const [district, setDistrict] = useState("");
  const [tutors, setTutors] = useState<TutorCard[] | null>(null);
  const [batches, setBatches] = useState<PublicBatch[] | null>(null);
  const [children, setChildren] = useState<Child[]>([]);
  const [studentId, setStudentId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadTutors = (filters: { subject: string; grade: string; district: string }) => {
    const params = new URLSearchParams();
    if (filters.subject.trim()) params.set("subject", filters.subject.trim());
    if (filters.grade.trim()) params.set("grade", filters.grade.trim());
    if (filters.district.trim()) params.set("district", filters.district.trim());
    const query = params.toString();
    setTutors(null);
    apiFetch<TutorCard[]>(`/api/public/tutors${query ? `?${query}` : ""}`)
      .then(setTutors)
      .catch((e: unknown) => {
        setTutors([]);
        toast.error(e instanceof Error ? e.message : "Could not load tutors");
      });
  };

  useEffect(() => {
    loadTutors({ subject: "", grade: "", district: "" });
    apiFetch<PublicBatch[]>("/api/public/batches")
      .then(setBatches)
      .catch((e: unknown) => {
        setBatches([]);
        toast.error(e instanceof Error ? e.message : "Could not load batches");
      });
    apiFetch<Child[]>("/api/parent/children")
      .then(setChildren)
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load children"));
  }, []);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadTutors({ subject, grade, district });
  };

  const requestEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId || !batchId) {
      toast.error("Choose a child and a batch");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/api/enrollments/request", {
        method: "POST",
        body: { student_id: Number(studentId), batch_id: Number(batchId) },
      });
      toast.success("Enrollment requested. The tutor will review it.");
      setBatchId("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not request enrollment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Find tutors</h1>
        <p className="text-sm text-slate-500">Search tutors and batches, then request a seat for your child.</p>
      </div>

      <Card>
        <form onSubmit={onSearch} className="grid gap-3 sm:grid-cols-4">
          <Field label="Subject">
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Maths" />
          </Field>
          <Field label="Grade">
            <Input value={grade} onChange={(e) => setGrade(e.target.value)} placeholder="e.g. 10" />
          </Field>
          <Field label="District">
            <Input value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="e.g. Chennai" />
          </Field>
          <div className="flex items-end">
            <Button type="submit" variant="primary">Search</Button>
          </div>
        </form>
      </Card>

      <section className="space-y-3">
        <h2 className="font-manrope text-lg font-semibold">Tutors</h2>
        {tutors === null ? (
          <div className="grid gap-4 md:grid-cols-2">
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
        ) : tutors.length === 0 ? (
          <Empty>No tutors match these filters.</Empty>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {tutors.map((t) => (
              <Card key={t.id}>
                <h3 className="font-manrope text-base font-semibold">{t.tuition_name}</h3>
                <p className="text-sm text-slate-600">{t.display_name}</p>
                <p className="mt-2 text-sm">District: {t.district}</p>
                <p className="text-sm">Subjects: {listText(t.subjects)}</p>
                <p className="text-sm">Grades: {listText(t.grades)}</p>
                <div className="mt-2">
                  <Badge>{t.teaching_mode}</Badge>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-manrope text-lg font-semibold">Batches</h2>
        {batches === null ? (
          <Skeleton className="h-32" />
        ) : batches.length === 0 ? (
          <Empty>No batches are open right now.</Empty>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {batches.map((b) => (
              <Card key={b.id}>
                <h3 className="font-manrope text-base font-semibold">{b.name}</h3>
                <p className="text-sm text-slate-600">{b.course_label} by {b.tutor_name}</p>
                <p className="mt-2 text-sm">Fee: {money(b.monthly_fee_paise)} per month</p>
                <p className="text-sm">Seats left: {b.seats_left}</p>
                <p className="text-sm">Mode: {b.teaching_mode}</p>
                <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
                  {b.schedules.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        )}
      </section>

      <Card>
        <h2 className="font-manrope text-lg font-semibold">Request enrollment</h2>
        {children.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">Add a child first, then request a batch for them.</p>
        ) : (
          <form onSubmit={requestEnrollment} className="mt-3 grid gap-3 sm:grid-cols-3">
            <Field label="Child">
              <Select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
                <option value="">Select a child</option>
                {children.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </Select>
            </Field>
            <Field label="Batch">
              <Select value={batchId} onChange={(e) => setBatchId(e.target.value)}>
                <option value="">Select a batch</option>
                {(batches ?? []).map((b) => (
                  <option key={b.id} value={b.id}>{b.name} ({b.tutor_name})</option>
                ))}
              </Select>
            </Field>
            <div className="flex items-end">
              <Button type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Requesting..." : "Request enrollment"}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
