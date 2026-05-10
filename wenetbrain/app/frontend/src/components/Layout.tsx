import { useEffect, useState } from "react";
import { FolderOpen, Inbox, Settings, LogOut, Search, ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiGet, type Space, type User } from "@/api";

interface LayoutProps {
  children: React.ReactNode;
  chatMessages: { role: "user" | "ai"; text: string }[];
  chatInput: string;
  onChatInputChange: (v: string) => void;
  onSendChat: () => void;
  currentSpace: string;
  onSpaceChange: (bankId: string) => void;
  onOpenMeetingModal: () => void;
  onShowTab: (tab: string) => void;
  activeTab: string;
  inboxCount: number;
}

export function Layout({
  children,
  chatMessages,
  chatInput,
  onChatInputChange,
  onSendChat,
  currentSpace,
  onSpaceChange,
  onOpenMeetingModal,
  onShowTab,
  activeTab,
  inboxCount,
}: LayoutProps) {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [userName, setUserName] = useState("—");
  const [searchQ, setSearchQ] = useState("");

  useEffect(() => {
    apiGet<User>("/api/auth/me").then((u) => setUserName(u.name || u.id));
    apiGet<Space[]>("/api/my/spaces").then(setSpaces);
  }, []);

  function logout() {
    localStorage.removeItem("wenetbrain_token");
    window.location.href = "/login.html";
  }

  function doSearch() {
    if (!searchQ.trim()) return;
    onShowTab("search");
    // search handled by parent via effect or callback
    window.dispatchEvent(new CustomEvent("global-search", { detail: searchQ.trim() }));
  }

  const spaceColor = (type: string) => {
    if (type === "company") return "var(--color-bank-comp-text)";
    if (type === "team") return "var(--color-bank-team-text)";
    if (type === "group") return "var(--color-bank-group-text)";
    if (type === "private") return "var(--color-bank-priv-text)";
    return "var(--color-bank-weall-text)";
  };

  return (
    <div className="grid h-screen grid-rows-[52px_1fr] grid-cols-[240px_1fr_360px]" style={{ background: "var(--color-background-primary)" }}>
      {/* Topbar */}
      <div
        className="col-span-3 flex items-center px-4 gap-3 border-b z-50"
        style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}
      >
        <span className="text-[15px] font-extrabold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          WenetBrain
        </span>
        <div
          className="flex-1 max-w-[480px] flex items-center gap-2 px-3 py-1.5 rounded-md border transition-all focus-within:ring-[3px]"
          style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)" }}
        >
          <Search className="w-4 h-4" style={{ color: "var(--color-text-tertiary)" }} />
          <Input
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
            placeholder="Wyszukaj notatki..."
            className="border-0 bg-transparent shadow-none focus-visible:ring-0 h-6 text-sm p-0"
            style={{ color: "var(--color-text-primary)" }}
          />
        </div>
        <div className="flex-1" />
        <Button
          size="sm"
          onClick={onOpenMeetingModal}
          className="gap-1.5"
          style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}
        >
          <span className="w-2 h-2 rounded-full" style={{ background: "var(--color-danger)" }} />
          Nagraj spotkanie
        </Button>
        <span className="text-xs px-2 py-1 rounded-md border" style={{ borderColor: "var(--color-border-primary)", color: "var(--color-text-secondary)" }}>
          {userName}
        </span>
        <Button variant="ghost" size="sm" onClick={logout} className="gap-1">
          <LogOut className="w-4 h-4" />
          Wyloguj
        </Button>
      </div>

      {/* Sidebar */}
      <aside
        className="flex flex-col gap-0.5 p-3 border-r overflow-y-auto"
        style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)" }}
      >
        <div
          className="text-[10px] font-bold uppercase tracking-wider px-2 py-3 pb-1"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Przestrzenie
        </div>
        <button
          onClick={() => onSpaceChange("all")}
          className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full"
          style={{
            color: currentSpace === "all" ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            background: currentSpace === "all" ? "var(--color-background-primary)" : "transparent",
            fontWeight: currentSpace === "all" ? 600 : 400,
            boxShadow: currentSpace === "all" ? "0 1px 2px rgba(0,0,0,0.04)" : "none",
          }}
        >
          <FolderOpen className="w-[18px] h-[18px]" style={{ color: currentSpace === "all" ? "var(--color-accent)" : "var(--color-text-tertiary)" }} />
          Wszystkie notatki
        </button>
        {spaces.map((s) => (
          <button
            key={s.bank_id}
            onClick={() => onSpaceChange(s.bank_id)}
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full"
            style={{
              color: currentSpace === s.bank_id ? "var(--color-text-primary)" : "var(--color-text-secondary)",
              background: currentSpace === s.bank_id ? "var(--color-background-primary)" : "transparent",
              fontWeight: currentSpace === s.bank_id ? 600 : 400,
              boxShadow: currentSpace === s.bank_id ? "0 1px 2px rgba(0,0,0,0.04)" : "none",
            }}
            title={s.name}
          >
            <span className="w-2 h-2 rounded-full shrink-0" style={{ background: spaceColor(s.space_type) }} />
            <span className="truncate">{s.name}</span>
          </button>
        ))}

        <div
          className="text-[10px] font-bold uppercase tracking-wider px-2 py-3 pb-1 mt-3"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Menu
        </div>
        <button
          onClick={() => onShowTab("inbox")}
          className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full"
          style={{
            color: activeTab === "inbox" ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            background: activeTab === "inbox" ? "var(--color-background-primary)" : "transparent",
            fontWeight: activeTab === "inbox" ? 600 : 400,
            boxShadow: activeTab === "inbox" ? "0 1px 2px rgba(0,0,0,0.04)" : "none",
          }}
        >
          <Inbox className="w-[18px] h-[18px]" style={{ color: activeTab === "inbox" ? "var(--color-accent)" : "var(--color-text-tertiary)" }} />
          Inbox
          {inboxCount > 0 && (
            <span className="ml-auto text-[11px] px-1.5 py-0.5 rounded-full font-semibold" style={{ background: "color-mix(in oklch, var(--color-danger) 15%, transparent)", color: "var(--color-danger)" }}>
              {inboxCount}
            </span>
          )}
        </button>
        <button
          onClick={() => onShowTab("settings")}
          className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full"
          style={{
            color: activeTab === "settings" ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            background: activeTab === "settings" ? "var(--color-background-primary)" : "transparent",
            fontWeight: activeTab === "settings" ? 600 : 400,
            boxShadow: activeTab === "settings" ? "0 1px 2px rgba(0,0,0,0.04)" : "none",
          }}
        >
          <Settings className="w-[18px] h-[18px]" style={{ color: activeTab === "settings" ? "var(--color-accent)" : "var(--color-text-tertiary)" }} />
          Ustawienia
        </button>
      </aside>

      {/* Main Content */}
      <main className="overflow-auto p-5" style={{ background: "var(--color-background-primary)" }}>
        {children}
      </main>

      {/* Chat */}
      <div
        className="flex flex-col border-l"
        style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}
      >
        <div
          className="px-4 py-3.5 border-b text-[13px] font-bold"
          style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", color: "var(--color-text-primary)" }}
        >
          Asystent WenetBrain
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="flex flex-col gap-3">
            {chatMessages.length === 0 && (
              <div
                className="text-sm p-3 rounded-lg"
                style={{ background: "var(--color-background-secondary)", color: "var(--color-text-primary)", border: "1px solid var(--color-border-primary)" }}
              >
                Witaj! Jestem Twoim asystentem wiedzy organizacyjnej. W czym mogę pomóc?
              </div>
            )}
            {chatMessages.map((m, i) => (
              <div
                key={i}
                className="text-sm p-3 rounded-lg max-w-[92%]"
                style={
                  m.role === "user"
                    ? { background: "color-mix(in oklch, var(--color-accent) 10%, transparent)", color: "var(--color-accent)", alignSelf: "flex-end", borderBottomRightRadius: "2px" }
                    : { background: "var(--color-background-secondary)", color: "var(--color-text-primary)", alignSelf: "flex-start", border: "1px solid var(--color-border-primary)", borderBottomLeftRadius: "2px" }
                }
              >
                {m.text}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="flex items-center gap-2 p-3 border-t" style={{ borderColor: "var(--color-border-primary)", background: "var(--color-background-primary)" }}>
          <Input
            value={chatInput}
            onChange={(e) => onChatInputChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSendChat()}
            placeholder="Zapytaj o coś..."
            className="flex-1 text-sm"
            style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-secondary)" }}
          />
          <Button variant="outline" size="icon" onClick={onSendChat}>
            <ArrowUp className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
