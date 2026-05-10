import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiGet, apiPost, type User } from "@/api";

export function SettingsView() {
  const [user, setUser] = useState<User | null>(null);
  const [clickupList, setClickupList] = useState("");

  useEffect(() => {
    apiGet<User>("/api/auth/me").then((u) => {
      setUser(u);
    });
  }, []);

  async function saveIntegrations() {
    try {
      await apiPost("/api/auth/me/integrations", { clickup_list_id: clickupList });
      alert("Zapisano integracje!");
    } catch (e) {
      alert(String(e));
    }
  }

  return (
    <div className="space-y-4 max-w-xl">
      <div>
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>Ustawienia</h2>
        <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Twoje konto i integracje</p>
      </div>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="mb-4" style={{ background: "var(--color-background-secondary)" }}>
          <TabsTrigger value="account" className="text-xs">Konto</TabsTrigger>
          <TabsTrigger value="integrations" className="text-xs">Integracje</TabsTrigger>
        </TabsList>

        <TabsContent value="account">
          <Card style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Imię i nazwisko</Label>
                <p className="text-sm py-2 px-3 rounded-md" style={{ background: "var(--color-background-tertiary)", color: "var(--color-text-primary)" }}>{user?.name || "—"}</p>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Email</Label>
                <p className="text-sm py-2 px-3 rounded-md" style={{ background: "var(--color-background-tertiary)", color: "var(--color-text-primary)" }}>{user?.email || "—"}</p>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Zespół</Label>
                <p className="text-sm py-2 px-3 rounded-md" style={{ background: "var(--color-background-tertiary)", color: "var(--color-text-primary)" }}>{user?.team || "—"}</p>
              </div>
              <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Dane konta można zmienić wyłącznie w panelu administracyjnym.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations">
          <div className="space-y-3">
            <Card style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center border" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
                  <span className="material-icons-outlined text-lg" style={{ color: "var(--color-text-secondary)" }}>task_alt</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">ClickUp</div>
                  <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Eksportuj zadania do listy ClickUp</div>
                </div>
                <Button size="sm" variant="outline" className="text-xs">Połącz</Button>
              </CardContent>
            </Card>
            <Card style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center border" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
                  <span className="material-icons-outlined text-lg" style={{ color: "var(--color-text-secondary)" }}>event</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">Microsoft Outlook</div>
                  <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Synchronizuj spotkania z kalendarzem</div>
                </div>
                <Button size="sm" variant="outline" className="text-xs">Połącz</Button>
              </CardContent>
            </Card>
            <Card style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
              <CardContent className="p-4 space-y-3">
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>ClickUp — ID listy (personal list)</Label>
                  <Input value={clickupList} onChange={(e) => setClickupList(e.target.value)} placeholder="np. 123456789" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
                </div>
                <Button size="sm" onClick={saveIntegrations} style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}>Zapisz integracje</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
