import { Link } from "react-router-dom";
import Logo from "../components/Logo";
import { Card } from "../components/ui";

const benefits = [
  {
    title: "Know who owes you",
    text: "See every invoice, partial payment and overdue balance at a glance.",
  },
  {
    title: "Plan cash for 30, 60 and 90 days",
    text: "Forecast incoming fees and expenses so you always know what's coming.",
  },
  {
    title: "Parents pay and track fees online",
    text: "Families see their invoices and pay by UPI, with every payment recorded.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-brand-cream text-ink">
      <style>{`
        @keyframes tm-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
        .tm-fade-in { animation: tm-fade-in 0.6s ease-out both; }
      `}</style>

      <header className="mx-auto flex max-w-5xl items-center px-6 py-6">
        <Logo />
      </header>

      <main className="tm-fade-in mx-auto max-w-5xl px-6 pb-16 pt-6 md:pt-12">
        <h1 className="font-manrope text-3xl font-bold leading-tight sm:text-4xl md:text-5xl">
          Teach smarter. Manage better. Stay financially ahead.
        </h1>
        <p className="mt-4 max-w-2xl text-base text-muted md:text-lg">
          TeachMan helps tutors track students, fees, UPI payments and cash flow in one place.
          Parents get a simple view of classes, invoices and progress without the back-and-forth.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {benefits.map((benefit) => (
            <Card key={benefit.title}>
              <h2 className="font-manrope text-base font-semibold text-ink">{benefit.title}</h2>
              <p className="mt-2 text-sm text-muted">{benefit.text}</p>
            </Card>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 sm:flex-row">
          <Link
            to="/register/tutor"
            className="inline-flex items-center justify-center rounded-lg bg-brand-green px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-green/90"
          >
            Continue as Tutor
          </Link>
          <Link
            to="/register/parent"
            className="inline-flex items-center justify-center rounded-lg border-2 border-brand-blue bg-white px-6 py-3 text-sm font-semibold text-brand-blue transition hover:bg-brand-blue/5"
          >
            Continue as Parent / Student
          </Link>
        </div>

        <p className="mt-6 text-sm text-muted">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brand-blue hover:underline">
            Log in
          </Link>
        </p>
      </main>
    </div>
  );
}
