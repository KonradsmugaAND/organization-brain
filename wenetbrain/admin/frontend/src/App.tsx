import { useState } from "react";
import { Layout } from "@/components/Layout";
import { SpacesView } from "@/components/SpacesView";
import { UsersView } from "@/components/UsersView";

function App() {
  const [activeTab, setActiveTab] = useState<"spaces" | "users">("spaces");

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === "spaces" && <SpacesView />}
      {activeTab === "users" && <UsersView />}
    </Layout>
  );
}

export default App;
