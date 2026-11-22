import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, money } from "../../lib/api";
import { Card, Button, Stat, Skeleton, useToast } from "../../components/ui";

interface DashboardData {
  parent_name: string;
  children_count: number;
  outstanding_paise: number;
  overdue_count: number;
  pending_claims_count: number;
  pending_enrollments_count: number;
  next_due_date: string | null;
}

export default function Home() {
  const toast = useToast();
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    apiFetch<DashboardData>("/api/parent/dashboard")
      .then(setData)
      .catch((e: unknown) =>
        toast.error(e instanceof Error ? e.message : "Could not load dashboard")
      );
  }, []);

  if (!data) {
    return (
      <div className="space-y-6">
        <h1 className="font-manrope text-2xl font-bold">Welcome</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Welcome, {data.parent_name}</h1>
        <p className="text-sm text-slate-500">A summary of your children's classes and fees.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <Stat label="Children" value={String(data.children_count)} />
        </Card>
        <Card>
          <Stat label="Outstanding fees" value={money(data.outstanding_paise)} />
        </Card>
        <Card>
          <Stat label="Overdue invoices" value={String(data.overdue_count)} />
        </Card>
        <Card>
          <Stat label="Pending payment claims" value={String(data.pending_claims_count)} />
        </Card>
        <Card>
          <Stat label="Pending enrollments" value={String(data.pending_enrollments_count)} />
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Next due date</p>
          <p className="font-manrope text-xl font-semibold">
            {data.next_due_date ? data.next_due_date : "No upcoming dues"}
          </p>
        </Card>
      </div>

      <Card>
        <h2 className="font-manrope text-lg font-semibold">Quick links</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link to="/parent/fees">
            <Button variant="primary">View fees and pay</Button>
          </Link>
          <Link to="/parent/children">
            <Button variant="secondary">Manage children</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
