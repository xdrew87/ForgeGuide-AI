import { useState, useRef, DragEvent } from "react";
import { Upload, FileText, CheckCircle, XCircle, Loader2, X } from "lucide-react";
import { api, Document, Equipment } from "../lib/api";
import { StatusDot, Badge } from "./ui";
import clsx from "clsx";

interface Props {
  equipment: Equipment[];
  documents: Document[];
  onUploaded: () => void;
}

export default function DocumentUploader({ equipment, documents, onUploaded }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [selectedEquipment, setSelectedEquipment] = useState("");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  }

  function pickFile(f: File) {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setPendingFile(f);
    if (!title) setTitle(f.name.replace(/\.pdf$/i, "").replace(/[-_]/g, " "));
    setError(null);
  }

  async function submit() {
    if (!pendingFile || !title.trim()) return;
    setUploading(true);
    setError(null);
    try {
      await api.documents.upload(pendingFile, title.trim(), selectedEquipment || undefined);
      setPendingFile(null);
      setTitle("");
      setSelectedEquipment("");
      onUploaded();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => !pendingFile && fileRef.current?.click()}
        className={clsx(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer",
          dragOver ? "border-forge-accent bg-forge-accent/10" : "border-forge-line hover:border-forge-mid",
          pendingFile && "border-emerald-500/50 bg-emerald-900/10 cursor-default"
        )}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) pickFile(f); }}
        />

        {pendingFile ? (
          <div className="flex items-center gap-3 justify-center">
            <FileText className="w-6 h-6 text-emerald-400" />
            <div className="text-left">
              <p className="text-sm font-medium text-white">{pendingFile.name}</p>
              <p className="text-xs text-forge-muted">{(pendingFile.size / 1024).toFixed(0)} KB</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setPendingFile(null); setTitle(""); }}
              className="ml-2 text-forge-muted hover:text-red-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="w-7 h-7 mx-auto mb-3 text-forge-muted" strokeWidth={1.75} />
            <p className="text-sm text-white/70">Drop a PDF manual here, or click to browse</p>
            <p className="text-xs text-forge-muted mt-1">Max 50 MB · PDF only</p>
          </>
        )}
      </div>

      {/* Metadata fields */}
      {pendingFile && (
        <div className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Document title"
            className="w-full bg-forge-navy border border-forge-line rounded-lg px-3 py-2 text-sm text-white placeholder-forge-muted focus:outline-none focus:border-forge-accent"
          />
          <select
            value={selectedEquipment}
            onChange={(e) => setSelectedEquipment(e.target.value)}
            className="w-full bg-forge-navy border border-forge-line rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-forge-accent"
          >
            <option value="">No equipment (global)</option>
            {equipment.map((eq) => (
              <option key={eq.id} value={eq.id}>
                {eq.manufacturer} {eq.model}
              </option>
            ))}
          </select>
          <button
            onClick={submit}
            disabled={uploading || !title.trim()}
            className="w-full py-2 rounded-lg bg-forge-accent text-white text-sm font-medium hover:bg-forge-accentDim disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading…</> : "Upload & ingest"}
          </button>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </div>
      )}

      {/* Existing docs */}
      {documents.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-forge-muted/80">Indexed documents</p>
          {documents.map((doc) => (
            <div key={doc.id} className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-forge-navy/40 border border-forge-line">
              <StatusDot status={doc.ingestion_status} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{doc.title}</p>
                <p className="text-xs text-forge-muted">{doc.page_count ? `${doc.page_count} pages` : doc.ingestion_status}</p>
              </div>
              <Badge variant={doc.ingestion_status === "complete" ? "success" : doc.ingestion_status === "failed" ? "danger" : "warn"}>
                {doc.ingestion_status}
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
