import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, AlertTriangle, ShieldCheck, Loader2, ImagePlus } from "lucide-react";
import { api, AskResponse, Equipment, ImageAnalysis } from "../lib/api";
import CitationPanel from "./CitationPanel";
import { ConfidenceBar, Badge } from "./ui";
import clsx from "clsx";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  qaData?: AskResponse;
  imageData?: ImageAnalysis;
}

interface Props {
  equipment: Equipment[];
}

export default function ChatInterface({ equipment }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [selectedEquipment, setSelectedEquipment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLInputElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setError(null);

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.chat.ask(q, selectedEquipment || undefined, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => [...prev, {
        id: res.message_id,
        role: "assistant",
        content: res.answer,
        qaData: res,
      }]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function analyzeImage(file: File) {
    setImageLoading(true);
    setError(null);
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: `📷 Image uploaded: ${file.name}`,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await api.multimodal.analyzeImage(file, selectedEquipment || undefined);
      const summary = res.fault_codes.length > 0
        ? `Detected fault codes: **${res.fault_codes.join(", ")}**`
        : "No fault codes detected in image.";
      setMessages((prev) => [...prev, {
        id: Date.now().toString() + "img",
        role: "assistant",
        content: res.qa_answer
          ? `${summary}\n\n${res.qa_answer}`
          : summary,
        imageData: res,
      }]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setImageLoading(false);
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  const displayAnswer = (raw: string) =>
    raw.replace(/^<<INSUFFICIENT_EVIDENCE>>\n\n?/, "").trim();

  return (
    <div className="flex flex-col h-full">
      {/* Equipment selector */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/10 bg-forge-navy/40">
        <span className="text-[10px] font-mono text-forge-muted uppercase tracking-widest">Equipment filter</span>
        <select
          value={selectedEquipment}
          onChange={(e) => { setSelectedEquipment(e.target.value); setConversationId(undefined); setMessages([]); }}
          className="flex-1 bg-forge-navy border border-white/10 rounded-md px-2 py-1 text-xs text-white focus:outline-none focus:border-forge-accent"
        >
          <option value="">All documents</option>
          {equipment.map((eq) => (
            <option key={eq.id} value={eq.id}>{eq.manufacturer} {eq.model}</option>
          ))}
        </select>
        {conversationId && (
          <button
            onClick={() => { setConversationId(undefined); setMessages([]); }}
            className="text-[10px] font-mono text-forge-muted hover:text-forge-accent transition-colors px-2 py-1 rounded border border-white/10"
          >
            New chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <ShieldCheck className="w-10 h-10 text-forge-accent opacity-60" />
            <div>
              <p className="text-sm font-semibold text-white/70">ForgeGuide AI</p>
              <p className="text-xs text-forge-muted mt-1 max-w-xs">
                Ask a maintenance question. Every answer is grounded in uploaded documentation — no unsupported recommendations.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-2 mt-2 w-full max-w-sm">
              {[
                "What does fault E17 indicate on the MX-400?",
                "How do I inspect the cooling fan?",
                "What is the air filter cleaning procedure?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  className="text-xs text-left px-3 py-2 rounded-lg border border-white/10 text-white/60 hover:border-forge-accent hover:text-white transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "assistant" && (
              <div className="w-6 h-6 rounded-full bg-forge-accent/20 border border-forge-accent/40 flex-shrink-0 flex items-center justify-center mt-0.5">
                <ShieldCheck className="w-3 h-3 text-forge-accent" />
              </div>
            )}

            <div className={clsx("max-w-[85%] space-y-2", msg.role === "user" ? "items-end" : "items-start")}>
              <div className={clsx(
                "rounded-xl px-4 py-3 text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-forge-mid/50 text-white rounded-tr-sm"
                  : "bg-forge-steel/40 border border-white/10 text-white/90 rounded-tl-sm"
              )}>
                {msg.role === "assistant" && msg.qaData && !msg.qaData.evidence_sufficient && (
                  <div className="flex items-center gap-1.5 mb-2 text-red-400">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Insufficient Evidence</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{msg.role === "assistant" ? displayAnswer(msg.content) : msg.content}</p>
              </div>

              {/* QA metadata */}
              {msg.qaData && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={msg.qaData.evidence_sufficient ? "success" : "danger"}>
                      {msg.qaData.evidence_sufficient ? "Evidence found" : "No evidence"}
                    </Badge>
                    <div className="w-28">
                      <ConfidenceBar value={msg.qaData.confidence} sufficient={msg.qaData.evidence_sufficient} />
                    </div>
                  </div>
                  {msg.qaData.citations.length > 0 && (
                    <CitationPanel
                      citations={msg.qaData.citations}
                      evidence_sufficient={msg.qaData.evidence_sufficient}
                      confidence={msg.qaData.confidence}
                      chunks_used={msg.qaData.chunks_used}
                    />
                  )}
                </div>
              )}

              {/* Image analysis metadata */}
              {msg.imageData && msg.imageData.fault_codes.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {msg.imageData.fault_codes.map((code) => (
                    <Badge key={code} variant="warn">🔴 {code}</Badge>
                  ))}
                </div>
              )}
              {msg.imageData?.qa_citations && msg.imageData.qa_citations.length > 0 && (
                <CitationPanel
                  citations={msg.imageData.qa_citations}
                  evidence_sufficient={msg.imageData.qa_evidence_sufficient}
                  confidence={msg.imageData.qa_confidence}
                  chunks_used={msg.imageData.qa_citations.length}
                />
              )}
            </div>
          </div>
        ))}

        {(loading || imageLoading) && (
          <div className="flex gap-3">
            <div className="w-6 h-6 rounded-full bg-forge-accent/20 border border-forge-accent/40 flex-shrink-0 flex items-center justify-center">
              <Loader2 className="w-3 h-3 text-forge-accent animate-spin" />
            </div>
            <div className="bg-forge-steel/40 border border-white/10 rounded-xl rounded-tl-sm px-4 py-3">
              <span className="text-xs text-forge-muted font-mono">
                {imageLoading ? "Analyzing image…" : "Retrieving evidence…"}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/30 border border-red-800/40 rounded-lg px-3 py-2">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="border-t border-white/10 p-3 bg-forge-navy/60">
        <div className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a maintenance question… (Enter to send)"
            rows={2}
            className="flex-1 bg-forge-navy/80 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-forge-muted focus:outline-none focus:border-forge-accent resize-none leading-relaxed"
          />
          <div className="flex flex-col gap-1.5">
            <button
              onClick={() => imageRef.current?.click()}
              title="Upload equipment image"
              className="p-2 rounded-lg border border-white/10 text-forge-muted hover:text-forge-accent hover:border-forge-accent transition-colors"
            >
              <ImagePlus className="w-4 h-4" />
            </button>
            <button
              onClick={send}
              disabled={!input.trim() || loading}
              className="p-2 rounded-lg bg-forge-accent hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
        <input
          ref={imageRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) analyzeImage(f); }}
        />
      </div>
    </div>
  );
}
