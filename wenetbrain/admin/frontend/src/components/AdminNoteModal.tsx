import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiPost, type Space } from "@/api";

interface AdminNoteModalProps {
  open: boolean;
  onClose: () => void;
  spaces: Space[];
  defaultSpaceBankId?: string;
  onSaved?: () => void;
}

const SPACE_TYPE_LABEL: Record<string, string> = {
  weall: "WeAll",
  company: "Firma",
  team: "Zespół",
  group: "Grupa",
  private: "Prywatna",
};

export function AdminNoteModal({
  open,
  onClose,
  spaces,
  defaultSpaceBankId,
  onSaved,
}: AdminNoteModalProps) {
  const [bankId, setBankId] = useState<string>(defaultSpaceBankId || spaces[0]?.bank_id || "");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [flash, setFlash] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (open) {
      setBankId(defaultSpaceBankId || spaces[0]?.bank_id || "");
      setTitle("");
      setBody("");
      setFlash(null);
    }
  }, [open, defaultSpaceBankId, spaces]);

  async function handleSave() {
    if (!bankId || !title.trim() || !body.trim()) return;
    setLoading(true);
    setFlash(null);
    try {
      await apiPost(`/api/spaces/${encodeURIComponent(bankId)}/notes`, {
        title: title.trim(),
        content: body.trim(),
      });
      const spaceName = spaces.find((s) => s.bank_id === bankId)?.name || bankId;
      setFlash({
        kind: "success",
        message: `Notatka opublikowana w przestrzeni „${spaceName}".`,
      });
      onSaved?.();
      setTitle("");
      setBody("");
      setTimeout(() => onClose(), 1400);
    } catch (e) {
      setFlash({ kind: "error", message: String(e) });
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (loading) return;
    onClose();
  }

  const sortedSpaces = [...spaces].sort((a, b) => {
    const order = ["weall", "company", "team", "group", "private"];
    const ai = order.indexOf(a.space_type);
    const bi = order.indexOf(b.space_type);
    if (ai !== bi) return ai - bi;
    return a.name.localeCompare(b.name);
  });

  const flashStyle = flash
    ? flash.kind === "error"
      ? { background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.4)", color: "#fca5a5" }
      : { background: "rgba(16, 185, 129, 0.1)", borderColor: "rgba(16, 185, 129, 0.4)", color: "#86efac" }
    : undefined;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent
        className="sm:max-w-md"
        style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}
      >
        <DialogHeader>
          <DialogTitle className="text-base font-bold">Dodaj notatkę do przestrzeni</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
              Przestrzeń
            </Label>
            {defaultSpaceBankId ? (
              <div
                className="flex items-center gap-2 px-3 py-2 rounded-md border text-sm"
                style={{ borderColor: "var(--color-border-secondary)", background: "var(--color-background-secondary)", color: "var(--color-text-primary)" }}
              >
                <span className="text-xs uppercase opacity-60">
                  {SPACE_TYPE_LABEL[sortedSpaces.find((s) => s.bank_id === bankId)?.space_type ?? ""] ?? ""}
                </span>
                <span className="font-medium">{sortedSpaces.find((s) => s.bank_id === bankId)?.name ?? bankId}</span>
              </div>
            ) : (
              <Select value={bankId} onValueChange={setBankId}>
                <SelectTrigger className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }}>
                  <SelectValue placeholder="Wybierz przestrzeń" />
                </SelectTrigger>
                <SelectContent>
                  {sortedSpaces.map((s) => (
                    <SelectItem key={s.bank_id} value={s.bank_id}>
                      <span className="text-xs uppercase mr-2 opacity-60">
                        {SPACE_TYPE_LABEL[s.space_type] ?? s.space_type}
                      </span>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
              Tytuł
            </Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Tytuł notatki"
              className="text-sm"
              style={{ borderColor: "var(--color-border-secondary)" }}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>
              Treść
            </Label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Treść notatki..."
              rows={5}
              className="flex w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
              style={{ borderColor: "var(--color-border-secondary)", color: "var(--color-text-primary)" }}
            />
          </div>
          {flash && (
            <div role="status" className="rounded-md border px-3 py-2 text-xs" style={flashStyle}>
              {flash.message}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={handleClose} disabled={loading}>
            Anuluj
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={loading || !bankId || !title.trim() || !body.trim()}
            style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
          >
            {loading ? "Zapisywanie..." : "Opublikuj notatkę"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
