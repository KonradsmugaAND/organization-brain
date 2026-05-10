import { useEffect, useMemo, useState } from "react";
import { Plus, Building2, Users, UserPlus, Trash2, ChevronRight, FileText, BookOpen, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { apiGet, apiPost, apiDelete, type Space, type User, type Note } from "@/api";
import { AdminNoteModal } from "@/components/AdminNoteModal";

type AddTarget = { type: "company"; parentId: string } | { type: "team"; parentId: string } | { type: "employee"; teamId: string; company: string } | null;

const SPACE_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  weall: { bg: "var(--color-bank-weall-bg)", text: "var(--color-bank-weall-text)", dot: "var(--color-bank-weall-text)" },
  company: { bg: "var(--color-bank-comp-bg)", text: "var(--color-bank-comp-text)", dot: "var(--color-bank-comp-text)" },
  team: { bg: "var(--color-bank-team-bg)", text: "var(--color-bank-team-text)", dot: "var(--color-bank-team-text)" },
  group: { bg: "var(--color-bank-group-bg)", text: "var(--color-bank-group-text)", dot: "var(--color-bank-group-text)" },
  private: { bg: "var(--color-bank-priv-bg)", text: "var(--color-bank-priv-text)", dot: "var(--color-bank-priv-text)" },
};

interface NotesPanelProps {
  bankId: string;
  spaceName: string;
  onClose: () => void;
}

function NotesPanel({ bankId, spaceName, onClose }: NotesPanelProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);

  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Note[]>(`/api/spaces/${encodeURIComponent(bankId)}/notes`)
      .then(setNotes)
      .catch(() => setNotes([]))
      .finally(() => setLoading(false));
  }, [bankId]);

  async function handleDelete(chunkId: string) {
    if (!confirm("Usunąć tę notatkę?")) return;
    setDeleting(chunkId);
    try {
      await apiDelete(`/api/spaces/${encodeURIComponent(bankId)}/notes/${chunkId}`);
      setNotes((prev) => prev.filter((n) => n.chunk_id !== chunkId));
    } catch (e) {
      alert(String(e));
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.35)" }} onClick={onClose}>
      <div
        className="relative flex flex-col rounded-xl border shadow-2xl w-full max-w-lg max-h-[80vh]"
        style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-xl) var(--radius-xl) 0 0" }}>
          <div>
            <div className="text-sm font-bold" style={{ color: "var(--color-text-primary)" }}>Notatki — {spaceName}</div>
            <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>{notes.length} notatek</div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && <div className="text-sm text-center py-8" style={{ color: "var(--color-text-tertiary)" }}>Ładowanie...</div>}
          {!loading && notes.length === 0 && (
            <div className="text-sm text-center py-8" style={{ color: "var(--color-text-tertiary)" }}>Brak notatek w tej przestrzeni</div>
          )}
          {notes.map((n) => (
            <div
              key={n.chunk_id}
              className="rounded-lg border p-3"
              style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)" }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 space-y-1">
                  {n.title && (
                    <div className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>{n.title}</div>
                  )}
                  <div className="text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>{n.text}</div>
                  <div className="text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                    {n.user_id} · {n.created_at?.substring(0, 10)}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  disabled={deleting === n.chunk_id}
                  onClick={() => handleDelete(n.chunk_id)}
                >
                  <Trash2 className="w-3.5 h-3.5" style={{ color: "var(--color-danger)" }} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function SpacesView() {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [addTarget, setAddTarget] = useState<AddTarget>(null);
  const [addName, setAddName] = useState("");
  const [addEmail, setAddEmail] = useState("");
  const [addLogin, setAddLogin] = useState("");
  const [addPassword, setAddPassword] = useState("");
  const [addRole, setAddRole] = useState("member");
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [noteDefaultBank, setNoteDefaultBank] = useState<string | undefined>(undefined);
  const [notesPanel, setNotesPanel] = useState<{ bankId: string; spaceName: string } | null>(null);

  function openNoteModal(defaultBank?: string) {
    setNoteDefaultBank(defaultBank);
    setNoteModalOpen(true);
  }

  async function load() {
    setLoading(true);
    try {
      const [s, u] = await Promise.all([
        apiGet<Space[]>("/api/spaces"),
        apiGet<User[]>("/api/users"),
      ]);
      // Auto-create WeAll if missing
      if (!s.find((x) => x.space_type === "weall")) {
        await apiPost("/api/spaces", {
          space_id: "weall",
          name: "WeAll",
          bank_id: "weall",
          space_type: "weall",
          description: "Główna przestrzeń organizacji",
          parent_id: null,
        });
        const refreshed = await apiGet<Space[]>("/api/spaces");
        setSpaces(refreshed);
        setUsers(u);
        setExpandedCompanies(new Set(refreshed.filter((x) => x.space_type === "company").map((x) => x.id)));
        return;
      }
      setSpaces(s);
      setUsers(u);
      setExpandedCompanies(new Set(s.filter((x) => x.space_type === "company").map((x) => x.id)));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const tree = useMemo(() => {
    const byId = new Map(spaces.map((s) => [s.id, { ...s, children: [] as Space[] }]));
    const roots: (Space & { children: Space[] })[] = [];
    for (const s of byId.values()) {
      if (s.parent_id && byId.has(s.parent_id)) {
        byId.get(s.parent_id)!.children.push(s);
      } else {
        roots.push(s);
      }
    }
    return roots;
  }, [spaces]);

  const weall = useMemo(() => {
    const found = spaces.find((s) => s.space_type === "weall");
    if (found) return found;
    if (tree[0]) return { ...tree[0], name: "WeAll", space_type: "weall" } as Space;
    return null;
  }, [spaces, tree]);

  const companies = useMemo(() => {
    return spaces.filter(
      (s) => s.space_type === "company" && (s.parent_id === weall?.id || !s.parent_id || s.parent_id === "weall")
    );
  }, [spaces, weall]);

  function teamsForCompany(companyId: string) {
    return spaces.filter((s) => s.parent_id === companyId && s.space_type === "team");
  }

  function employeesForTeam(teamBankId: string) {
    return users.filter((u) => u.team && teamBankId.includes(u.team));
  }

  function toggleCompany(id: string) {
    setExpandedCompanies((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleAdd() {
    if (!addTarget || !addName.trim()) return;
    try {
      if (addTarget.type === "company" || addTarget.type === "team") {
        const type = addTarget.type;
        const slug = addName.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
        const bankId = type + "_" + slug;
        await apiPost("/api/spaces", {
          space_id: bankId,
          name: addName.trim(),
          bank_id: bankId,
          space_type: type,
          parent_id: addTarget.parentId,
        });
      } else if (addTarget.type === "employee") {
        const userId = (addLogin.trim() || addName.toLowerCase().replace(/\s+/g, ".").replace(/[^a-z0-9.]/g, ""));
        await apiPost("/api/users", {
          user_id: userId,
          name: addName.trim(),
          role: addRole,
          team: addTarget.teamId,
          company: addTarget.company,
          email: addEmail.trim(),
          password: addPassword,
        });
        const teamSpace = spaces.find((s) => s.bank_id === addTarget.teamId);
        if (teamSpace) {
          await apiPost(`/api/users/${userId}/acl`, {
            user_id: userId,
            bank_id: teamSpace.bank_id,
            role: addRole,
          });
        }
      }
      setAddTarget(null);
      setAddName("");
      setAddEmail("");
      setAddLogin("");
      setAddPassword("");
      setAddRole("member");
      await load();
    } catch (e) {
      alert(String(e));
    }
  }

  async function handleDeleteSpace(id: string, name: string) {
    if (!confirm(`Usunąć przestrzeń ${name}?`)) return;
    try {
      await apiDelete(`/api/spaces/${id}`);
      await load();
    } catch (e) {
      alert(String(e));
    }
  }

  async function handleDeleteUser(id: string, name: string) {
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
    <div className="space-y-6">
      {/* WeAll header */}
      {weall && (
        <div
          className="flex items-center justify-between p-4 rounded-xl border"
          style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)" }}
        >
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full" style={{ background: SPACE_COLORS.weall.dot }} />
            <div>
              <div className="text-base font-bold" style={{ color: "var(--color-text-primary)" }}>
                {weall.space_type === "weall" ? "WeAll" : weall.name}
              </div>
              <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
                Główna przestrzeń — widoczna dla wszystkich
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setNotesPanel({ bankId: weall.bank_id, spaceName: "WeAll" })}
              className="gap-1"
              style={{ borderColor: "var(--color-border-secondary)", color: "var(--color-text-primary)" }}
            >
              <BookOpen className="w-4 h-4" />
              Przeglądaj notatki
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => openNoteModal(weall.bank_id)}
              className="gap-1"
              style={{ borderColor: "var(--color-border-secondary)", color: "var(--color-text-primary)" }}
            >
              <FileText className="w-4 h-4" />
              Dodaj notatkę
            </Button>
            <Button
              size="sm"
              onClick={() => setAddTarget({ type: "company", parentId: weall.id })}
              className="gap-1"
              style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
            >
              <Plus className="w-4 h-4" />
              Dodaj firmę
            </Button>
          </div>
        </div>
      )}

      {/* Companies grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
        {companies.map((company) => {
          const isExpanded = expandedCompanies.has(company.id);
          const teams = teamsForCompany(company.id);
          return (
            <Card
              key={company.id}
              className="border flex flex-col"
              style={{
                background: "var(--color-background-secondary)",
                borderColor: "var(--color-border-primary)",
                borderRadius: "var(--radius-lg)",
              }}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4" style={{ color: SPACE_COLORS.company.dot }} />
                    <CardTitle className="text-sm font-semibold">{company.name}</CardTitle>
                    <Badge
                      variant="outline"
                      className="text-[10px] uppercase"
                      style={{ borderColor: "var(--color-border-primary)", color: "var(--color-text-tertiary)" }}
                    >
                      Firma
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => setNotesPanel({ bankId: company.bank_id, spaceName: company.name })}
                      title="Przeglądaj notatki firmy"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => openNoteModal(company.bank_id)}
                      title="Dodaj notatkę do firmy"
                    >
                      <FileText className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => setAddTarget({ type: "team", parentId: company.id })}
                      title="Dodaj zespół"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => handleDeleteSpace(company.id, company.name)}
                      title="Usuń firmę"
                    >
                      <Trash2 className="w-3.5 h-3.5" style={{ color: "var(--color-danger)" }} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => toggleCompany(company.id)}
                      title="Rozwiń/zwiń"
                    >
                      <ChevronRight
                        className={`w-3.5 h-3.5 transition-transform ${isExpanded ? "rotate-90" : ""}`}
                      />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              {isExpanded && (
                <CardContent className="pt-0 space-y-3">
                  {teams.length === 0 && (
                    <div className="text-xs italic py-2" style={{ color: "var(--color-text-tertiary)" }}>
                      Brak zespołów. Dodaj pierwszy.
                    </div>
                  )}
                  {teams.map((team) => {
                    const emps = employeesForTeam(team.bank_id);
                    return (
                      <div
                        key={team.id}
                        className="rounded-lg border p-3 space-y-2"
                        style={{
                          background: "var(--color-background-primary)",
                          borderColor: "var(--color-border-primary)",
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" style={{ color: SPACE_COLORS.team.dot }} />
                            <span className="text-sm font-medium">{team.name}</span>
                            <Badge
                              variant="outline"
                              className="text-[10px] uppercase"
                              style={{ borderColor: "var(--color-border-primary)", color: "var(--color-text-tertiary)" }}
                            >
                              Zespół
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() => setNotesPanel({ bankId: team.bank_id, spaceName: team.name })}
                              title="Przeglądaj notatki zespołu"
                            >
                              <BookOpen className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() => openNoteModal(team.bank_id)}
                              title="Dodaj notatkę do zespołu"
                            >
                              <FileText className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() =>
                                setAddTarget({
                                  type: "employee",
                                  teamId: team.bank_id,
                                  company: company.name,
                                })
                              }
                              title="Dodaj pracownika"
                            >
                              <UserPlus className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() => handleDeleteSpace(team.id, team.name)}
                              title="Usuń zespół"
                            >
                              <Trash2 className="w-3.5 h-3.5" style={{ color: "var(--color-danger)" }} />
                            </Button>
                          </div>
                        </div>

                        {/* Employees */}
                        <div className="space-y-1 pl-6">
                          {emps.length === 0 && (
                            <div className="text-[11px] italic" style={{ color: "var(--color-text-tertiary)" }}>
                              Brak pracowników
                            </div>
                          )}
                          {emps.map((emp) => (
                            <div
                              key={emp.id}
                              className="flex items-center justify-between text-xs py-1 px-2 rounded-md"
                              style={{ background: "var(--color-background-secondary)" }}
                            >
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ background: "var(--color-accent)" }} />
                                <span className="font-medium">{emp.name}</span>
                                <span style={{ color: "var(--color-text-tertiary)" }}>{emp.email}</span>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon-xs"
                                onClick={() => handleDeleteUser(emp.id, emp.name)}
                              >
                                <Trash2 className="w-3 h-3" style={{ color: "var(--color-danger)" }} />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>

      {/* Add Dialog */}
      <Dialog open={!!addTarget} onOpenChange={(open) => !open && setAddTarget(null)}>
        <DialogContent className="sm:max-w-md" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
          <DialogHeader>
            <DialogTitle className="text-base font-bold">
              {addTarget?.type === "company" && "Dodaj firmę"}
              {addTarget?.type === "team" && "Dodaj zespół"}
              {addTarget?.type === "employee" && "Dodaj pracownika"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
                {addTarget?.type === "employee" ? "Imię i nazwisko" : "Nazwa"}
              </Label>
              <Input
                value={addName}
                onChange={(e) => setAddName(e.target.value)}
                placeholder={
                  addTarget?.type === "company"
                    ? "np. WebWave"
                    : addTarget?.type === "team"
                    ? "np. Product"
                    : "np. Jan Kowalski"
                }
                className="text-sm"
                style={{ borderColor: "var(--color-border-secondary)" }}
              />
            </div>
            {addTarget?.type === "employee" && (
              <>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Email</Label>
                  <Input type="email" value={addEmail} onChange={(e) => setAddEmail(e.target.value)} placeholder="jan@webwave.pl" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Login (ID użytkownika)</Label>
                  <Input value={addLogin} onChange={(e) => setAddLogin(e.target.value)} placeholder="np. jan.kowalski" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
                  <p className="text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>Zostaw puste — zostanie wygenerowany z imienia i nazwiska</p>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Hasło</Label>
                  <Input type="password" value={addPassword} onChange={(e) => setAddPassword(e.target.value)} placeholder="••••••" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Rola</Label>
                  <select
                    value={addRole}
                    onChange={(e) => setAddRole(e.target.value)}
                    className="flex h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-sm"
                    style={{ borderColor: "var(--color-border-secondary)", color: "var(--color-text-primary)", background: "var(--color-background-primary)" }}
                  >
                    <option value="member">Pracownik (member)</option>
                    <option value="editor">Edytor (editor)</option>
                    <option value="manager">Manager</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setAddTarget(null)}>
              Anuluj
            </Button>
            <Button
              size="sm"
              onClick={handleAdd}
              disabled={!addName.trim()}
              style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
            >
              Zapisz
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AdminNoteModal
        open={noteModalOpen}
        onClose={() => setNoteModalOpen(false)}
        spaces={spaces}
        defaultSpaceBankId={noteDefaultBank}
      />

      {notesPanel && (
        <NotesPanel
          bankId={notesPanel.bankId}
          spaceName={notesPanel.spaceName}
          onClose={() => setNotesPanel(null)}
        />
      )}
    </div>
  );
}
