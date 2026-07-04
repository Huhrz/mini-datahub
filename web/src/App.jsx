import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import CoverageHeatmap from "./CoverageHeatmap.jsx";

// 用完整 class 字符串（Tailwind 无法识别动态拼接的 class）
const TONES = {
  slate: "bg-slate-100 text-slate-700",
  indigo: "bg-indigo-100 text-indigo-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
};
const Tag = ({ children, tone = "slate" }) => (
  <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium mr-1 mb-1 ${TONES[tone] || TONES.slate}`}>
    {children}
  </span>
);

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 px-5 py-4 shadow-sm">
      <div className="text-sm text-slate-500 font-medium">{label}</div>
      <div className="text-2xl font-bold text-slate-800 mt-1">{value}</div>
    </div>
  );
}

function Detail({ id, onClose }) {
  const [d, setD] = useState(null);
  useEffect(() => { setD(null); api.detail(id).then(setD); }, [id]);
  if (!d) return null;
  const ds = d.dataset || {};
  const viz = `https://huggingface.co/spaces/lerobot/visualize_dataset?dataset=${id}`;
  return (
    <div className="fixed inset-0 z-30 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-white h-full overflow-y-auto p-7 shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-5 text-slate-400 hover:text-slate-700 text-xl">×</button>
        <h2 className="text-xl font-bold mb-1">{ds.name}</h2>
        <div className="text-sm text-slate-400 mb-4">{ds.dataset_id}</div>

        <div className="grid grid-cols-3 gap-3 mb-5">
          <StatCard label="本体" value={`${ds.embodiment || "—"}`} />
          <StatCard label="轨迹数" value={ds.n_episodes ?? "—"} />
          <StatCard label="可商用" value={ds.commercial_ok ? "是" : "否"} />
        </div>

        <div className="text-sm text-slate-600 space-y-1 mb-4">
          <div>许可证：<code className="bg-slate-100 px-1 rounded">{ds.license_spdx}</code>　源格式：<code className="bg-slate-100 px-1 rounded">{ds.source_format}</code></div>
          <div>采集方式：{ds.provenance_type || "—"}　来源：{ds.source}</div>
          <div>质量分：{ds.quality_score != null ? ds.quality_score.toFixed(2) : "未评分"}
            {ds.quality_report?.tier === "metadata" && <span className="text-slate-400"> （元数据初筛）</span>}</div>
        </div>

        {!ds.commercial_ok && (
          <div className="bg-amber-50 border border-amber-200 text-amber-700 text-sm rounded-lg px-3 py-2 mb-4">
            ⚠️ 该数据集不可商用，请勿混入商业训练集。
          </div>
        )}

        {ds.action_convention && Object.keys(ds.action_convention).length > 0 && (
          <div className="mb-3 text-sm"><span className="font-semibold">动作约定：</span>
            {Object.entries(ds.action_convention).map(([k, v]) => <Tag key={k}>{k}={String(v)}</Tag>)}
          </div>
        )}
        {["tasks", "scenes", "modalities"].map((f) =>
          (ds[f] || []).length > 0 ? (
            <div key={f} className="mb-2 text-sm">
              <span className="font-semibold">{{ tasks: "任务", scenes: "场景", modalities: "模态" }[f]}：</span>
              {ds[f].map((v) => <Tag key={v} tone="indigo">{v}</Tag>)}
            </div>
          ) : null
        )}

        <div className="flex gap-2 mt-5">
          {(ds.source === "huggingface" || String(ds.source_format).includes("lerobot")) && (
            <a href={viz} target="_blank" rel="noreferrer"
               className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700">🎬 在线可视化</a>
          )}
          {ds.homepage && (
            <a href={ds.homepage} target="_blank" rel="noreferrer"
               className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-semibold hover:border-brand-600 hover:text-brand-600">🔗 数据集主页</a>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [facets, setFacets] = useState({ embodiments: [], formats: [], provenances: [], concepts: [] });
  const [filters, setFilters] = useState({
    search: "", embodiment: "", format: "", provenance: "",
    commercial_only: false, failures_only: false, min_episodes: 0, min_quality: 0, concept: "",
  });
  const [data, setData] = useState({ count: 0, datasets: [] });
  const [tab, setTab] = useState("list");
  const [selected, setSelected] = useState(null);

  useEffect(() => { api.stats().then(setStats); api.facets().then(setFacets); }, []);
  useEffect(() => { api.datasets(filters).then(setData); }, [filters]);

  const set = (k, v) => setFilters((f) => ({ ...f, [k]: v }));

  return (
    <div className="min-h-screen">
      {/* 顶部渐变横幅 */}
      <header className="bg-gradient-to-r from-brand-600 via-violet-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-8 py-8">
          <h1 className="text-2xl font-bold">🤖 机器人 DataHub</h1>
          <p className="text-indigo-100 mt-1">跨源聚合 · 统一检索 · 自动质检 · 覆盖度地图 —— 具身智能数据的联邦门户</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-6">
        {/* 统计卡 */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <StatCard label="数据集数量" value={stats.n_datasets} />
            <StatCard label="轨迹总数" value={stats.n_episodes.toLocaleString()} />
            <StatCard label="总帧数" value={stats.n_frames.toLocaleString()} />
          </div>
        )}

        {/* 标签页 */}
        <div className="flex gap-2 mb-5">
          {[["list", "数据集"], ["coverage", "覆盖度地图"]].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                tab === k ? "bg-brand-600 text-white" : "bg-white border border-slate-200 text-slate-600 hover:border-brand-600"}`}>
              {label}
            </button>
          ))}
        </div>

        {tab === "coverage" ? (
          <CoverageHeatmap />
        ) : (
          <div className="flex gap-6">
            {/* 侧栏筛选 */}
            <aside className="w-64 shrink-0 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm h-fit">
              <h3 className="font-bold mb-3">🔎 筛选</h3>
              <input placeholder="搜索名称 / ID" value={filters.search}
                onChange={(e) => set("search", e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3" />

              <Select label="🧭 任务概念" value={filters.concept} onChange={(v) => set("concept", v)}
                options={[["", "（不限）"], ...facets.concepts.map((c) => [c.id, c.label])]} />
              <Select label="本体类型" value={filters.embodiment} onChange={(v) => set("embodiment", v)}
                options={[["", "（不限）"], ...facets.embodiments.map((e) => [e, e])]} />
              <Select label="源格式" value={filters.format} onChange={(v) => set("format", v)}
                options={[["", "（不限）"], ...facets.formats.map((e) => [e, e])]} />
              <Select label="采集方式" value={filters.provenance} onChange={(v) => set("provenance", v)}
                options={[["", "（不限）"], ...facets.provenances.map((e) => [e, e])]} />

              <label className="flex items-center gap-2 text-sm mt-2">
                <input type="checkbox" checked={filters.commercial_only}
                  onChange={(e) => set("commercial_only", e.target.checked)} /> 仅可商用
              </label>
              <label className="flex items-center gap-2 text-sm mt-1">
                <input type="checkbox" checked={filters.failures_only}
                  onChange={(e) => set("failures_only", e.target.checked)} /> 仅含失败标注
              </label>

              <div className="text-sm mt-3">最低质量分：{filters.min_quality}</div>
              <input type="range" min="0" max="1" step="0.05" value={filters.min_quality}
                onChange={(e) => set("min_quality", parseFloat(e.target.value))} className="w-full" />
            </aside>

            {/* 数据集列表 */}
            <section className="flex-1">
              <div className="text-sm text-slate-500 mb-3">共 {data.count} 个数据集</div>
              <div className="grid gap-3">
                {data.datasets.map((d) => (
                  <div key={d.dataset_id} onClick={() => setSelected(d.dataset_id)}
                    className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md hover:border-brand-500 cursor-pointer transition">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold text-slate-800">{d.name}</div>
                        <div className="text-xs text-slate-400">{d.dataset_id}</div>
                      </div>
                      <div className="text-right">
                        {d.quality_score != null && (
                          <span className="text-sm font-semibold text-brand-600">质量 {d.quality_score.toFixed(2)}</span>
                        )}
                      </div>
                    </div>
                    <div className="mt-2">
                      <Tag tone="indigo">{d.embodiment}</Tag>
                      <Tag>{d.source_format}</Tag>
                      <Tag tone={d.commercial_ok ? "emerald" : "amber"}>{d.commercial_ok ? "可商用" : "非商用"}</Tag>
                      <Tag>{d.n_episodes} 轨迹</Tag>
                      {d.has_failure_labels && <Tag tone="rose">含失败</Tag>}
                    </div>
                  </div>
                ))}
                {data.datasets.length === 0 && (
                  <div className="text-slate-400 text-sm py-10 text-center">没有符合条件的数据集，试试放宽筛选。</div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>

      {selected && <Detail id={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <div className="mb-3">
      <div className="text-sm text-slate-600 mb-1">{label}</div>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}
