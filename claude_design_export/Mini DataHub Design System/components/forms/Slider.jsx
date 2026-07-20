import React from "react";

/** Range slider with live value label — used for min quality score. */
export function Slider({ label, value, min = 0, max = 1, step = 0.05, onChange, format }) {
  const display = format ? format(value) : value;
  return (
    <div style={{ marginTop: "var(--space-3)" }}>
      <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 4 }}>
        {label}：<span style={{ color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>{display}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: "100%", accentColor: "var(--accent)" }}
      />
    </div>
  );
}
