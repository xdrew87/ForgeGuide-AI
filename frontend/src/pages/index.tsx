import { useState, useEffect, useCallback } from "react";
import Head from "next/head";
import { ShieldCheck, Wifi, WifiOff, ChevronLeft, ChevronRight } from "lucide-react";
import { api, Equipment, Document } from "../lib/api";
import ChatInterface from "../components/ChatInterface";
import DocumentUploader from "../components/DocumentUploader";
import EquipmentManager from "../components/EquipmentManager";
import { Spinner } from "../components/ui";
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
      <Head>
        <title>ForgeGuide AI</title>
      </Head>

      {/* Top bar */}
      <header className="flex items-center justify-between px-5 h-14 border-b border-forge-line bg-forge-navy/95 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-6 h-6 text-forge-accent" strokeWidth={2.25} />
          <div className="flex items-baseline gap-3">
            <h1 className="text-[15px] font-bold tracking-tight leading-none">
              <span className="text-white">ForgeGuide</span>
              <span className="text-forge-accent"> AI</span>
            </h1>
            <span className="hidden sm:inline text-[11px] text-forge-muted leading-none">
              Evidence-grounded maintenance
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            {connected === null ? (
              <Spinner size={3} />
            ) : connected ? (
              <><Wifi className="w-3.5 h-3.5 text-emerald-400" /><span className="text-emerald-400 font-medium">Connected</span></>
            ) : (
              <><WifiOff className="w-3.5 h-3.5 text-red-400" /><span className="text-red-400 font-medium">API offline</span></>
            )}
          </div>
          <span className="text-[10px] font-semibold text-forge-accent bg-forge-accent/10 px-2 py-0.5 rounded-full">
            DEMO
          </span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden relative">
        {/* Sidebar */}
        <aside className={clsx(
          "flex-shrink-0 border-r border-forge-line bg-forge-steel transition-all duration-200 flex flex-col",
          sidebarOpen ? "w-72" : "w-0"
        )}>
          {sidebarOpen && (
            <div className="flex flex-col flex-1 overflow-hidden w-72">
              {/* Tabs */}
              <div className="flex border-b border-forge-line px-1 pt-1">
                {(["docs", "equipment"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={clsx(
                      "flex-1 text-sm font-medium py-2.5 rounded-t-md transition-colors",
                      activeTab === tab
                        ? "text-white bg-forge-navy border-b-2 border-forge-accent"
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
              <div className="p-3 border-t border-forge-line">
                <div className="rounded-lg bg-forge-accent/8 border border-forge-accent/25 px-3 py-2.5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-forge-accent" />
                    <p className="text-xs font-semibold text-forge-accent">Safety guarantee</p>
                  </div>
                  <p className="text-xs text-white/55 leading-relaxed">
                    Every answer is grounded in uploaded documentation. No procedure is generated without supporting evidence.
                  </p>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Sidebar toggle */}
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          className="absolute top-3 z-10 w-6 h-6 rounded-full bg-forge-mid border border-forge-line flex items-center justify-center text-forge-muted hover:text-white hover:border-forge-accent transition-all"
          style={{ left: sidebarOpen ? "17.5rem" : "0.5rem" }}
        >
          {sidebarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </button>

        {/* Main: Chat */}
        <main className="flex-1 overflow-hidden">
          <ChatInterface equipment={equipment} />
        </main>
      </div>
    </div>
  );
}
