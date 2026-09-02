import { useState } from "react";
import { FileText, ChevronDown, ChevronUp, AlertTriangle, BookOpen } from "lucide-react";
import { Citation } from "../lib/api";
import { Badge, Card, SectionLabel } from "./ui";
import clsx from "clsx";

interface Props {
  citations: Citation[];
  evidence_sufficient: boolean;
  confidence: number;
  chunks_used: number;
}

export default function CitationPanel({ citations, evidence_sufficient, confidence, chunks_used }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!evidence_sufficient) {
    return (
      <div className="rounded-lg border border-red-700/50 bg-red-950/30 p-4 flex gap-3">
        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-red-300 mb-1">Insufficient evidence</p>
          <p className="text-xs text-red-400/80">
            No supporting documentation was found. Upload the relevant manual before asking this question.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <SectionLabel>Sources ({citations.length})</SectionLabel>
        <span className="text-xs text-forge-muted">{chunks_used} chunks retrieved</span>
      </div>

      {citations.length === 0 && (
        <p className="text-xs text-forge-muted italic">No citations parsed from response.</p>
      )}

      {citations.map((c, i) => {
        const key = `${c.document_id}-${c.page}-${i}`;
        const open = expanded === key;
        return (
          <Card key={key} className="overflow-hidden">
            <button
              onClick={() => setExpanded(open ? null : key)}
              className="w-full flex items-start gap-2.5 p-3 text-left hover:bg-white/[0.03] transition-colors"
            >
              <FileText className="w-4 h-4 text-forge-accent flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-medium text-white/90 truncate">{c.document}</span>
                  <Badge variant="muted">pg {c.page}</Badge>
                  {c.section && <Badge variant="default">{c.section.slice(0, 40)}</Badge>}
                </div>
                {!open && (
                  <p className="text-xs text-forge-muted mt-1 truncate">{c.excerpt}</p>
                )}
              </div>
              {open ? (
                <ChevronUp className="w-3.5 h-3.5 text-forge-muted flex-shrink-0" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-forge-muted flex-shrink-0" />
              )}
            </button>

            {open && (
              <div className="border-t border-forge-line px-3 py-2.5 bg-forge-navy/60">
                <div className="flex items-center gap-1.5 mb-2">
                  <BookOpen className="w-3.5 h-3.5 text-forge-muted" />
                  <span className="text-xs font-medium text-forge-muted">Supporting text</span>
                </div>
                <p className="text-xs text-white/70 leading-relaxed whitespace-pre-wrap">{c.excerpt}</p>
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
