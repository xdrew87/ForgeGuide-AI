// Relative URL — proxied to backend via src/pages/api/v1/[...slug].ts
// Works in browser regardless of Docker networking.
const API_PREFIX = "/api/v1";

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export interface Equipment {
  id: string;
  manufacturer: string;
  model: string;
  equipment_type: string;
}

export interface Document {
  id: string;
  title: string;
  filename: string;
  original_filename: string;
  page_count: number | null;
  ingestion_status: "pending" | "processing" | "complete" | "failed";
  equipment_id: string | null;
  error_message: string | null;
}

export interface Citation {
  document: string;
  page: number;
  section: string | null;
  excerpt: string;
  chunk_id: string;
  document_id: string;
}

export interface AskResponse {
  conversation_id: string;
  message_id: string;
  question: string;
  answer: string;
  citations: Citation[];
  evidence_sufficient: boolean;
  confidence: number;
  chunks_used: number;
}

export interface ImageAnalysis {
  raw_text: string;
  fault_codes: string[];
  suggested_query: string;
  qa_answer: string | null;
  qa_citations: Citation[];
  qa_evidence_sufficient: boolean;
  qa_confidence: number;
}

export const api = {
  equipment: {
    list: (): Promise<Equipment[]> => req("/equipment/"),
    create: (data: Omit<Equipment, "id">): Promise<Equipment> =>
      req("/equipment/", { method: "POST", body: JSON.stringify(data) }),
  },
  documents: {
    list: (equipment_id?: string): Promise<Document[]> =>
      req(`/documents/${equipment_id ? `?equipment_id=${equipment_id}` : ""}`),
    get: (id: string): Promise<Document> => req(`/documents/${id}`),
    upload: (file: File, title: string, equipment_id?: string): Promise<Document> => {
      const form = new FormData();
      form.append("file", file);
      form.append("title", title);
      if (equipment_id) form.append("equipment_id", equipment_id);
      return fetch(`${API_PREFIX}/documents/upload`, { method: "POST", body: form })
        .then(async (r) => {
          if (!r.ok) {
            const e = await r.json().catch(() => ({ detail: r.statusText }));
            throw new Error(e.detail || "Upload failed");
          }
          return r.json();
        });
    },
    delete: (id: string): Promise<void> =>
      req(`/documents/${id}`, { method: "DELETE" }),
  },
  chat: {
    ask: (question: string, equipment_id?: string, conversation_id?: string): Promise<AskResponse> =>
      req("/chat/ask", {
        method: "POST",
        body: JSON.stringify({ question, equipment_id, conversation_id }),
      }),
  },
  multimodal: {
    analyzeImage: (file: File, equipment_id?: string): Promise<ImageAnalysis> => {
      const form = new FormData();
      form.append("file", file);
      if (equipment_id) form.append("equipment_id", equipment_id);
      return fetch(`${API_PREFIX}/multimodal/analyze-image`, { method: "POST", body: form })
        .then(async (r) => {
          if (!r.ok) {
            const e = await r.json().catch(() => ({ detail: r.statusText }));
            throw new Error(e.detail || "Analysis failed");
          }
          return r.json();
        });
    },
  },
  health: (): Promise<{ status: string }> =>
    fetch(`/api/health`).then((r) => r.json()),
};
