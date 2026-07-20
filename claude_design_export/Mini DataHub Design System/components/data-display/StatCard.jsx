import React from "react";

/** Top-of-page metric card (dataset count / episode count / frame count). */
export function StatCard({ label, value, icon }) {
  return (
    <div
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "16px 18px",
        boxShadow: "var(--shadow-sm)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
      }}
    >
      <div>
        <div style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-secondary)" }}>
          {label}
        </div>
        <div style={{ fontSize: "var(--text-h1)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
          {value}
        </div>
      </div>
      {icon && (
        <i data-lucide={icon} style={{ width: 18, height: 18, color: "var(--text-tertiary)" }} />
      )}
    </div>
  );
}
