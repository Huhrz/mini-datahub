import React from "react";
import { Tag } from "./Tag.jsx";

/** One row in the dataset list/grid — opens the detail drawer on click. */
export function DatasetCard({ dataset: d, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "14px 16px",
        boxShadow: "var(--shadow-sm)",
        cursor: onClick ? "pointer" : "default",
        transition: "box-shadow var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "var(--shadow-md)";
        e.currentTarget.style.borderColor = "var(--accent-300)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "var(--shadow-sm)";
        e.currentTarget.style.borderColor = "var(--border-subtle)";
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontWeight: "var(--weight-semibold)", color: "var(--text-primary)", fontSize: "var(--text-body)" }}>
            {d.name}
          </div>
          <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
            {d.dataset_id}
          </div>
        </div>
        {d.quality_score != null && (
          <div style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--accent)", fontFamily: "var(--font-mono)" }}>
            质量 {d.quality_score.toFixed(2)}
          </div>
        )}
      </div>
      <div style={{ marginTop: 8 }}>
        <Tag tone="accent">{d.embodiment}</Tag>
        <Tag tone="neutral">{d.source_format}</Tag>
        <Tag tone={d.commercial_ok ? "success" : "warning"}>{d.commercial_ok ? "可商用" : "非商用"}</Tag>
        <Tag tone="neutral">{d.n_episodes} 轨迹</Tag>
        {d.has_failure_labels && <Tag tone="danger">含失败</Tag>}
      </div>
    </div>
  );
}
