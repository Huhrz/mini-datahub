import React, { useEffect, useState } from "react";
import { api } from "./api.js";

// 覆盖度热力图：本体(行) × 任务概念(列)，颜色深浅=数据量，一眼看 gap
export default function CoverageHeatmap() {
  const [data, setData] = useState(null);
  const [hover, setHover] = useState(null);

  useEffect(() => {
    api.coverage().then(setData).catch(() => setData({ error: true }));
  }, []);

  if (!data) return <div className="p-8 text-slate-400">加载中…</div>;
  if (data.error) return <div className="p-8 text-slate-400">暂无覆盖度数据</div>;

  const { embodiments, concepts, cells } = data;
  const lookup = {};
  let max = 0;
  cells.forEach((c) => {
    lookup[`${c.embodiment}|${c.concept}`] = c.count;
    if (c.count > max) max = c.count;
  });

  const color = (n) => {
    if (!n) return "#f1f5f9"; // 空白 = 浅灰（gap）
    const t = 0.15 + 0.85 * (n / max);
    return `rgba(79,70,229,${t})`;
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-baseline justify-between mb-1">
        <h2 className="text-lg font-bold">覆盖度地图</h2>
        <span className="text-xs text-slate-400">颜色越深数据越多 · 浅灰=空白(gap)</span>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        本体 × 任务概念。一眼看出哪些组合数据充足、哪些是空白——空白正是值得补充数据的方向。
      </p>

      <div className="overflow-x-auto">
        <table className="border-separate" style={{ borderSpacing: "4px" }}>
          <thead>
            <tr>
              <th className="text-left text-xs text-slate-400 font-medium p-2"></th>
              {concepts.map((c) => (
                <th key={c.id} className="p-1 align-bottom">
                  <div className="text-xs text-slate-600 whitespace-nowrap mx-auto"
                       style={{ writingMode: "vertical-rl", textOrientation: "upright", height: 90, letterSpacing: "1px" }}>
                    {c.label.split(" / ")[0]}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {embodiments.map((e) => (
              <tr key={e}>
                <td className="text-right text-sm font-medium text-slate-600 pr-3 whitespace-nowrap">{e}</td>
                {concepts.map((c) => {
                  const n = lookup[`${e}|${c.id}`] || 0;
                  return (
                    <td key={c.id}>
                      <div
                        onMouseEnter={() => setHover({ e, c: c.label, n })}
                        onMouseLeave={() => setHover(null)}
                        className="w-10 h-10 rounded-md flex items-center justify-center text-xs font-semibold cursor-default transition"
                        style={{ background: color(n), color: n > max * 0.5 ? "#fff" : "#475569" }}
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
        <div className="mt-4 text-sm text-slate-600">
          <b>{hover.e}</b> × <b>{hover.c.split(" / ")[0]}</b>：
          {hover.n > 0 ? `${hover.n} 个数据集` : "空白 — 该组合暂无数据"}
        </div>
      )}
    </div>
  );
}
