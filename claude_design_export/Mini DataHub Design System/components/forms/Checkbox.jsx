import React from "react";

/** Labeled checkbox — used for "仅可商用" / "仅含失败标注" toggle filters. */
export function Checkbox({ label, checked, onChange }) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: "var(--text-sm)",
        color: "var(--text-primary)",
        cursor: "pointer",
        marginTop: 6,
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ accentColor: "var(--accent)", width: 14, height: 14 }}
      />
      {label}
    </label>
  );
}
