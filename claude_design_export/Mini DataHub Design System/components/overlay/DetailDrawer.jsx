import React from "react";

/** Right-side slide-over — used for the dataset detail panel. Click the
 * scrim or the × to close. */
export function DetailDrawer({ open, onClose, title, subtitle, children }) {
  if (!open) return null;
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 30, display: "flex", justifyContent: "flex-end" }}>
      <div
        onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "var(--surface-overlay-scrim)" }}
      />
      <div
        style={{
          position: "relative",
          width: "min(480px, 100%)",
          background: "var(--surface-card)",
          height: "100%",
          overflowY: "auto",
          padding: 28,
          boxShadow: "var(--shadow-2xl)",
          fontFamily: "var(--font-sans)",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 16,
            right: 20,
            border: "none",
            background: "none",
            color: "var(--text-tertiary)",
            fontSize: 20,
            cursor: "pointer",
            lineHeight: 1,
          }}
        >
          ×
        </button>
        <h2 style={{ fontSize: "var(--text-h2)", fontWeight: "var(--weight-bold)", margin: "0 0 2px", color: "var(--text-primary)" }}>
          {title}
        </h2>
        {subtitle && (
          <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginBottom: 16, fontFamily: "var(--font-mono)" }}>
            {subtitle}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
