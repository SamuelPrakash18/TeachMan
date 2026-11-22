import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Child } from "../../lib/types";
import { Card, Button, Field, Input, Textarea, Empty, Skeleton, Modal, useToast } from "../../components/ui";

interface ChildForm {
  name: string;
  grade: string;
  address: string;
}

const emptyForm: ChildForm = { name: "", grade: "", address: "" };

export default function Children() {
  const toast = useToast();
  const [children, setChildren] = useState<Child[] | null>(null);
  const [form, setForm] = useState<ChildForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Child | null>(null);
  const [editForm, setEditForm] = useState<ChildForm>(emptyForm);
  const [editSaving, setEditSaving] = useState(false);

  const load = () => {
    apiFetch<Child[]>("/api/parent/children")
      .then(setChildren)
      .catch((e: unknown) => {
        setChildren([]);
        toast.error(e instanceof Error ? e.message : "Could not load children");
      });
  };

  useEffect(() => {
    load();
  }, []);

  const addChild = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error("Child's name is required");
      return;
    }
    setSaving(true);
    try {
      await apiFetch("/api/parent/children", {
        method: "POST",
        body: { name: form.name.trim(), grade: form.grade.trim(), address: form.address.trim() },
      });
      toast.success("Child added");
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not add child");
    } finally {
      setSaving(false);
    }
  };

  const openEdit = (child: Child) => {
    setEditing(child);
    setEditForm({ name: child.name, grade: String(child.grade ?? ""), address: child.address ?? "" });
  };

  const saveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    if (!editForm.name.trim()) {
      toast.error("Child's name is required");
      return;
    }
    setEditSaving(true);
    try {
      await apiFetch(`/api/parent/children/${editing.id}`, {
        method: "PUT",
        body: { name: editForm.name.trim(), grade: editForm.grade.trim(), address: editForm.address.trim() },
      });
      toast.success("Child updated");
      setEditing(null);
      load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not update child");
    } finally {
      setEditSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-manrope text-2xl font-bold">My children</h1>
        <p className="text-sm text-slate-500">Add your children and keep their details up to date.</p>
      </div>

      <Card>
        <h2 className="font-manrope text-lg font-semibold">Add a child</h2>
        <form onSubmit={addChild} className="mt-3 grid gap-3 sm:grid-cols-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Grade">
            <Input value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })} />
          </Field>
          <Field label="Address">
            <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <div className="sm:col-span-3">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Adding..." : "Add child"}
            </Button>
          </div>
        </form>
      </Card>

      {children === null ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      ) : children.length === 0 ? (
        <Empty>You have not added any children yet.</Empty>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {children.map((c) => (
            <Card key={c.id}>
              <h3 className="font-manrope text-base font-semibold">{c.name}</h3>
              <p className="text-sm text-slate-600">Grade: {c.grade}</p>
              <p className="text-sm text-slate-600">Address: {c.address || "Not set"}</p>
              <p className="text-sm text-slate-600">Enrolled on: {c.enrolled_on}</p>
              <p className="text-xs text-slate-400">ID: {c.public_id}</p>
              <div className="mt-3">
                <Button variant="secondary" onClick={() => openEdit(c)}>Edit</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={editing !== null} onClose={() => setEditing(null)} title="Edit child">
        <form onSubmit={saveEdit} className="space-y-3">
          <Field label="Name">
            <Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
          </Field>
          <Field label="Grade">
            <Input value={editForm.grade} onChange={(e) => setEditForm({ ...editForm, grade: e.target.value })} />
          </Field>
          <Field label="Address">
            <Textarea value={editForm.address} onChange={(e) => setEditForm({ ...editForm, address: e.target.value })} />
          </Field>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setEditing(null)}>Cancel</Button>
            <Button type="submit" variant="primary" disabled={editSaving}>
              {editSaving ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
