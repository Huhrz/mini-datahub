import React from "react";

/**
 * Small label pill — mirrors the source app's `TONES` map exactly
 * (slate→neutral, indigo→accent, emerald→success, amber→warning, rose→danger).
 * Used for embodiment/format/license/quality/failure tags on dataset cards
 * and in the detail drawer (task/scene/modality/action-convention tags).
 */
export function Tag({ children, tone = "neutral" }) {
  const tones = {
    neutral: { background: "var(--tone-neutral-bg)", color: "var(--tone-neutral-fg)" },
    accent: { background: "var(--tone-accent-bg)", color: "var(--tone-accent-fg)" },
    success: { background: "var(--tone-success-bg)", color: "var(--tone-success-fg)" },
    warning: { background: "var(--tone-warning-bg)", color: "var(--tone-warning-fg)" },
    danger: { background: "var(--tone-danger-bg)", color: "var(--tone-danger-fg)" },
  };
  return (
    <span
      style={{
        display: "inline-block",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--text-xs)",
        fontWeight: "var(--weight-medium)",
        padding: "3px 8px",
        borderRadius: "var(--radius-sm)",
        marginRight: 4,
        marginBottom: 4,
        ...tones[tone],
      }}
    >
      {children}
    </span>
  );
}
