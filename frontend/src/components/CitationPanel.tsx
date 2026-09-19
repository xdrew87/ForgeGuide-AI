import { useState } from "react";
import { FileText, ChevronDown, ChevronUp, AlertTriangle, BookOpen, Eye } from "lucide-react";
import { Citation } from "../lib/api";
import { Badge, Card, SectionLabel } from "./ui";
import clsx from "clsx";

interface Props {
  citations: Citation[];
  evidence_sufficient: boolean;
  confidence: number;
  chunks_used: number;
  onCitationClick?: (citation: Citation) => void;
}

function TableExcerpt({ text }: { text: string }) {
  const rows = text
    .split("\n")
    .map((r) => r.trim())
    .filter((r) => r.startsWith("|"))
    .filter((r) => !/^\|[\s-:|]+\|$/.test(r)) // drop markdown separator row
    .map((r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));

  if (rows.length === 0) {
    return <p className="text-xs text-white/70 leading-relaxed whitespace-pre-wrap">{text}</p>;
  }

  return (
    <table className="w-full text-xs border-collapse">
      <tbody>
        {rows.map((cells, ri) => (
          <tr key={ri} className={ri === 0 ? "font-semibold text-white/90" : "text-white/70"}>
            {cells.map((cell, ci) => (
              <td key={ci} className="border border-forge-line px-2 py-1 align-top">{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function CitationPanel({ citations, evidence_sufficient, confidence, chunks_used, onCitationClick }: Props) {
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

  // Group citations by source document, preserving first-seen order.
  const groups: { document_id: string; document: string; items: Citation[] }[] = [];
  for (const c of citations) {
    let g = groups.find((g) => g.document_id === c.document_id);
    if (!g) {
      g = { document_id: c.document_id, document: c.document, items: [] };
      groups.push(g);
    }
    g.items.push(c);
  }
  for (const g of groups) g.items.sort((a, b) => a.page - b.page);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <SectionLabel>Sources ({citations.length})</SectionLabel>
        <div className="flex items-center gap-2">
          {groups.length > 1 && <Badge variant="default">{groups.length} source documents</Badge>}
          <span className="text-xs text-forge-muted">{chunks_used} chunks retrieved</span>
        </div>
      </div>

      {citations.length === 0 && (
        <p className="text-xs text-forge-muted italic">No citations parsed from response.</p>
      )}

      {groups.map((group) => (
        <div key={group.document_id || group.document} className="space-y-2">
          {groups.length > 1 && <SectionLabel>{group.document}</SectionLabel>}

          {group.items.map((c, i) => {
            const key = `${c.document_id}-${c.page}-${i}`;
            const open = expanded === key;
            return (
              <Card key={key} className="overflow-hidden">
                <div className="flex items-start gap-1">
                  <button
                    onClick={() => setExpanded(open ? null : key)}
                    className="flex-1 flex items-start gap-2.5 p-3 text-left hover:bg-white/[0.03] transition-colors min-w-0"
                  >
                    <FileText className="w-4 h-4 text-forge-accent flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-medium text-white/90 truncate">{c.document}</span>
                        <Badge variant="muted">pg {c.page}</Badge>
                        {c.chunk_type === "table" && <Badge variant="warn">Table</Badge>}
                        {c.section && <Badge variant="default">{c.section.slice(0, 40)}</Badge>}
                      </div>
                      {!open && (
                        <p className="text-xs text-forge-muted mt-1 truncate">{c.excerpt}</p>
                      )}
                    </div>
                    {open ? (
                      <ChevronUp className="w-3.5 h-3.5 text-forge-muted flex-shrink-0 mt-0.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-forge-muted flex-shrink-0 mt-0.5" />
                    )}
                  </button>
                  {onCitationClick && (
                    <button
                      onClick={() => onCitationClick(c)}
                      title="View in document"
                      className="p-2.5 mt-1 mr-1 rounded-md text-forge-muted hover:text-forge-accent hover:bg-white/5 transition-colors flex-shrink-0"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {open && (
                  <div className="border-t border-forge-line px-3 py-2.5 bg-forge-navy/60">
                    <div className="flex items-center gap-1.5 mb-2">
                      <BookOpen className="w-3.5 h-3.5 text-forge-muted" />
                      <span className="text-xs font-medium text-forge-muted">Supporting text</span>
                    </div>
                    {c.chunk_type === "table" ? (
                      <TableExcerpt text={c.excerpt} />
                    ) : (
                      <p className="text-xs text-white/70 leading-relaxed whitespace-pre-wrap">{c.excerpt}</p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      ))}
    </div>
  );
}
