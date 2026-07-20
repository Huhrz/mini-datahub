import React from "react";

/** Labeled dropdown used for each facet filter (embodiment, format, provenance, concept). */
export function Select({ label, value, onChange, options }) {
  return (
    <div style={{ marginBottom: "var(--space-3)" }}>
      <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 4 }}>
        {label}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          fontFamily: "var(--font-sans)",
          fontSize: "var(--text-sm)",
          padding: "7px 8px",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-md)",
          background: "var(--surface-card)",
          color: "var(--text-primary)",
        }}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
