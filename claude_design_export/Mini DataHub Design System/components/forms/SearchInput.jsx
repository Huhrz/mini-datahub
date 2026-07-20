import React from "react";

/** Search field with a leading icon, used at the top of the filter sidebar. */
export function SearchInput({ value, onChange, placeholder = "搜索名称 / ID" }) {
  return (
    <div style={{ position: "relative" }}>
      <i
        data-lucide="search"
        style={{
          position: "absolute",
          left: 10,
          top: "50%",
          transform: "translateY(-50%)",
          width: 14,
          height: 14,
          color: "var(--text-tertiary)",
        }}
      />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: "100%",
          fontFamily: "var(--font-sans)",
          fontSize: "var(--text-sm)",
          padding: "8px 10px 8px 30px",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-md)",
          color: "var(--text-primary)",
          background: "var(--surface-card)",
          outline: "none",
        }}
      />
    </div>
  );
}
