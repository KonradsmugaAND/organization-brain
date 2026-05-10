import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, apiDelete, type Note, type Space } from "@/api";

interface NotesViewProps {
  spaceId: string;
  spaces: Space[];
  userId: string;
  onOpenNoteModal: () => void;
  onRefresh?: number;
}

export function NotesView({ spaceId, spaces, userId, onOpenNoteModal, onRefresh }: NotesViewProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadNotes();
  }, [spaceId, onRefresh]);

  async function loadNotes() {
    setLoading(true);
    try {
      let all: Note[] = [];
      if (spaceId === "all") {
        for (const s of spaces) {
          try {
            const n = await apiGet<Note[]>(`/api/my/spaces/${encodeURIComponent(s.bank_id)}/notes`);
            all.push(...n.map((x) => ({ ...x, space_name: s.name, space_bank_id: s.bank_id })));
          } catch {
            // space may not have a collection yet
          }
        }
      } else {
        const sp = spaces.find((s) => s.bank_id === spaceId);
        try {
          const n = await apiGet<Note[]>(`/api/my/spaces/${encodeURIComponent(spaceId)}/notes`);
          all = n.map((x) => ({ ...x, space_name: sp?.name || spaceId, space_bank_id: spaceId }));
        } catch {
          // empty
        }
      }
      all.sort((a, b) => ((b.payload?.created_at || "") > (a.payload?.created_at || "") ? 1 : -1));
      setNotes(all);
    } finally {
      setLoading(false);
    }
  }

  function canDelete(note: Note): boolean {
    const bankId = note.space_bank_id || spaceId;
    if (bankId === `private_${userId}`) return true;
    const sp = spaces.find((s) => s.bank_id === bankId);
    return ["editor", "manager", "admin"].includes(sp?.role || "");
  }

  async function handleDelete(note: Note) {
    const bankId = note.space_bank_id || spaceId;
    if (!confirm("Usunąć tę notatkę?")) return;
    setDeleting(note.chunk_id);
    try {
      await apiDelete(`/api/my/spaces/${encodeURIComponent(bankId)}/notes/${note.chunk_id}`);
      setNotes((prev) => prev.filter((n) => n.chunk_id !== note.chunk_id));
    } catch (e) {
      alert(String(e));
    } finally {
      setDeleting(null);
    }
  }

  const title = spaceId === "all" ? "Wszystkie notatki" : spaces.find((s) => s.bank_id === spaceId)?.name || spaceId;
  const subtitle = spaceId === "all" ? "Notatki ze wszystkich przestrzeni" : "Notatki w tej przestrzeni";

  if (loading) {
    return <div className="p-5 text-sm" style={{ color: "var(--color-text-tertiary)" }}>Ładowanie...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>{title}</h2>
          <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>{subtitle}</p>
        </div>
        <Button size="sm" onClick={onOpenNoteModal} className="gap-1" style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}>
          <Plus className="w-4 h-4" />
          Nowa notatka
        </Button>
      </div>

      {notes.length === 0 && (
        <div className="text-center py-12" style={{ color: "var(--color-text-tertiary)" }}>
          <div className="text-sm font-semibold" style={{ color: "var(--color-text-secondary)" }}>Brak notatek</div>
          <div className="text-xs mt-1">Dodaj pierwszą notatkę lub przetwórz spotkanie</div>
        </div>
      )}

      <div className="space-y-3">
        {notes.map((n) => {
          const proposalBank = n.payload?.proposal_for_bank;
          const proposalStatus = n.payload?.proposal_status;
          const targetSpace = proposalBank
            ? spaces.find((s) => s.bank_id === proposalBank)?.name || proposalBank
            : null;

          const isPending = proposalBank && proposalStatus === "pending_approval";
          const isApproved = proposalBank && proposalStatus === "approved";
          const isRejected = proposalBank && proposalStatus === "rejected";

          return (
            <Card key={n.chunk_id} className="border transition-shadow hover:shadow-sm" style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap flex-1">
                    <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-accent) 15%, transparent)", color: "var(--color-accent)" }}>
                      {n.space_name || "notatka"}
                    </Badge>
                    {isPending && (
                      <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-warning) 15%, transparent)", color: "var(--color-warning)" }}>
                        Oczekuje na akceptację → {targetSpace}
                      </Badge>
                    )}
                    {isApproved && (
                      <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-success) 15%, transparent)", color: "var(--color-success)" }}>
                        Zatwierdzono → {targetSpace}
                      </Badge>
                    )}
                    {isRejected && (
                      <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-danger) 15%, transparent)", color: "var(--color-danger)" }}>
                        Odrzucono ({targetSpace})
                      </Badge>
                    )}
                  </div>
                  {canDelete(n) && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0 h-7 w-7"
                      disabled={deleting === n.chunk_id}
                      onClick={() => handleDelete(n)}
                    >
                      <Trash2 className="w-3.5 h-3.5" style={{ color: "var(--color-danger)" }} />
                    </Button>
                  )}
                </div>
                <div className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                  {n.payload?.title || n.text?.substring(0, 60) || "Notatka"}
                </div>
                <div className="text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {n.text}
                </div>
                <div className="flex items-center gap-3 text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                  <span>{n.payload?.user_id}</span>
                  <span>{n.payload?.created_at?.substring(0, 10)}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
