import { useState } from "react";
import { Link } from "react-router-dom";
import Logo from "../components/Logo";

export default function Landing() {
  const [role, setRole] = useState<"tutor" | "parent" | null>(null);

  return (
    <div className="min-h-screen overflow-hidden bg-[#071711] text-ink">
      <style>{`
        @keyframes ds-brand-in { from { opacity: 0; transform: scale(.96) translateY(12px); } to { opacity: 1; transform: none; } }
        @keyframes ds-panel-in { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
        @keyframes ds-float { 0%,100% { transform: translate3d(0,0,0); } 50% { transform: translate3d(0,-10px,0); } }
        .ds-brand-in { animation: ds-brand-in .7s cubic-bezier(.2,.8,.2,1) both; }
        .ds-panel-in { animation: ds-panel-in .65s cubic-bezier(.2,.8,.2,1) both; }
        .ds-float { animation: ds-float 7s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) { .ds-brand-in,.ds-panel-in,.ds-float { animation: none; } }
      `}</style>
      <main className="relative grid min-h-screen md:grid-cols-2">
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-10 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/10 blur-3xl" />
        <section className={`ds-panel-in relative min-h-[50vh] overflow-hidden transition-all duration-700 md:min-h-screen ${role === "parent" ? "md:translate-x-[-8%] md:scale-[.92]" : role === "tutor" ? "md:translate-x-0" : ""}`}>
          <img src="/images/teacher-and-student.jfif" alt="Tutor managing a teaching session" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#071711] via-[#071711]/55 to-transparent" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(52,211,153,.18),transparent_32%)]" />
          <div className="relative flex h-full flex-col justify-end p-6 pb-10 text-white md:p-12 md:pb-16">
            <p className="mb-2 text-sm font-semibold uppercase tracking-[.18em] text-emerald-200">Tutor</p>
            <h2 className="font-manrope text-2xl font-bold md:text-4xl">Manage your teaching business smarter.</h2>
            <div className="mt-6 flex flex-wrap gap-3">
              {role === "tutor" ? (
                <>
                  <Link to="/register/tutor" className="rounded-lg bg-white px-5 py-3 text-sm font-bold text-[#071711]">Register</Link>
                  <Link to="/login?role=tutor" className="rounded-lg border border-white/70 px-5 py-3 text-sm font-bold text-white">Login</Link>
                  <button type="button" onClick={() => setRole(null)} className="px-3 py-3 text-sm font-semibold text-white/80">Back</button>
                </>
              ) : (
                <button type="button" onClick={() => setRole("tutor")} className="rounded-lg bg-brand-green px-5 py-3 text-sm font-bold text-white">Continue as Tutor</button>
              )}
            </div>
          </div>
        </section>

        <section className={`ds-panel-in relative min-h-[50vh] overflow-hidden transition-all duration-700 md:min-h-screen ${role === "tutor" ? "md:translate-x-[8%] md:scale-[.92]" : role === "parent" ? "md:translate-x-0" : ""}`}>
          <img src="/images/student.jfif" alt="Student learning with support" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#08263A] via-[#08263A]/55 to-transparent" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(56,189,248,.18),transparent_32%)]" />
          <div className="relative flex h-full flex-col justify-end p-6 pb-10 text-white md:p-12 md:pb-16">
            <p className="mb-2 text-sm font-semibold uppercase tracking-[.18em] text-sky-200">Student / Parent</p>
            <h2 className="font-manrope text-2xl font-bold md:text-4xl">Find the right tutor and manage your learning journey.</h2>
            <div className="mt-6 flex flex-wrap gap-3">
              {role === "parent" ? (
                <>
                  <Link to="/register/parent" className="rounded-lg bg-white px-5 py-3 text-sm font-bold text-[#08263A]">Register</Link>
                  <Link to="/login?role=parent" className="rounded-lg border border-white/70 px-5 py-3 text-sm font-bold text-white">Login</Link>
                  <button type="button" onClick={() => setRole(null)} className="px-3 py-3 text-sm font-semibold text-white/80">Back</button>
                </>
              ) : (
                <button type="button" onClick={() => setRole("parent")} className="rounded-lg bg-brand-blue px-5 py-3 text-sm font-bold text-white">Continue as Student / Parent</button>
              )}
            </div>
          </div>
        </section>

        <div className="ds-brand-in ds-float pointer-events-none absolute left-1/2 top-6 z-30 -translate-x-1/2 rounded-2xl border border-white/30 bg-white/90 px-5 py-2 shadow-[0_12px_40px_rgba(15,23,42,.24)] backdrop-blur-xl md:top-8">
          <Logo size={32} />
        </div>
      </main>
    </div>
  );
}
