import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import { NotesView } from "@/components/NotesView";
import { InboxView } from "@/components/InboxView";
import { SettingsView } from "@/components/SettingsView";
import { SearchView } from "@/components/SearchView";
import { MeetingModal } from "@/components/MeetingModal";
import { NoteModal } from "@/components/NoteModal";
import { apiGet, apiPost, type Space, type User } from "@/api";

export default function App() {
  const [currentSpace, setCurrentSpace] = useState("all");
  const [activeTab, setActiveTab] = useState("notes");
  const [searchQuery, setSearchQuery] = useState("");
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [userId, setUserId] = useState("default_user");
  const [inboxCount, setInboxCount] = useState(0);
  const [chatMessages, setChatMessages] = useState<{ role: "user" | "ai"; text: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [meetingOpen, setMeetingOpen] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);
  const [notesRefresh, setNotesRefresh] = useState(0);

  useEffect(() => {
    apiGet<User>("/api/auth/me").then((u) => setUserId(u.id));
    apiGet<Space[]>("/api/my/spaces").then(setSpaces);

    const onSearch = (e: Event) => {
      const q = (e as CustomEvent).detail;
      setSearchQuery(q);
      setActiveTab("search");
    };
    window.addEventListener("global-search", onSearch);
    return () => window.removeEventListener("global-search", onSearch);
  }, []);

  function handleSpaceChange(bankId: string) {
    setCurrentSpace(bankId);
    setActiveTab("notes");
  }

  function handleShowTab(tab: string) {
    setActiveTab(tab);
  }

  async function sendChat() {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatMessages((prev) => [...prev, { role: "user", text: msg }]);
    setChatInput("");
    try {
      const res = await apiPost<{ answer: string }>("/api/chat", {
        query: msg,
        user_id: userId,
      });
      setChatMessages((prev) => [...prev, { role: "ai", text: res.answer || "..." }]);
    } catch {
      setChatMessages((prev) => [...prev, { role: "ai", text: "Przepraszam, wystąpił błąd." }]);
    }
  }

  return (
    <>
      <Layout
        chatMessages={chatMessages}
        chatInput={chatInput}
        onChatInputChange={setChatInput}
        onSendChat={sendChat}
        currentSpace={currentSpace}
        onSpaceChange={handleSpaceChange}
        onOpenMeetingModal={() => setMeetingOpen(true)}
        onShowTab={handleShowTab}
        activeTab={activeTab}
        inboxCount={inboxCount}
      >
        {activeTab === "notes" && (
          <NotesView spaceId={currentSpace} spaces={spaces} userId={userId} onOpenNoteModal={() => setNoteOpen(true)} onRefresh={notesRefresh} />
        )}
        {activeTab === "inbox" && <InboxView userId={userId} spaces={spaces} onCountChange={setInboxCount} />}
        {activeTab === "settings" && <SettingsView />}
        {activeTab === "search" && <SearchView query={searchQuery} />}
      </Layout>

      <MeetingModal open={meetingOpen} onClose={() => { setMeetingOpen(false); setNotesRefresh((n) => n + 1); }} />
      <NoteModal open={noteOpen} onClose={() => setNoteOpen(false)} spaces={spaces} defaultSpace={currentSpace === "all" ? undefined : currentSpace} onSaved={() => {
        setActiveTab("notes");
        setNotesRefresh((n) => n + 1);
      }} />
    </>
  );
}
