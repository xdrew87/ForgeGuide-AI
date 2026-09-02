import { ReactNode } from "react";
import clsx from "clsx";

// ── Badge ────────────────────────────────────────────────────────────────────
export function Badge({ children, variant = "default" }: {
  children: ReactNode;
  variant?: "default" | "success" | "warn" | "danger" | "muted";
}) {
  return (
    <span className={clsx(
      "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium leading-5",
      variant === "success" && "bg-forge-safe/15 text-emerald-300 border border-forge-safe/30",
      variant === "warn"    && "bg-amber-500/15 text-amber-300 border border-amber-500/30",
      variant === "danger"  && "bg-forge-warn/15 text-red-300 border border-forge-warn/30",
      variant === "muted"   && "bg-white/5 text-forge-muted border border-forge-line",
      variant === "default" && "bg-forge-mid/40 text-sky-200 border border-forge-mid/60",
    )}>
      {children}
    </span>
  );
}

// ── ConfidenceBar ─────────────────────────────────────────────────────────────
export function ConfidenceBar({ value, sufficient }: { value: number; sufficient: boolean }) {
  const pct = Math.round(value * 100);
  const color = !sufficient ? "bg-red-500" : pct >= 70 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-500" : "bg-orange-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/8 rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono font-medium text-forge-muted w-9 text-right tabular-nums">{pct}%</span>
    </div>
  );
}

// ── StatusDot ────────────────────────────────────────────────────────────────
export function StatusDot({ status }: { status: string }) {
  const classes: Record<string, string> = {
    complete: "bg-emerald-400",
    processing: "bg-amber-400 animate-pulse",
    pending: "bg-forge-muted",
    failed: "bg-red-400",
  };
  return <span className={clsx("inline-block w-2 h-2 rounded-full flex-shrink-0", classes[status] ?? "bg-forge-muted")} />;
}

// ── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ size = 4 }: { size?: number }) {
  return (
    <svg className={`animate-spin w-${size} h-${size} text-forge-accent`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

// ── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx(
      "rounded-lg border border-forge-line bg-forge-steel shadow-panel",
      className
    )}>
      {children}
    </div>
  );
}

// ── SectionLabel ─────────────────────────────────────────────────────────────
export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-wide text-forge-muted/80 mb-2">{children}</p>
  );
}

// ── EmptyState ────────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <div className="text-forge-muted opacity-40">{icon}</div>
      <p className="text-sm font-medium text-white/70">{title}</p>
      <p className="text-xs text-forge-muted max-w-xs">{body}</p>
    </div>
  );
}
