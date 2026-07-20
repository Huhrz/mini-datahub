import React from "react";

/** Inline notice banner — used for the non-commercial-use warning in the detail drawer. */
export function Alert({ children, tone = "warning", icon = "alert-triangle" }) {
  const tones = {
    warning: { background: "var(--warning-subtle)", border: "var(--amber-600)", color: "var(--amber-700)" },
    danger: { background: "var(--danger-subtle)", border: "var(--rose-600)", color: "var(--rose-700)" },
    info: { background: "var(--info-subtle)", border: "var(--sky-600)", color: "var(--sky-700)" },
  };
  const t = tones[tone];
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        background: t.background,
        border: `1px solid ${t.border}`,
        borderRadius: "var(--radius-md)",
        padding: "10px 14px",
        fontSize: "var(--text-sm)",
        color: t.color,
      }}
    >
      {icon && <i data-lucide={icon} style={{ width: 16, height: 16, flexShrink: 0 }} />}
      <span>{children}</span>
    </div>
  );
}
