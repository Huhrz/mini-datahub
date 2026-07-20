import React, { useState } from "react";

/** Embodiment × task-concept coverage heatmap — single-hue accent ramp, gray gaps. */
export function CoverageHeatmap({ embodiments, concepts, cells }) {
  const [hover, setHover] = useState(null);
  const lookup = {};
  let max = 0;
  cells.forEach((c) => {
    lookup[`${c.embodiment}|${c.concept}`] = c.count;
    if (c.count > max) max = c.count;
  });
  const color = (n) => {
    if (!n) return "var(--heatmap-empty)";
    const t = 0.15 + 0.85 * (n / max);
    return `color-mix(in srgb, var(--heatmap-fill) ${Math.round(t * 100)}%, white)`;
  };

  return (
    <div
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-xl)",
        padding: 24,
        boxShadow: "var(--shadow-sm)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <h2 style={{ fontSize: "var(--text-h2)", fontWeight: "var(--weight-bold)", margin: 0, color: "var(--text-primary)" }}>
          覆盖度地图
        </h2>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>颜色越深数据越多 · 浅灰=空白(gap)</span>
      </div>
      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", margin: "0 0 16px" }}>
        本体 × 任务概念。一眼看出哪些组合数据充足、哪些是空白。
      </p>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "separate", borderSpacing: 4 }}>
          <thead>
            <tr>
              <th></th>
              {concepts.map((c) => (
                <th key={c.id} style={{ padding: 4, verticalAlign: "bottom" }}>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)", writingMode: "vertical-rl", height: 80 }}>
                    {c.label}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {embodiments.map((e) => (
              <tr key={e}>
                <td style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-secondary)", paddingRight: 10, whiteSpace: "nowrap" }}>
                  {e}
                </td>
                {concepts.map((c) => {
                  const n = lookup[`${e}|${c.id}`] || 0;
                  return (
                    <td key={c.id}>
                      <div
                        onMouseEnter={() => setHover({ e, c: c.label, n })}
                        onMouseLeave={() => setHover(null)}
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: "var(--radius-md)",
                          background: color(n),
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 11,
                          fontWeight: 600,
                          color: n > max * 0.5 ? "#fff" : "var(--text-secondary)",
                        }}
                      >
                        {n || ""}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hover && (
        <div style={{ marginTop: 16, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
          <b style={{ color: "var(--text-primary)" }}>{hover.e}</b> × <b style={{ color: "var(--text-primary)" }}>{hover.c}</b>：
          {hover.n > 0 ? `${hover.n} 个数据集` : "空白 — 该组合暂无数据"}
        </div>
      )}
    </div>
  );
}
