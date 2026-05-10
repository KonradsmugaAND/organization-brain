import { useEffect, useState } from "react";
import { Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { apiGet, apiPost, apiPatch, apiDelete, type User } from "@/api";

export function UsersView() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("webwave");
  const [team, setTeam] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editTeam, setEditTeam] = useState("");
  const [editCompany, setEditCompany] = useState("");
  const [editRole, setEditRole] = useState("");

  async function load() {
    setLoading(true);
    try {
      const u = await apiGet<User[]>("/api/users");
      setUsers(u);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAdd() {
    if (!name.trim()) return;
    const userId = name.toLowerCase().replace(/\s+/g, ".").replace(/[^a-z0-9.]/g, "");
    try {
      await apiPost("/api/users", {
        user_id: userId,
        name: name.trim(),
        role: "member",
        team: team.trim(),
        company: company.trim() || "webwave",
        email: email.trim(),
        password: "",
      });
      setOpen(false);
      setName("");
      setEmail("");
      setTeam("");
      await load();
    } catch (e) {
      alert(String(e));
    }
  }

  function openEdit(u: User) {
    setEditUser(u);
    setEditName(u.name);
    setEditEmail(u.email || "");
    setEditTeam(u.team || "");
    setEditCompany(u.company || "webwave");
    setEditRole(u.role);
    setEditOpen(true);
  }

  async function handleEdit() {
    if (!editUser || !editName.trim()) return;
    try {
      await apiPatch(`/api/users/${editUser.id}`, {
        name: editName.trim(),
        email: editEmail.trim(),
        team: editTeam.trim(),
        company: editCompany.trim(),
        role: editRole.trim(),
      });
      setEditOpen(false);
      await load();
    } catch (e) {
      alert(String(e));
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Usunąć użytkownika ${name}?`)) return;
    try {
      await apiDelete(`/api/users/${id}`);
      await load();
    } catch (e) {
      alert(String(e));
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: "var(--color-text-tertiary)" }}>
        Ładowanie...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>
            Użytkownicy
          </h2>
          <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            Zarządzaj użytkownikami systemu
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => setOpen(true)}
          className="gap-1"
          style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
        >
          <Plus className="w-4 h-4" />
          Dodaj użytkownika
        </Button>
      </div>

      <div
        className="rounded-xl border overflow-hidden"
        style={{
          background: "var(--color-background-secondary)",
          borderColor: "var(--color-border-primary)",
        }}
      >
        <Table>
          <TableHeader>
            <TableRow style={{ borderColor: "var(--color-border-primary)" }}>
              <TableHead className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                Użytkownik
              </TableHead>
              <TableHead className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                Rola
              </TableHead>
              <TableHead className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                Zespół
              </TableHead>
              <TableHead className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                Firma
              </TableHead>
              <TableHead className="text-xs font-medium text-right" style={{ color: "var(--color-text-secondary)" }}>
                Akcje
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-xs py-8" style={{ color: "var(--color-text-tertiary)" }}>
                  Brak użytkowników
                </TableCell>
              </TableRow>
            )}
            {users.map((u) => (
              <TableRow key={u.id} style={{ borderColor: "var(--color-border-primary)" }}>
                <TableCell>
                  <div className="text-sm font-medium">{u.name}</div>
                  <div className="text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                    {u.email}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className="text-[10px] capitalize"
                    style={{ borderColor: "var(--color-border-primary)" }}
                  >
                    {u.role}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  {u.team || "—"}
                </TableCell>
                <TableCell className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  {u.company || "—"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => openEdit(u)}
                    >
                      <Pencil className="w-3.5 h-3.5" style={{ color: "var(--color-text-secondary)" }} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => handleDelete(u.id, u.name)}
                    >
                      <Trash2 className="w-3.5 h-3.5" style={{ color: "var(--color-danger)" }} />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
          <DialogHeader>
            <DialogTitle className="text-base font-bold">Edytuj użytkownika</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Imię i nazwisko</Label>
              <Input value={editName} onChange={(e) => setEditName(e.target.value)} placeholder="Jan Kowalski" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Email</Label>
              <Input type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} placeholder="jan@webwave.pl" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Firma</Label>
                <Input value={editCompany} onChange={(e) => setEditCompany(e.target.value)} placeholder="webwave" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Zespół</Label>
                <Input value={editTeam} onChange={(e) => setEditTeam(e.target.value)} placeholder="Product" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Rola</Label>
              <Input value={editRole} onChange={(e) => setEditRole(e.target.value)} placeholder="member / admin" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setEditOpen(false)}>Anuluj</Button>
            <Button size="sm" onClick={handleEdit} disabled={!editName.trim()} style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}>Zapisz</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
          <DialogHeader>
            <DialogTitle className="text-base font-bold">Dodaj użytkownika</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
                Imię i nazwisko
              </Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jan Kowalski"
                className="text-sm"
                style={{ borderColor: "var(--color-border-secondary)" }}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
                Email
              </Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jan@webwave.pl"
                className="text-sm"
                style={{ borderColor: "var(--color-border-secondary)" }}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
                  Firma
                </Label>
                <Input
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="webwave"
                  className="text-sm"
                  style={{ borderColor: "var(--color-border-secondary)" }}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
                  Zespół
                </Label>
                <Input
                  value={team}
                  onChange={(e) => setTeam(e.target.value)}
                  placeholder="Product"
                  className="text-sm"
                  style={{ borderColor: "var(--color-border-secondary)" }}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setOpen(false)}>
              Anuluj
            </Button>
            <Button
              size="sm"
              onClick={handleAdd}
              disabled={!name.trim()}
              style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
            >
              Zapisz
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
