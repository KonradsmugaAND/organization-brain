import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiPost, type Space, type NoteCreateResponse } from "@/api";

interface NoteModalProps {
  open: boolean;
  onClose: () => void;
  spaces: Space[];
  defaultSpace?: string;
  onSaved: (result: NoteCreateResponse) => void;
}

type FlashKind = "success" | "info" | "error";

interface Flash {
  kind: FlashKind;
  message: string;
}

export function NoteModal({ open, onClose, spaces, defaultSpace, onSaved }: NoteModalProps) {
  const [spaceId, setSpaceId] = useState(defaultSpace || spaces[0]?.bank_id || "");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);

  function reset() {
    setTitle("");
    setBody("");
    setFlash(null);
  }

  async function handleSave() {
    if (!title.trim() || !body.trim()) return;
    setLoading(true);
    setFlash(null);
    try {
      const result = await apiPost<NoteCreateResponse>(
        `/api/my/spaces/${encodeURIComponent(spaceId)}/notes`,
        { title, content: body }
      );
      onSaved(result);
      if (result.mode === "proposal") {
        setFlash({
          kind: "info",
          message:
            "Wysłano propozycję — czeka na zatwierdzenie przez admina przestrzeni. Kopia widoczna w Twojej prywatnej przestrzeni.",
        });
        setTimeout(() => {
          reset();
          onClose();
        }, 2200);
      } else {
        reset();
        onClose();
      }
    } catch (e) {
      setFlash({ kind: "error", message: String(e) });
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (loading) return;
    reset();
    onClose();
  }

  const flashStyle = flash
    ? flash.kind === "error"
      ? { background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.4)", color: "#fca5a5" }
      : flash.kind === "info"
        ? { background: "rgba(99, 102, 241, 0.1)", borderColor: "rgba(99, 102, 241, 0.4)", color: "#c7d2fe" }
        : { background: "rgba(16, 185, 129, 0.1)", borderColor: "rgba(16, 185, 129, 0.4)", color: "#86efac" }
    : undefined;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-md" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
        <DialogHeader>
          <DialogTitle className="text-base font-bold">Nowa notatka</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Przestrzeń</Label>
            <Select value={spaceId} onValueChange={setSpaceId}>
              <SelectTrigger className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {spaces.map((s) => (
                  <SelectItem key={s.bank_id} value={s.bank_id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Tytuł</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Tytuł notatki" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Treść</Label>
            <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Treść notatki..." rows={5} className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
          </div>
          {flash && (
            <div
              role="status"
              className="rounded-md border px-3 py-2 text-xs"
              style={flashStyle}
            >
              {flash.message}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={handleClose} disabled={loading}>Anuluj</Button>
          <Button size="sm" onClick={handleSave} disabled={loading || !title.trim() || !body.trim()} style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}>
            Zapisz notatkę
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
