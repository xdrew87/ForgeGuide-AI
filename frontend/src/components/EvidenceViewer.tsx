import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { api, Citation, HighlightRect } from "../lib/api";
import Modal from "./Modal";
import { Badge, Card, Spinner } from "./ui";

interface Props {
  citation: Citation | null;
  onClose: () => void;
}

// Owns all per-citation state. Keyed by citation identity in the parent so
// React remounts it (fresh initial state) instead of needing an effect that
// resets state synchronously on citation change.
function EvidenceViewerContent({ citation }: { citation: Citation }) {
  const [rects, setRects] = useState<HighlightRect[] | null>(null);
  const [pageSize, setPageSize] = useState<{ w: number; h: number } | null>(null);
  const [imageError, setImageError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.documents
      .getHighlights(citation.document_id, citation.page, citation.chunk_id || undefined)
      .then((h) => {
        if (cancelled) return;
        setRects(h.rects);
        setPageSize({ w: h.page_width, h: h.page_height });
      })
      .catch(() => { if (!cancelled) setRects([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [citation]);

  const imgSrc = api.documents.pageImageUrl(citation.document_id, citation.page);

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant="muted">pg {citation.page}</Badge>
        {citation.section && <Badge variant="default">{citation.section}</Badge>}
        {citation.chunk_type === "table" && <Badge variant="warn">Table</Badge>}
        {!loading && rects !== null && rects.length === 0 && (
          <span className="flex items-center gap-1.5 text-xs text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5" />
            Exact passage not located — showing full page
          </span>
        )}
      </div>

      {imageError ? (
        <Card className="p-4">
          <p className="text-xs text-forge-muted mb-2">Page image unavailable — showing cited text instead:</p>
          <p className="text-sm text-white/80 whitespace-pre-wrap leading-relaxed">{citation.excerpt}</p>
        </Card>
      ) : (
        <div className="relative inline-block max-w-full">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-10">
              <Spinner />
            </div>
          )}
          {/* eslint-disable-next-line @next/next/no-img-element -- same-origin
              proxied route; next/image would require images.localPatterns
              config that doesn't exist in this project, see build plan */}
          <img
            src={imgSrc}
            alt={`${citation.document} page ${citation.page}`}
            onError={() => setImageError(true)}
            className="max-w-full rounded-md border border-forge-line"
          />
          {pageSize && rects && rects.map((r, i) => (
            <div
              key={i}
              className="absolute bg-amber-400/30 border border-amber-400/70 rounded-sm pointer-events-none"
              style={{
                left: `${(r.x0 / pageSize.w) * 100}%`,
                top: `${(r.y0 / pageSize.h) * 100}%`,
                width: `${((r.x1 - r.x0) / pageSize.w) * 100}%`,
                height: `${((r.y1 - r.y0) / pageSize.h) * 100}%`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function EvidenceViewer({ citation, onClose }: Props) {
  return (
    <Modal open={!!citation} onClose={onClose} title={citation ? `${citation.document} — page ${citation.page}` : ""}>
      {citation && <EvidenceViewerContent key={`${citation.document_id}-${citation.chunk_id}-${citation.page}`} citation={citation} />}
    </Modal>
  );
}
