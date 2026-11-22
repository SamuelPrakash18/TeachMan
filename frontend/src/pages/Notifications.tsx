import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Empty, Skeleton, useToast } from "../components/ui";
import { apiFetch } from "../lib/api";

interface NotificationItem {
  id: string;
  title: string;
  body: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
}

type NotificationsResponse = NotificationItem[] | { items: NotificationItem[] };

function normalise(res: NotificationsResponse | null | undefined): NotificationItem[] {
  if (Array.isArray(res)) {
    return res;
  }
  if (res && Array.isArray(res.items)) {
    return res.items;
  }
  return [];
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export default function Notifications() {
  const toast = useToast();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch<NotificationsResponse>("/notifications");
        if (!cancelled) {
          setItems(normalise(res));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load notifications");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function markRead(id: string) {
    setBusyId(id);
    try {
      await apiFetch(`/notifications/${id}/read`, { method: "PUT" });
      setItems((prev) =>
        prev.map((item) => (item.id === id ? { ...item, is_read: true } : item)),
      );
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not mark as read", "error");
    } finally {
      setBusyId(null);
    }
  }

  const unreadCount = items.filter((item) => !item.is_read).length;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="font-manrope text-xl font-bold text-ink">Notifications</h1>
        {!loading && !error && (
          <p className="mt-1 text-sm text-muted">
            {unreadCount} unread {unreadCount === 1 ? "notification" : "notifications"}
          </p>
        )}
      </div>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {!loading && error && (
        <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <Empty title="No notifications yet" text="New updates will appear here." />
      )}

      {!loading &&
        !error &&
        items.map((item) => (
          <Card key={item.id} className={item.is_read ? "" : "border-brand-blue/40"}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  {!item.is_read && <Badge tone="info">New</Badge>}
                  <h2 className="font-manrope text-base font-semibold text-ink">{item.title}</h2>
                </div>
                <p className="text-sm text-muted">{item.body}</p>
                <p className="text-xs text-muted">{formatTime(item.created_at)}</p>
                {item.link && (
                  <Link to={item.link} className="text-sm font-semibold text-brand-blue hover:underline">
                    View details
                  </Link>
                )}
              </div>
              {!item.is_read && (
                <Button
                  variant="ghost"
                  className="shrink-0 px-3 py-1.5"
                  disabled={busyId === item.id}
                  onClick={() => markRead(item.id)}
                >
                  Mark read
                </Button>
              )}
            </div>
          </Card>
        ))}
    </div>
  );
}
