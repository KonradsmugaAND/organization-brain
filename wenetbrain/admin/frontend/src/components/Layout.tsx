import { useState, useEffect } from "react";
import { FolderOpen, Users, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/api";

interface LayoutProps {
  children: React.ReactNode;
  activeTab: "spaces" | "users";
  onTabChange: (tab: "spaces" | "users") => void;
}

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  const [userName, setUserName] = useState("—");

  useEffect(() => {
    apiGet<{ name?: string; id: string }>("/api/auth/me")
      .then((u) => setUserName(u.name || u.id))
      .catch(() => {});
  }, []);

  function logout() {
    localStorage.removeItem("wenetbrain_admin_token");
    window.location.href = "/login.html";
  }

  return (
    <div className="grid h-screen grid-rows-[52px_1fr] grid-cols-[240px_1fr]" style={{ background: "var(--color-background-primary)" }}>
      {/* Topbar */}
      <div
        className="col-span-2 flex items-center px-4 gap-3 border-b z-50"
        style={{
          background: "var(--color-background-primary)",
          borderColor: "var(--color-border-primary)",
        }}
      >
        <span className="text-[15px] font-extrabold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          WenetBrain Admin
        </span>
        <div className="flex-1" />
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
        className="flex flex-col gap-1 p-3 border-r overflow-y-auto"
        style={{
          background: "var(--color-background-secondary)",
          borderColor: "var(--color-border-primary)",
        }}
      >
        <div
          className="text-[10px] font-bold uppercase tracking-wider px-2 py-3 pb-1"
          style={{ color: "var(--color-text-tertiary)" }}
        >
          Menu
        </div>
        <button
          onClick={() => onTabChange("spaces")}
          className={`flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full ${
            activeTab === "spaces"
              ? "font-semibold shadow-sm"
              : ""
          }`}
          style={{
            color: activeTab === "spaces" ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            background: activeTab === "spaces" ? "var(--color-background-primary)" : "transparent",
          }}
        >
          <FolderOpen className="w-[18px] h-[18px]" style={{ color: activeTab === "spaces" ? "var(--color-accent)" : "var(--color-text-tertiary)" }} />
          Przestrzenie
        </button>
        <button
          onClick={() => onTabChange("users")}
          className={`flex items-center gap-2.5 px-2 py-1.5 rounded-md text-[13px] transition-all cursor-pointer border-none bg-transparent text-left w-full ${
            activeTab === "users"
              ? "font-semibold shadow-sm"
              : ""
          }`}
          style={{
            color: activeTab === "users" ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            background: activeTab === "users" ? "#fff" : "transparent",
          }}
        >
          <Users className="w-[18px] h-[18px]" style={{ color: activeTab === "users" ? "var(--color-accent)" : "var(--color-text-tertiary)" }} />
          Użytkownicy
        </button>
      </aside>

      {/* Main */}
      <main className="overflow-auto p-5" style={{ background: "var(--color-background-primary)" }}>
        {children}
      </main>
    </div>
  );
}
