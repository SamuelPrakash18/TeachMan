import { useEffect, useState } from "react";
import { apiFetch, money } from "../../lib/api";
import { Card, Button, Field, Input, Skeleton, useToast } from "../../components/ui";

interface AccountSettings {
  phone: string;
  role: string;
  display_name: string;
  public_id: string;
}

interface DeletionPreview {
  children_count: number;
  outstanding_paise: number;
  overdue_count: number;
  pending_claims: number;
  requested_enrollments: number;
  retention_notice: string;
}

const CONFIRM_PHRASE = "DELETE MY ACCOUNT";

export default function Settings() {
  const toast = useToast();
  const [settings, setSettings] = useState<AccountSettings | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [savingName, setSavingName] = useState(false);

  const [preview, setPreview] = useState<DeletionPreview | null>(null);
  const [password, setPassword] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [deletionRequested, setDeletionRequested] = useState(false);
  const [phrase, setPhrase] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    apiFetch<AccountSettings>("/api/account/settings")
      .then((s) => {
        setSettings(s);
        setDisplayName(s.display_name);
      })
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load settings"));

    apiFetch<DeletionPreview>("/api/account/deletion-preview")
      .then(setPreview)
      .catch((e: unknown) => toast.error(e instanceof Error ? e.message : "Could not load deletion preview"));
  }, []);

  const saveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim()) {
      toast.error("Display name cannot be empty");
      return;
    }
    setSavingName(true);
    try {
      const updated = await apiFetch<AccountSettings>("/api/account/settings", {
        method: "PUT",
        body: { display_name: displayName.trim() },
      });
      setSettings(updated);
      setDisplayName(updated.display_name);
      toast.success("Display name updated");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not update settings");
    } finally {
      setSavingName(false);
    }
  };

  const requestDeletion = async () => {
    if (!password) {
      toast.error("Enter your password");
      return;
    }
    setRequesting(true);
    try {
      await apiFetch("/api/account/deletion-request", { method: "POST", body: { password } });
      setDeletionRequested(true);
      toast.success("Deletion requested. Confirm below to finish.");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not request deletion");
    } finally {
      setRequesting(false);
    }
  };

  const confirmDeletion = async () => {
    if (phrase !== CONFIRM_PHRASE) {
      toast.error(`Type ${CONFIRM_PHRASE} exactly to confirm`);
      return;
    }
    setConfirming(true);
    try {
      await apiFetch("/api/account/deletion-request/confirm", {
        method: "POST",
        body: { password, confirmation_phrase: phrase },
      });
      toast.success("Your account has been deactivated.");
      setDeletionRequested(false);
      setPhrase("");
      setPassword("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not confirm deletion");
    } finally {
      setConfirming(false);
    }
  };

  const cancelDeletion = async () => {
    setCancelling(true);
    try {
      await apiFetch("/api/account/deletion-request/cancel", { method: "POST" });
      toast.success("Deletion request cancelled");
      setDeletionRequested(false);
      setPhrase("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not cancel deletion request");
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">Profile</h1>
        <p className="text-sm text-slate-500">Manage your profile and account.</p>
      </div>

      {settings === null ? (
        <Skeleton className="h-40" />
      ) : (
        <Card>
          <h2 className="font-manrope text-lg font-semibold">Profile</h2>
          <div className="mt-2 grid gap-1 text-sm text-slate-600">
            <p>Phone: {settings.phone}</p>
            <p>Role: {settings.role}</p>
            <p>Public ID: {settings.public_id}</p>
          </div>
          <form onSubmit={saveName} className="mt-4 grid gap-3 sm:grid-cols-3">
            <Field label="Display name">
              <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
            </Field>
            <div className="flex items-end">
              <Button type="submit" variant="primary" disabled={savingName}>
                {savingName ? "Saving..." : "Save name"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="font-manrope text-lg font-semibold text-red-700">Delete account</h2>
        {preview === null ? (
          <Skeleton className="mt-3 h-24" />
        ) : (
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            <p>Children linked to this account: {preview.children_count}</p>
            <p>Outstanding fees: {money(preview.outstanding_paise)}</p>
            <p>Overdue invoices: {preview.overdue_count}</p>
            <p>Pending payment claims: {preview.pending_claims}</p>
            <p>Requested enrollments: {preview.requested_enrollments}</p>
            <p className="rounded bg-slate-50 p-3">{preview.retention_notice}</p>
          </div>
        )}

        {!deletionRequested ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Field label="Password">
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <div className="flex items-end">
              <Button variant="danger" onClick={requestDeletion} disabled={requesting}>
                {requesting ? "Requesting..." : "Request account deletion"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-slate-600">
              A deletion request is open. To finish, type <strong>{CONFIRM_PHRASE}</strong> exactly and confirm.
              You can cancel the request at any time.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label={`Type ${CONFIRM_PHRASE}`}>
                <Input value={phrase} onChange={(e) => setPhrase(e.target.value)} />
              </Field>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="primary" onClick={cancelDeletion} disabled={cancelling}>
                {cancelling ? "Cancelling..." : "Cancel request"}
              </Button>
              <Button
                variant="danger"
                onClick={confirmDeletion}
                disabled={confirming || phrase !== CONFIRM_PHRASE}
              >
                {confirming ? "Deleting..." : "Confirm deletion"}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
