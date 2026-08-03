import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { Loader2, TrendingUp, AlertTriangle, Layers, Sparkles, ArrowRight } from "lucide-react";

const fmtNum = (n) => (n == null ? "—" : n.toLocaleString());
function fmtBytes(n) {
  if (!n) return null;
  const u = ["B", "KB", "MB", "GB", "TB", "PB"];
  let i = 0, v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v >= 100 ? 0 : 1)} ${u[i]}`;
}

const TONE = {
  "缺口": { cls: "border-rose-200 dark:border-rose-500/30 bg-rose-50 dark:bg-rose-500/10", icon: AlertTriangle, color: "text-rose-600 dark:text-rose-400" },
  "风险": { cls: "border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10", icon: AlertTriangle, color: "text-amber-600 dark:text-amber-400" },
  "集中": { cls: "border-cyan-200 dark:border-cyan-500/30 bg-cyan-50 dark:bg-cyan-500/10", icon: Layers, color: "text-cyan-700 dark:text-cyan-400" },
  "长尾": { cls: "border-violet-200 dark:border-violet-500/30 bg-violet-50 dark:bg-violet-500/10", icon: TrendingUp, color: "text-violet-600 dark:text-violet-400" },
  "现状": { cls: "border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-800/50", icon: Sparkles, color: "text-slate-600 dark:text-zinc-300" },
};

function Bars({ items, total, unit = "个" }) {
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <div className="space-y-1.5">
      {items.map((it) => (
        <div key={it.name} className="flex items-center gap-3 text-sm">
          <span className="w-32 sm:w-44 truncate text-slate-600 dark:text-zinc-300" title={it.name}>{it.name}</span>
          <span className="flex-1 h-2.5 bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden">
            <span className="block h-full bg-cyan-500 rounded-full" style={{ width: `${100 * it.count / max}%` }} />
          </span>
          <span className="w-20 text-right font-mono text-xs text-slate-500 dark:text-zinc-400 whitespace-nowrap">
            {it.count} {unit}{total ? ` · ${Math.round(100 * it.count / total)}%` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function Card({ title, sub, children }) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-6 shadow-sm">
      <h3 className="font-bold text-slate-900 dark:text-zinc-100 mb-0.5">{title}</h3>
      {sub && <p className="text-xs text-slate-500 dark:text-zinc-400 mb-3">{sub}</p>}
      {children}
    </div>
  );
}

export default function ReportView({ onOpenDataset }) {
  const [d, setD] = useState(null);
  useEffect(() => { api.report().then(setD).catch(() => setD({ n: 0 })); }, []);

  if (!d) return (
    <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-16 justify-center">
      <Loader2 size={16} className="animate-spin" /> 生成领域报告…</div>
  );
  if (!d.n) return <div className="text-slate-400 text-sm py-16 text-center">暂无数据。</div>;

  const s = d.scale, g = d.governance;

  return (
    <div className="space-y-4">
      {/* 概览 */}
      <div className="bg-gradient-to-br from-cyan-600 to-cyan-700 rounded-2xl p-6 text-white shadow-sm">
        <h2 className="text-lg font-bold mb-1">机器人数据领域现状报告</h2>
        <p className="text-sm opacity-90 mb-5">
          基于本平台收录的 {s.datasets} 个跨源数据集自动统计生成，随目录更新而刷新。
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[["数据集", fmtNum(s.datasets)], ["轨迹总数", fmtNum(s.episodes)],
            ["总帧数", fmtNum(s.frames)], ["累计时长", s.hours ? `${fmtNum(Math.round(s.hours))} 小时` : "—"]]
            .map(([l, v]) => (
              <div key={l}>
                <div className="text-xs opacity-80">{l}</div>
                <div className="text-xl sm:text-2xl font-bold font-mono">{v}</div>
              </div>
            ))}
        </div>
        {s.bytes > 0 && (
          <div className="mt-3 text-xs opacity-80">源侧数据总量约 {fmtBytes(s.bytes)}（联邦索引，不由本平台存储）</div>
        )}
      </div>

      {/* 关键发现 */}
      <Card title="关键发现" sub="由确定性规则从上述统计推导，非人工撰写">
        <div className="grid gap-3 sm:grid-cols-2">
          {(d.findings || []).map((f, i) => {
            const t = TONE[f.type] || TONE["现状"];
            const Icon = t.icon;
            return (
              <div key={i} className={`rounded-xl border p-4 ${t.cls}`}>
                <div className={`flex items-center gap-1.5 text-xs font-semibold mb-1 ${t.color}`}>
                  <Icon size={13} /> {f.type}
                </div>
                <div className="font-semibold text-slate-900 dark:text-zinc-100 text-sm mb-1">{f.title}</div>
                <div className="text-[13px] text-slate-600 dark:text-zinc-300 leading-relaxed">{f.detail}</div>
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="按数据来源" sub="跨源聚合的构成">
          <Bars items={d.by_source} total={d.n} />
        </Card>
        <Card title="按存储格式" sub="格式碎片化是本领域的主要摩擦点">
          <Bars items={d.by_format} total={d.n} />
        </Card>
        <Card title="按机器人本体" sub="决定数据能否迁移到你的机器人">
          <Bars items={d.by_embodiment} total={d.n} />
        </Card>
        <Card title="按模态覆盖" sub="含该模态的数据集数量">
          <Bars items={d.by_modality} total={d.n} />
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="数据集规模分布" sub="按轨迹数分档，可见明显长尾">
          <Bars items={d.size_buckets} total={d.n} />
        </Card>

        <Card title="治理与可用性" sub="合规、标注完整度的整体状况">
          <div className="space-y-2.5">
            {[["可商用", g.commercial_pct, g.commercial_ok],
              ["含语言指令", g.language_pct, g.with_language],
              ["含失败标注", g.failure_pct, g.with_failure],
              ["含深度信息", g.depth_pct, g.with_depth],
              ["许可证不明", g.license_unknown_pct, g.license_unknown],
              ["采集方式未知", g.provenance_unknown_pct, g.provenance_unknown]].map(([l, pct, cnt]) => (
              <div key={l} className="flex items-center gap-3 text-sm">
                <span className="w-28 text-slate-600 dark:text-zinc-300">{l}</span>
                <span className="flex-1 h-2.5 bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                  <span className={`block h-full rounded-full ${
                    l.includes("不明") || l.includes("未知") ? "bg-amber-500" : "bg-cyan-500"}`}
                    style={{ width: `${pct}%` }} />
                </span>
                <span className="w-24 text-right font-mono text-xs text-slate-500 dark:text-zinc-400">
                  {pct}% · {cnt} 个
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="规模最大的数据集" sub="少数超大数据集主导了整个领域的数据供给">
        <div className="space-y-1.5">
          {(d.biggest || []).map((b) => (
            <button key={b.dataset_id} onClick={() => onOpenDataset && onOpenDataset(b.dataset_id)}
              className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg border
                border-slate-200 dark:border-zinc-800 hover:border-cyan-500 text-left transition">
              <span className="min-w-0">
                <span className="block text-sm font-medium text-slate-800 dark:text-zinc-100 truncate">{b.name}</span>
                <span className="block text-xs text-slate-400 dark:text-zinc-500 font-mono truncate">{b.dataset_id}</span>
              </span>
              <span className="shrink-0 flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400">
                {b.embodiment} · {fmtNum(b.n_episodes)} 轨迹
                <ArrowRight size={14} className="text-cyan-600" />
              </span>
            </button>
          ))}
        </div>
      </Card>

      {d.freshness?.length > 0 && (
        <Card title="数据新鲜度" sub="按源站最后更新年份分布">
          <Bars items={d.freshness.map((f) => ({ name: f.year, count: f.count }))} total={d.n} />
        </Card>
      )}

      <p className="text-xs text-slate-400 dark:text-zinc-500 text-center px-4">{d.note}</p>
    </div>
  );
}
