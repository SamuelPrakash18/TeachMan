import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import Logo from "../components/Logo";
import { Button, Card, Field, Input } from "../components/ui";
import { apiFetch, setSession } from "../lib/api";
import type { TokenOut } from "../lib/types";

const initialForm = {
  name: "",
  phone: "",
  password: "",
  confirm_password: "",
  student_name: "",
  student_grade: "",
  student_address: "",
};

type ParentForm = typeof initialForm;

const step1Schema = z
  .object({
    name: z.string().trim().min(2, "Enter your name"),
    phone: z.string().regex(/^\d{10}$/, "Phone number must be 10 digits"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

const step2Schema = z.object({
  student_name: z.string().trim().min(1, "Enter the student's name"),
  student_grade: z.string().trim().min(1, "Enter the student's grade"),
  student_address: z.string().trim().min(1, "Enter the student's address"),
});

export default function ParentRegister() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
  const [form, setForm] = useState<ParentForm>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function setField(key: keyof ParentForm) {
    return (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setForm((prev) => ({ ...prev, [key]: value }));
    };
  }

  function handleStep1(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = step1Schema.safeParse(form);
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Please check the form");
      return;
    }
    setError(null);
    setStep(2);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = step2Schema.safeParse(form);
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Please check the form");
      return;
    }
    setError(null);

    setSubmitting(true);
    try {
      const res = await apiFetch<TokenOut>("/auth/register/parent", {
        method: "POST",
        body: {
          name: form.name.trim(),
          phone: form.phone,
          password: form.password,
          confirm_password: form.confirm_password,
          student_name: form.student_name.trim(),
          student_grade: form.student_grade.trim(),
          student_address: form.student_address.trim(),
        },
      });
      setSession(res.access_token, res.role);
      navigate("/parent", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center overflow-hidden bg-[#f7f9f5] px-4 py-10 text-ink">
      <style>{`
        @keyframes auth-card-in { from { opacity: 0; transform: translateY(18px) scale(.985); } to { opacity: 1; transform: none; } }
        .auth-card-in { animation: auth-card-in .55s cubic-bezier(.2,.8,.2,1) both; }
        @media (prefers-reduced-motion: reduce) { .auth-card-in { animation: none; } }
      `}</style>
      <div className="pointer-events-none absolute -left-24 top-16 h-72 w-72 rounded-full bg-brand-blue/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-10 h-80 w-80 rounded-full bg-brand-green/12 blur-3xl" />
      <div className="auth-card-in relative z-10 rounded-2xl border border-white/70 bg-white/75 px-5 py-3 shadow-[0_12px_40px_rgba(31,41,55,.12)] backdrop-blur-xl">
        <Logo size={32} />
      </div>
      <Card className="auth-card-in relative z-10 mt-6 w-full max-w-md border-white/70 bg-white/85 shadow-[0_24px_70px_rgba(31,41,55,.16)] backdrop-blur-xl">
        <div className="flex items-center justify-between gap-4">
          <h1 className="font-manrope text-xl font-bold">Register as a parent</h1>
          <span className="text-sm font-medium text-muted">Step {step} of 2</span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-line" aria-hidden="true">
          <div
            className="h-full bg-brand-blue transition-all"
            style={{ width: step === 1 ? "50%" : "100%" }}
          />
        </div>

        {step === 1 ? (
          <form onSubmit={handleStep1} className="mt-6 space-y-4" noValidate>
            <h2 className="font-manrope text-base font-semibold">Your account</h2>
            <Field label="Your name">
              <Input value={form.name} onChange={setField("name")} autoComplete="name" />
            </Field>
            <Field label="Phone number">
              <Input
                type="tel"
                inputMode="numeric"
                maxLength={10}
                value={form.phone}
                onChange={setField("phone")}
                autoComplete="tel"
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                value={form.password}
                onChange={setField("password")}
                autoComplete="new-password"
              />
            </Field>
            <Field label="Confirm password">
              <Input
                type="password"
                value={form.confirm_password}
                onChange={setField("confirm_password")}
                autoComplete="new-password"
              />
            </Field>

            {error && (
              <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
                {error}
              </div>
            )}

            <div className="flex items-center justify-between gap-3 pt-2">
              <Link to="/login" className="text-sm font-medium text-brand-blue hover:underline">
                Already registered? Log in
              </Link>
              <Button type="submit" variant="secondary">
                Next
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <h2 className="font-manrope text-base font-semibold">Student details</h2>
            <Field label="Student's name">
              <Input value={form.student_name} onChange={setField("student_name")} />
            </Field>
            <Field label="Student's grade">
              <Input
                placeholder="e.g. 8"
                value={form.student_grade}
                onChange={setField("student_grade")}
              />
            </Field>
            <Field label="Student's address">
              <Input value={form.student_address} onChange={setField("student_address")} />
            </Field>

            {error && (
              <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
                {error}
              </div>
            )}

            <div className="flex items-center justify-between gap-3 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setError(null);
                  setStep(1);
                }}
              >
                Back
              </Button>
              <Button type="submit" variant="secondary" disabled={submitting}>
                {submitting ? "Creating account..." : "Create account"}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
