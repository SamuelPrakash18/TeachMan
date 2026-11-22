import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Card, Button, Field, Input, Badge, Empty, Skeleton, Modal, useToast } from "../../components/ui";

type AccountSettings = {
  phone: string;
  role: string;
  display_name: string;
  public_id: string;
};

type DeletionPreview = {
  retention_notice: string;
  [key: string]: string | number | boolean | null;
};

const CONFIRM_PHRASE = "DELETE MY ACCOUNT";

const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function Settings() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<AccountSettings | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [savingName, setSavingName] = useState(false);

  const [preview, setPreview] = useState<DeletionPreview | null>(null);
  const [password, setPassword] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [phrase, setPhrase] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    apiFetch<AccountSettings>("/api/account/settings")
      .then((s) => {
        setSettings(s);
        setDisplayName(s.display_name);
      })
      .catch((e) => toast(errMsg(e), "error"));
    apiFetch<DeletionPreview>("/api/account/deletion-preview")
      .then((p) => setPreview(p))
      .catch((e) => toast(errMsg(e), "error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    setSavingName(true);
    try {
      const s = await apiFetch<AccountSettings>("/api/account/settings", {
        method: "PUT",
        body: { display_name: displayName },
      });
      setSettings(s);
      toast("Display name updated", "success");
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setSavingName(false);
    }
  }

  function closeDeleteFlow() {
    setDeleteOpen(false);
    setStep(1);
    setPassword("");
    setPhrase("");
  }

  async function requestDeletion() {
    setRequesting(true);
    try {
      await apiFetch("/api/account/deletion-request", { method: "POST", body: { password } });
      toast("Deletion requested. Confirm to continue.", "success");
      setStep(2);
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setRequesting(false);
    }
  }

  async function confirmDeletion() {
    setConfirming(true);
    try {
      await apiFetch("/api/account/deletion-request/confirm", {
        method: "POST",
        body: { password, confirmation_phrase: phrase },
      });
      toast("Account deletion confirmed", "success");
      closeDeleteFlow();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setConfirming(false);
    }
  }

  async function cancelDeletion() {
    setCancelling(true);
    try {
      await apiFetch("/api/account/deletion-request/cancel", { method: "POST" });
      toast("Deletion request cancelled", "success");
      closeDeleteFlow();
    } catch (err) {
      toast(errMsg(err), "error");
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-manrope text-2xl font-bold">Settings</h1>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold">Account</h2>
        {settings === null ? (
          <Skeleton className="h-24" />
        ) : (
          <div className="space-y-4">
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="text-slate-500">Phone</dt>
              <dd>{settings.phone}</dd>
              <dt className="text-slate-500">Role</dt>
              <dd className="capitalize">{settings.role}</dd>
              <dt className="text-slate-500">Public ID</dt>
              <dd className="break-all">{settings.public_id}</dd>
            </dl>
            <form onSubmit={saveName} className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
              <Field label="Display name">
                <Input required value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
              </Field>
              <Button type="submit" disabled={savingName}>
                {savingName ? "Saving..." : "Save name"}
              </Button>
            </form>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="font-manrope mb-3 text-lg font-semibold text-red-700">Delete account</h2>
        {preview === null ? (
          <Skeleton className="h-24" />
        ) : (
          <div className="space-y-4">
            <dl className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(preview)
                .filter(([k, v]) => k !== "retention_notice" && (typeof v === "number" || typeof v === "boolean"))
                .map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="text-slate-500">{k.replace(/_/g, " ")}</dt>
                    <dd>{String(v)}</dd>
                  </div>
                ))}
            </dl>
            <p className="rounded-md bg-slate-50 p-3 text-sm">{preview.retention_notice}</p>
            {!deleteOpen && (
              <Button variant="danger" onClick={() => setDeleteOpen(true)}>
                Start account deletion
              </Button>
            )}
            {deleteOpen && step === 1 && (
              <div className="space-y-3 rounded-md border p-4">
                <Field label="Password">
                  <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </Field>
                <div className="flex flex-wrap justify-end gap-2">
                  <Button variant="secondary" onClick={closeDeleteFlow}>
                    Cancel
                  </Button>
                  <Button variant="danger" disabled={requesting || !password} onClick={requestDeletion}>
                    {requesting ? "Requesting..." : "Request deletion"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      <Modal open={deleteOpen && step === 2} onClose={closeDeleteFlow} title="Confirm account deletion">
        <div className="space-y-4">
          <p className="text-sm">
            This is the final step. To confirm, type <strong>{CONFIRM_PHRASE}</strong> exactly as shown.
          </p>
          <Field label="Confirmation phrase">
            <Input value={phrase} onChange={(e) => setPhrase(e.target.value)} />
          </Field>
          <div className="flex flex-wrap justify-end gap-2">
            <Button onClick={cancelDeletion} disabled={cancelling}>
              {cancelling ? "Cancelling..." : "Cancel deletion"}
            </Button>
            <Button
              variant="danger"
              disabled={confirming || phrase !== CONFIRM_PHRASE}
              onClick={confirmDeletion}
            >
              {confirming ? "Deleting..." : "Permanently delete my account"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
