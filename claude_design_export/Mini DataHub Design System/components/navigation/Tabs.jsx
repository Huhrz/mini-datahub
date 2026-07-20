import React from "react";

/** Top-level view switch — "数据集" / "覆盖度地图" in the source app. */
export function Tabs({ items, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 8 }}>
      {items.map((it) => {
        const isActive = it.key === active;
        return (
          <button
            key={it.key}
            onClick={() => onChange(it.key)}
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "var(--text-sm)",
              fontWeight: "var(--weight-semibold)",
              padding: "8px 16px",
              borderRadius: "var(--radius-md)",
              border: isActive ? "1px solid var(--accent)" : "1px solid var(--border-subtle)",
              background: isActive ? "var(--accent)" : "var(--surface-card)",
              color: isActive ? "var(--text-on-accent)" : "var(--text-secondary)",
              cursor: "pointer",
              transition: "all var(--duration-fast) var(--ease-standard)",
            }}
          >
            {it.label}
          </button>
        );
      })}
    </div>
  );
}
