import { useState, useEffect, useCallback } from "react";
import { ShieldCheck, Wifi, WifiOff, PanelLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { api, Equipment, Document } from "../lib/api";
import ChatInterface from "../components/ChatInterface";
import DocumentUploader from "../components/DocumentUploader";
import EquipmentManager from "../components/EquipmentManager";
import { SectionLabel, Spinner } from "../components/ui";
import clsx from "clsx";

export default function Home() {
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<"docs" | "equipment">("docs");

  const loadEquipment = useCallback(async () => {
    try { setEquipment(await api.equipment.list()); } catch {}
  }, []);

  const loadDocuments = useCallback(async () => {
    try { setDocuments(await api.documents.list()); } catch {}
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      await api.health();
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    // Fetch-on-mount, not a state-sync effect; setState happens inside the async callbacks after an await.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    checkHealth();
    loadEquipment();
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000); // Poll for ingestion status
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-forge-navy overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 bg-forge-navy/80 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-forge-accent/20 border border-forge-accent/40 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4 text-forge-accent" />
          </div>
          <div>
            <span className="text-sm font-semibold text-white tracking-tight">ForgeGuide AI</span>
            <span className="ml-2 text-[9px] font-mono text-forge-muted uppercase tracking-widest">Evidence-Grounded Maintenance</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            {connected === null ? (
              <Spinner size={3} />
            ) : connected ? (
              <><Wifi className="w-3.5 h-3.5 text-green-400" /><span className="text-[10px] font-mono text-green-400">Connected</span></>
            ) : (
              <><WifiOff className="w-3.5 h-3.5 text-red-400" /><span className="text-[10px] font-mono text-red-400">API offline</span></>
            )}
          </div>
          <span className="text-[9px] font-mono text-forge-muted border border-white/10 px-1.5 py-0.5 rounded">DEMO</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={clsx(
          "flex-shrink-0 border-r border-white/10 bg-forge-steel/20 transition-all duration-200 flex flex-col",
          sidebarOpen ? "w-72" : "w-10"
        )}>
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="absolute -right-3 top-16 z-10 w-6 h-6 rounded-full bg-forge-steel border border-white/20 flex items-center justify-center text-forge-muted hover:text-white transition-colors"
          >
            {sidebarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>

          {sidebarOpen && (
            <div className="flex flex-col flex-1 overflow-hidden">
              {/* Tabs */}
              <div className="flex border-b border-white/10">
                {(["docs", "equipment"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={clsx(
                      "flex-1 text-[10px] font-mono uppercase tracking-widest py-2.5 transition-colors",
                      activeTab === tab
                        ? "text-forge-accent border-b-2 border-forge-accent bg-forge-accent/5"
                        : "text-forge-muted hover:text-white"
                    )}
                  >
                    {tab === "docs" ? "Documents" : "Equipment"}
                  </button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                {activeTab === "docs" ? (
                  <DocumentUploader
                    equipment={equipment}
                    documents={documents}
                    onUploaded={loadDocuments}
                  />
                ) : (
                  <EquipmentManager equipment={equipment} onCreated={loadEquipment} />
                )}
              </div>

              {/* Safety notice */}
              <div className="p-3 border-t border-white/10">
                <div className="rounded-lg bg-forge-accent/10 border border-forge-accent/20 px-3 py-2">
                  <p className="text-[9px] font-mono text-forge-accent/80 uppercase tracking-widest mb-1">Safety Guarantee</p>
                  <p className="text-[10px] text-white/50 leading-relaxed">
                    All answers are grounded in uploaded documentation. No procedures are generated without evidence.
                  </p>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Main: Chat */}
        <main className="flex-1 overflow-hidden">
          <ChatInterface equipment={equipment} />
        </main>
      </div>
    </div>
  );
}
