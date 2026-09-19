import { ReactNode, useEffect } from "react";
import { X } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

export default function Modal({ open, onClose, title, children }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-lg border border-forge-line bg-forge-steel shadow-panel overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 h-12 border-b border-forge-line flex-shrink-0">
          <span className="text-sm font-medium text-white/90 truncate">{title}</span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-forge-muted hover:text-white hover:bg-white/5 transition-colors flex-shrink-0"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-auto">{children}</div>
      </div>
    </div>
  );
}
