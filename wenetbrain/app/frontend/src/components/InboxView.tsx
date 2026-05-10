import { useEffect, useState } from "react";
import { CheckCircle, XCircle, CheckCircle2, CalendarDays, FileText, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, apiPost, type InboxItem, type Space } from "@/api";

interface InboxViewProps {
  userId: string;
  spaces?: Space[];
  onCountChange: (count: number) => void;
}

export function InboxView({ userId, spaces = [], onCountChange }: InboxViewProps) {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInbox();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  async function loadInbox() {
    setLoading(true);
    try {
      const data = await apiGet<InboxItem[]>("/api/inbox");
      setItems(data);
      onCountChange(
        data.filter((i) => (i.status ?? "pending_approval") === "pending_approval").length,
      );
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function approve(id: string, action: string) {
    try {
      await apiPost(`/api/inbox/${id}/approve`, { action });
      await loadInbox();
    } catch (e) {
      alert(String(e));
    }
  }

  async function reject(id: string) {
    try {
      await apiPost(`/api/inbox/${id}/reject`, {});
      await loadInbox();
    } catch (e) {
      alert(String(e));
    }
  }

  const typeIcon = (type: string) => {
    if (type === "action_item") return <CheckCircle2 className="w-4 h-4" />;
    if (type === "calendar_event") return <CalendarDays className="w-4 h-4" />;
    if (type === "note") return <FileText className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const typeBg = (type: string) => {
    if (type === "action_item") return { bg: "var(--color-info)", color: "var(--color-primary-foreground)" };
    if (type === "calendar_event") return { bg: "var(--color-success)", color: "var(--color-primary-foreground)" };
    if (type === "note") return { bg: "var(--color-warning)", color: "var(--color-primary-foreground)" };
    return { bg: "var(--color-accent)", color: "var(--color-primary-foreground)" };
  };

  function spaceName(bankId?: string) {
    if (!bankId) return "—";
    return spaces.find((s) => s.bank_id === bankId)?.name || bankId;
  }

  function renderNoteContent(item: InboxItem): { title: string; body: string } {
    let title = "";
    let body = "";
    if (typeof item.content === "string") {
      try {
        const parsed = JSON.parse(item.content);
        title = parsed.title ?? "";
        body = parsed.content ?? "";
      } catch {
        body = item.content;
      }
    } else if (item.content) {
      title = String(item.content.title ?? "");
      body = String(item.content.content ?? "");
    }
    return { title, body };
  }

  if (loading) {
    return <div className="p-5 text-sm" style={{ color: "var(--color-text-tertiary)" }}>Ładowanie...</div>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>Inbox</h2>
        <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Zatwierdź zadania, spotkania, decyzje i propozycje notatek</p>
      </div>

      {items.length === 0 && (
        <div className="text-center py-12" style={{ color: "var(--color-text-tertiary)" }}>
          <span className="material-icons-outlined text-5xl mb-3 opacity-40">inbox</span>
          <div className="text-sm font-semibold" style={{ color: "var(--color-text-secondary)" }}>Inbox jest pusty</div>
          <div className="text-xs mt-1">Przetwórz spotkanie, aby zobaczyć propozycje</div>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => {
          const isNote = item.item_type === "note";
          const isTask = item.item_type === "action_item";
          const isEvent = item.item_type === "calendar_event";
          const status = item.status ?? "pending_approval";
          const isPending = status === "pending_approval";
          const canApprove = item.can_approve === true && isPending;
          const isMine = item.is_mine === true;
          const noteParts = isNote ? renderNoteContent(item) : null;
          const fallbackContent =
            typeof item.content === "string" ? item.content : JSON.stringify(item.content);
          const style = typeBg(item.item_type);

          return (
            <Card key={item.id} className="border" style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className="text-[11px] px-2 py-0.5 rounded-full flex items-center gap-1" style={{ background: style.bg, color: style.color }}>
                    {typeIcon(item.item_type)}
                    {item.item_type}
                  </Badge>
                  <Badge variant="outline" className="text-[11px]" style={{ borderColor: "var(--color-border-primary)", color: "var(--color-text-tertiary)" }}>
                    {isNote ? `→ ${spaceName(item.bank_id)}` : item.bank_id || "—"}
                  </Badge>
                  {isNote && isMine && (
                    <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-accent) 18%, transparent)", color: "var(--color-accent)" }}>
                      Twoja propozycja
                    </Badge>
                  )}
                  {!isPending && (
                    <Badge variant="outline" className="text-[11px] gap-1 flex items-center" style={{ borderColor: "var(--color-border-primary)", color: status === "approved" ? "var(--color-success)" : status === "rejected" ? "var(--color-danger)" : "var(--color-text-tertiary)" }}>
                      {status === "approved" ? <CheckCircle className="w-3 h-3" /> : status === "rejected" ? <XCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                      {status}
                    </Badge>
                  )}
                </div>

                {isNote && noteParts ? (
                  <>
                    {noteParts.title && (
                      <div className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                        {noteParts.title}
                      </div>
                    )}
                    <div className="text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                      {noteParts.body}
                    </div>
                    {item.proposed_by && (
                      <div className="text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                        Autor: {item.proposed_by}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                    {fallbackContent?.substring(0, 200)}
                  </div>
                )}

                <div className="text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                  {item.created_at}
                </div>

                {isPending && (
                  <div className="flex flex-wrap gap-2">
                    {isTask && canApprove && (
                      <Button size="sm" className="gap-1 text-xs" style={{ background: "var(--color-success)", color: "var(--color-primary-foreground)" }} onClick={() => approve(item.id, "clickup")}>
                        <CheckCircle className="w-3.5 h-3.5" />
                        Zatwierdź i dodaj do ClickUp
                      </Button>
                    )}
                    {isEvent && canApprove && (
                      <Button size="sm" className="gap-1 text-xs" style={{ background: "var(--color-success)", color: "var(--color-primary-foreground)" }} onClick={() => approve(item.id, "outlook")}>
                        <CheckCircle className="w-3.5 h-3.5" />
                        Zatwierdź i dodaj do Outlook
                      </Button>
                    )}
                    {canApprove && (
                      <Button size="sm" variant="ghost" className="text-xs gap-1" style={{ color: "var(--color-success)" }} onClick={() => approve(item.id, "none")}>
                        <CheckCircle className="w-3.5 h-3.5" />
                        {isNote ? "Opublikuj w przestrzeni" : "Tylko zatwierdź"}
                      </Button>
                    )}
                    {(canApprove || (isNote && isMine)) && (
                      <Button size="sm" variant="ghost" className="text-xs gap-1" style={{ color: "var(--color-danger)" }} onClick={() => reject(item.id)}>
                        <XCircle className="w-3.5 h-3.5" />
                        {isNote && isMine && !canApprove ? "Anuluj" : "Odrzuć"}
                      </Button>
                    )}
                    {isNote && isMine && !canApprove && (
                      <span className="text-[11px] self-center" style={{ color: "var(--color-text-tertiary)" }}>
                        Czeka na zatwierdzenie przez admina przestrzeni.
                      </span>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
