import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";
import Logo from "../components/Logo";
import { Button, Card, Field, Input } from "../components/ui";
import { apiFetch, setSession } from "../lib/api";
import type { TokenOut } from "../lib/types";

const loginSchema = z.object({
  phone: z.string().regex(/^\d{10}$/, "Enter a 10-digit phone number"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedRole = searchParams.get("role") === "tutor" ? "tutor" : searchParams.get("role") === "parent" ? "parent" : null;
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginForm) {
    setServerError(null);
    try {
      const res = await apiFetch<TokenOut>("/auth/login", {
        method: "POST",
        body: { phone: values.phone, password: values.password, role: selectedRole },
      });
      setSession(res.access_token, res.role);
      navigate(res.role === "tutor" ? "/tutor" : "/parent", { replace: true });
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center overflow-hidden bg-[#f7f9f5] px-4 py-10 text-ink">
      <style>{`
        @keyframes auth-card-in { from { opacity: 0; transform: translateY(18px) scale(.985); } to { opacity: 1; transform: none; } }
        .auth-card-in { animation: auth-card-in .55s cubic-bezier(.2,.8,.2,1) both; }
        @media (prefers-reduced-motion: reduce) { .auth-card-in { animation: none; } }
      `}</style>
      <div className="pointer-events-none absolute -left-24 top-20 h-72 w-72 rounded-full bg-brand-green/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-10 h-80 w-80 rounded-full bg-brand-blue/15 blur-3xl" />
      <div className="auth-card-in relative z-10 rounded-2xl border border-white/70 bg-white/75 px-5 py-3 shadow-[0_12px_40px_rgba(31,41,55,.12)] backdrop-blur-xl">
        <Logo size={32} />
      </div>
      <Card className="auth-card-in relative z-10 mt-6 w-full max-w-md border-white/70 bg-white/85 shadow-[0_24px_70px_rgba(31,41,55,.16)] backdrop-blur-xl">
        <h1 className="font-manrope text-xl font-bold">Log in to TeachMan</h1>
        <p className="mt-1 text-sm text-muted">
          {selectedRole === "tutor" ? "Tutor login" : selectedRole === "parent" ? "Student / Parent login" : "Use your registered phone number and password."}
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          <Field label="Phone number">
            <Input
              type="tel"
              inputMode="numeric"
              maxLength={10}
              placeholder="10-digit mobile number"
              autoComplete="username"
              {...register("phone")}
            />
          </Field>
          {errors.phone && <p className="text-sm text-danger">{errors.phone.message}</p>}

          <Field label="Password">
            <Input
              type="password"
              placeholder="At least 8 characters"
              autoComplete="current-password"
              {...register("password")}
            />
          </Field>
          {errors.password && <p className="text-sm text-danger">{errors.password.message}</p>}

          {serverError && (
            <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
              {serverError}
            </div>
          )}

          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? "Logging in..." : "Log in"}
          </Button>
        </form>

        <div className="mt-6 space-y-2 text-center text-sm text-muted">
          <p>
            New tutor?{" "}
            <Link to="/register/tutor" className="font-semibold text-brand-green hover:underline">
              Register as a tutor
            </Link>
          </p>
          <p>
            New parent or student?{" "}
            <Link to="/register/parent" className="font-semibold text-brand-blue hover:underline">
              Register as a parent
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}
