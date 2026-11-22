import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import Logo from "../components/Logo";
import { Button, Card, Field, Input, Select } from "../components/ui";
import { apiFetch, setSession } from "../lib/api";
import type { TokenOut } from "../lib/types";

const TEACHING_MODES = ["offline", "online", "hybrid"] as const;

const initialForm = {
  name: "",
  phone: "",
  password: "",
  confirm_password: "",
  tuition_name: "",
  door_no: "",
  street: "",
  district: "",
  pin_code: "",
  state: "",
  subjects: "",
  grades: "",
  teaching_timings: "",
  teaching_mode: "offline",
  upi_id: "",
};

type TutorForm = typeof initialForm;

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
  tuition_name: z.string().trim().min(1, "Enter your tuition name"),
  door_no: z.string().trim().min(1, "Enter the door number"),
  street: z.string().trim().min(1, "Enter the street"),
  district: z.string().trim().min(1, "Enter the district"),
  pin_code: z.string().regex(/^\d{6}$/, "PIN code must be 6 digits"),
  state: z.string().trim().min(1, "Enter the state"),
  subjects: z.string().refine((value) => splitList(value).length > 0, "Enter at least one subject"),
  grades: z.string().refine((value) => splitList(value).length > 0, "Enter at least one grade"),
  teaching_timings: z.string().trim().min(1, "Enter your teaching timings"),
  teaching_mode: z.enum(TEACHING_MODES, { errorMap: () => ({ message: "Choose a teaching mode" }) }),
  upi_id: z.string(),
});

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function TutorRegister() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
  const [form, setForm] = useState<TutorForm>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function setField(key: keyof TutorForm) {
    return (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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

    const body: Record<string, unknown> = {
      name: form.name.trim(),
      phone: form.phone,
      password: form.password,
      confirm_password: form.confirm_password,
      tuition_name: form.tuition_name.trim(),
      door_no: form.door_no.trim(),
      street: form.street.trim(),
      district: form.district.trim(),
      pin_code: form.pin_code,
      state: form.state.trim(),
      subjects: splitList(form.subjects),
      grades: splitList(form.grades),
      teaching_timings: form.teaching_timings.trim(),
      teaching_mode: form.teaching_mode,
    };
    if (form.upi_id.trim()) {
      body.upi_id = form.upi_id.trim();
    }

    setSubmitting(true);
    try {
      const res = await apiFetch<TokenOut>("/auth/register/tutor", {
        method: "POST",
        body,
      });
      setSession(res.access_token, res.role);
      navigate("/tutor", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-brand-cream px-4 py-10 text-ink">
      <Logo />
      <Card className="mt-8 w-full max-w-xl">
        <div className="flex items-center justify-between gap-4">
          <h1 className="font-manrope text-xl font-bold">Register as a tutor</h1>
          <span className="text-sm font-medium text-muted">Step {step} of 2</span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-line" aria-hidden="true">
          <div
            className="h-full bg-brand-green transition-all"
            style={{ width: step === 1 ? "50%" : "100%" }}
          />
        </div>

        {step === 1 ? (
          <form onSubmit={handleStep1} className="mt-6 space-y-4" noValidate>
            <h2 className="font-manrope text-base font-semibold">Your account</h2>
            <Field label="Full name">
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
              <Button type="submit">Next</Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <h2 className="font-manrope text-base font-semibold">Your tuition</h2>
            <Field label="Tuition name">
              <Input value={form.tuition_name} onChange={setField("tuition_name")} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Door no.">
                <Input value={form.door_no} onChange={setField("door_no")} />
              </Field>
              <Field label="Street">
                <Input value={form.street} onChange={setField("street")} />
              </Field>
              <Field label="District">
                <Input value={form.district} onChange={setField("district")} />
              </Field>
              <Field label="PIN code">
                <Input
                  inputMode="numeric"
                  maxLength={6}
                  value={form.pin_code}
                  onChange={setField("pin_code")}
                />
              </Field>
              <Field label="State">
                <Input value={form.state} onChange={setField("state")} />
              </Field>
              <Field label="Teaching mode">
                <Select value={form.teaching_mode} onChange={setField("teaching_mode")}>
                  {TEACHING_MODES.map((mode) => (
                    <option key={mode} value={mode}>
                      {mode.charAt(0).toUpperCase() + mode.slice(1)}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <Field label="Subjects (comma-separated)">
              <Input
                placeholder="Maths, Science, English"
                value={form.subjects}
                onChange={setField("subjects")}
              />
            </Field>
            <Field label="Grades (comma-separated)">
              <Input
                placeholder="6, 7, 8"
                value={form.grades}
                onChange={setField("grades")}
              />
            </Field>
            <Field label="Teaching timings">
              <Input
                placeholder="Mon-Fri 4pm to 7pm"
                value={form.teaching_timings}
                onChange={setField("teaching_timings")}
              />
            </Field>
            <Field label="UPI ID (optional)">
              <Input
                placeholder="name@bank"
                value={form.upi_id}
                onChange={setField("upi_id")}
              />
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
              <Button type="submit" disabled={submitting}>
                {submitting ? "Creating account..." : "Create account"}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
