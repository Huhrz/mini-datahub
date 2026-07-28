import React, { useEffect, useState } from "react";
import { api, setToken, getToken } from "./api.js";
import CoverageHeatmap from "./CoverageHeatmap.jsx";
import EpisodePlayer, { Thumbnail, SampleStrip, OfficialViz, ThumbStrip } from "./EpisodePlayer.jsx";
import {
  Search, SlidersHorizontal, ExternalLink, AlertTriangle,
  Sun, Moon, Check, Film, LayoutGrid, List, ChevronLeft, ChevronRight,
  ShoppingCart, Download, X, Loader2, WifiOff, Braces, User, LogOut, FolderHeart, Save, Trash2,
} from "lucide-react";

const PAGE_SIZE = 20;

const TONES = {
  slate: "bg-slate-100 text-slate-700 dark:bg-zinc-800 dark:text-zinc-200",
  cyan: "bg-cyan-100 text-cyan-700 dark:bg-cyan-400/15 dark:text-cyan-300",
  emerald: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  amber: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  rose: "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
};
const Tag = ({ children, tone = "slate" }) => (
  <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-medium mr-1 mb-1 ${TONES[tone] || TONES.slate}`}>
    {children}
  </span>
);

function StatCard({ label, value }) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-slate-200 dark:border-zinc-800 px-5 py-4 shadow-sm">
      <div className="text-sm text-slate-500 dark:text-zinc-400 font-medium">{label}</div>
      <div className="text-2xl font-bold text-slate-900 dark:text-zinc-50 mt-1 font-mono">{value}</div>
    </div>
  );
}

function fmtBytes(n) {
  if (!n || n <= 0) return null;
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${u[i]}`;
}
function fmtDuration(s) {
  if (!s || s <= 0) return null;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  if (h >= 1) return `${h} 小时${m ? " " + m + " 分" : ""}`;
  if (m >= 1) return `${m} 分${Math.floor(s % 60)} 秒`;
  return `${Math.round(s)} 秒`;
}

function SpecsGrid({ ds }) {
  const specs = [
    ["数据大小", fmtBytes(ds.size_bytes)],
    ["总时长", fmtDuration(ds.duration_s)],
    ["平均每集", ds.avg_episode_frames > 0 ? `${Math.round(ds.avg_episode_frames)} 帧` : null],
    ["总帧数", ds.total_frames > 0 ? ds.total_frames.toLocaleString() : null],
    ["帧率", ds.fps > 0 ? `${ds.fps} fps` : null],
    ["分辨率", ds.video_resolution || null],
    ["视频编码", ds.video_codec || null],
    ["相机数", ds.n_cameras > 0 ? ds.n_cameras : null],
    ["下载量", ds.downloads > 0 ? ds.downloads.toLocaleString() : null],
    ["点赞", ds.likes > 0 ? ds.likes : null],
    ["更新时间", ds.last_modified || null],
  ].filter(([, v]) => v != null && v !== "");
  if (!specs.length) return null;
  return (
    <div className="mb-4">
      <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 mb-2">规格</div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {specs.map(([k, v]) => (
          <div key={k} className="bg-slate-50 dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg px-3 py-2">
            <div className="text-xs text-slate-400 dark:text-zinc-500">{k}</div>
            <div className="text-sm font-mono text-slate-800 dark:text-zinc-100 truncate" title={String(v)}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// OXE 数据集：找它的 HF LeRobot 转换版（社区 IPEC-COMMUNITY），用官方可视化打开。
function OxeConversion({ id }) {
  const [r, setR] = useState(null);
  useEffect(() => { setR(null); api.oxeHf(id).then(setR).catch(() => setR({ repo: null })); }, [id]);
  if (r == null) return (
    <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-6 justify-center">
      <Loader2 size={15} className="animate-spin" /> 查找 HF LeRobot 转换版…</div>
  );
  if (!r.repo) return (
    <div className="rounded-lg border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 p-5 text-sm text-slate-500 dark:text-zinc-400">
      这是 OXE(RLDS)数据集,原始格式不便直接可视化;暂未找到它的 HF LeRobot 转换版。
      {r.guess && <span className="block text-xs mt-1 font-mono text-slate-400 dark:text-zinc-600">尝试的仓库: {r.guess}(不存在)</span>}
    </div>
  );
  return (
    <div>
      <div className="text-xs text-slate-500 dark:text-zinc-400 mb-2">
        OXE 数据集 · 可视化来自社区 HF LeRobot 转换版 <code className="bg-slate-100 dark:bg-zinc-800 px-1 rounded">{r.repo}</code>
      </div>
      <OfficialViz repoId={r.repo} />
    </div>
  );
}

function Detail({ id, onClose, onOpen }) {
  const [d, setD] = useState(null);
  const [playEp, setPlayEp] = useState(null);
  const [vizMode, setVizMode] = useState("official");
  useEffect(() => { setD(null); setPlayEp(null); setVizMode("official"); api.detail(id).then(setD); }, [id]);
  if (!d) return null;
  const ds = d.dataset || {};
  const isOxe = ds.source === "openx";
  const isHF = !isOxe && (ds.source === "huggingface"
    || String(ds.source_format || "").includes("lerobot")
    || String(ds.homepage || ds.source_uri || "").includes("huggingface.co"));
  return (
    <div className="fixed inset-0 z-30 flex justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-white dark:bg-zinc-900 h-full overflow-y-auto p-6 sm:p-7 shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-5 text-slate-400 dark:text-zinc-500 hover:text-slate-800 dark:hover:text-zinc-100 text-2xl leading-none">×</button>
        <h2 className="text-xl font-bold mb-1 text-slate-900 dark:text-zinc-50 pr-8">{ds.name}</h2>
        <div className="text-sm text-slate-500 dark:text-zinc-500 mb-4 font-mono break-all">{ds.dataset_id}</div>
        <div className="grid grid-cols-3 gap-3 mb-5">
          <StatCard label="本体" value={`${ds.embodiment || "—"}`} />
          <StatCard label="轨迹数" value={ds.n_episodes ?? "—"} />
          <StatCard label="可商用" value={ds.commercial_ok ? "是" : "否"} />
        </div>
        <div className="text-sm text-slate-700 dark:text-zinc-300 space-y-1 mb-4">
          <div>许可证：<code className="bg-slate-100 dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 px-1 rounded font-mono">{ds.license_spdx}</code>　源格式：<code className="bg-slate-100 dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 px-1 rounded font-mono">{ds.source_format}</code></div>
          <div>采集方式：{ds.provenance_type || "—"}　来源：{ds.source}</div>
          <div>质量分：<span className="font-mono">{ds.quality_score != null && ds.quality_score >= 0 ? ds.quality_score.toFixed(2) : "未评分"}</span>
            {ds.quality_report?.tier === "metadata" && <span className="text-slate-400 dark:text-zinc-500"> （元数据初筛）</span>}</div>
        </div>

        <SpecsGrid ds={ds} />
        {!ds.commercial_ok && (
          <div className="flex items-center gap-2 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-300 text-sm rounded-lg px-3 py-2 mb-4">
            <AlertTriangle size={16} className="shrink-0" /> 该数据集不可商用，请勿混入商业训练集。
          </div>
        )}
        {ds.action_convention && Object.keys(ds.action_convention).length > 0 && (
          <div className="mb-3 text-sm text-slate-700 dark:text-zinc-300"><span className="font-semibold text-slate-900 dark:text-zinc-100">动作约定：</span>
            {Object.entries(ds.action_convention).map(([k, v]) => <Tag key={k}>{k}={String(v)}</Tag>)}
          </div>
        )}
        {["tasks", "scenes", "modalities"].map((f) =>
          (ds[f] || []).length > 0 ? (
            <div key={f} className="mb-2 text-sm text-slate-700 dark:text-zinc-300">
              <span className="font-semibold text-slate-900 dark:text-zinc-100">{{ tasks: "任务", scenes: "场景", modalities: "模态" }[f]}：</span>
              {ds[f].map((v) => <Tag key={v} tone="cyan">{v}</Tag>)}
            </div>
          ) : null
        )}
        <div className="mt-5">
          <ThumbStrip datasetId={ds.dataset_id} />

          <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
            <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 flex items-center gap-1.5">
              <Film size={15} /> 可视化
              <span className="text-[11px] font-normal text-slate-400 dark:text-zinc-500 font-mono">
                （{isOxe ? "HF转换版" : isHF ? "官方可视化" : "自研"} · {ds.source}/{ds.source_format}）
              </span>
            </div>
            {isHF && (
              <div className="flex items-center rounded-lg border border-slate-200 dark:border-zinc-800 overflow-hidden text-xs">
                {[["official", "官方可视化"], ["self", "自研播放器"]].map(([k, label]) => (
                  <button key={k} onClick={() => setVizMode(k)}
                    className={`px-2.5 py-1 font-medium ${vizMode === k ? "bg-cyan-600 text-white" : "bg-white dark:bg-zinc-900 text-slate-500 dark:text-zinc-400 hover:text-cyan-600"}`}>
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {isOxe ? (
            <OxeConversion id={ds.dataset_id} />
          ) : isHF && vizMode === "official" ? (
            <OfficialViz repoId={ds.dataset_id} totalEpisodes={ds.n_episodes} />
          ) : (
            <>
              <SampleStrip datasetId={ds.dataset_id} onPick={setPlayEp} activeEp={playEp} />
              {playEp != null ? (
                <div className="mt-4">
                  <EpisodePlayer datasetId={ds.dataset_id} initialEp={playEp} />
                </div>
              ) : (
                <div className="text-xs text-slate-400 dark:text-zinc-500 mt-2">点上面任意样本，加载完整回放与状态/动作曲线。</div>
              )}
            </>
          )}
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            {ds.homepage && (
              <a href={ds.homepage} target="_blank" rel="noreferrer"
                 className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 text-slate-700 dark:text-zinc-200 text-sm font-semibold hover:border-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400">
                <ExternalLink size={14} /> 数据集主页
              </a>
            )}
            <a href={api.croissantUrl(ds.dataset_id)} target="_blank" rel="noreferrer"
               title="Croissant 1.1 元数据（用于 Google Dataset Search 等对外发现）"
               className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 text-slate-700 dark:text-zinc-200 text-sm font-semibold hover:border-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400">
              <Braces size={14} /> Croissant 元数据
            </a>
          </div>
        </div>

        <BenchmarkLinks id={id} />
        <SimilarDatasets id={id} onOpen={onOpen} />
      </div>
    </div>
  );
}

function BenchmarkLinks({ id }) {
  const [items, setItems] = useState(null);
  useEffect(() => {
    let cancel = false;
    setItems(null);
    api.benchmarks(id).then((r) => { if (!cancel) setItems(r.benchmarks || []); }).catch(() => { if (!cancel) setItems([]); });
    return () => { cancel = true; };
  }, [id]);
  if (!items || !items.length) return null;
  return (
    <div className="mt-7">
      <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 mb-1">适用评测基准</div>
      <div className="text-xs text-slate-400 dark:text-zinc-500 mb-2">按本体/任务匹配，跳转其项目/榜单页（协议不完全可比，仅作适用性链接）。</div>
      <div className="flex flex-wrap gap-2">
        {items.map((b) => (
          <a key={b.name} href={b.url} target="_blank" rel="noreferrer" title={`${b.desc}（${b.why}）`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-zinc-800 hover:border-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400 text-sm text-slate-700 dark:text-zinc-200">
            <ExternalLink size={13} /> {b.name}
            {b.sim && <span className="text-[10px] px-1 rounded bg-slate-100 dark:bg-zinc-800 text-slate-400 dark:text-zinc-500">sim</span>}
          </a>
        ))}
      </div>
    </div>
  );
}

function SimilarDatasets({ id, onOpen }) {
  const [items, setItems] = useState(null);
  useEffect(() => {
    let cancel = false;
    setItems(null);
    api.similar(id).then((r) => { if (!cancel) setItems(r.similar || []); }).catch(() => { if (!cancel) setItems([]); });
    return () => { cancel = true; };
  }, [id]);
  if (!items || !items.length) return null;
  return (
    <div className="mt-7">
      <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 mb-2">相似数据集（按语义向量）</div>
      <div className="space-y-1.5">
        {items.map((s) => (
          <button key={s.dataset_id} onClick={() => onOpen && onOpen(s.dataset_id)}
            className="w-full text-left flex items-center justify-between gap-3 px-3 py-2 rounded-lg border border-slate-200 dark:border-zinc-800 hover:border-cyan-500 hover:shadow-sm transition">
            <div className="min-w-0">
              <div className="truncate font-medium text-slate-800 dark:text-zinc-100">{s.name}</div>
              <div className="text-xs text-slate-400 dark:text-zinc-500 font-mono truncate">{s.dataset_id}</div>
            </div>
            <div className="shrink-0 flex items-center gap-2">
              <Tag tone="cyan">{s.embodiment}</Tag>
              {s.quality_score != null && s.quality_score >= 0 && (
                <span className="text-xs text-slate-400 dark:text-zinc-500 font-mono">质量 {s.quality_score.toFixed(2)}</span>
              )}
              <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400">相似 {s.score.toFixed(2)}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function CompareView({ allDs }) {
  const [a, setA] = useState(""); const [b, setB] = useState("");
  const opts = [["", "（选择数据集）"], ...allDs.map((d) => [d.dataset_id, d.name])];
  const dA = allDs.find((d) => d.dataset_id === a);
  const dB = allDs.find((d) => d.dataset_id === b);
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900 dark:text-zinc-100 mb-1">对比回放</h2>
      <p className="text-sm text-slate-500 dark:text-zinc-400 mb-4">并排回放两个数据集（可跨来源）——HuggingFace / Festivus / Humaid 都没占的"跨源统一回放"。</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[[a, setA, dA], [b, setB, dB]].map(([val, setV, d], i) => (
          <div key={i}>
            <select value={val} onChange={(e) => setV(e.target.value)}
              className="w-full mb-2 border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded-lg px-2 py-2 text-sm bg-white">
              {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            {d ? <EpisodePlayer datasetId={d.dataset_id} compact /> :
              <div className="rounded-lg border border-dashed border-slate-300 dark:border-zinc-700 h-[420px] flex items-center justify-center text-slate-400 dark:text-zinc-600 text-sm">选择一个数据集</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function ConceptChips({ concepts, selected, onToggle }) {
  return (
    <div>
      <div className="text-sm text-slate-600 dark:text-zinc-400 mb-1.5">任务概念（可多选）</div>
      <div className="flex flex-wrap gap-1.5">
        {concepts.map((c) => {
          const on = selected.includes(c.id);
          return (
            <button key={c.id} onClick={() => onToggle(c.id)}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border transition ${
                on ? "bg-cyan-600 border-cyan-600 text-white"
                   : "bg-white dark:bg-zinc-950 border-slate-300 dark:border-zinc-700 text-slate-600 dark:text-zinc-300 hover:border-cyan-500"}`}>
              {on && <Check size={11} />}{c.label.split(" / ")[0]}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function GapReport() {
  const [d, setD] = useState(null);
  useEffect(() => { api.gaps().then(setD).catch(() => {}); }, []);
  if (!d) return null;
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900 dark:text-zinc-100 mb-1">数据缺口报告</h2>
      <p className="text-sm text-slate-500 dark:text-zinc-400 mb-4">
        基于覆盖度矩阵，指出全球都缺的 本体×任务 组合 —— 指导"该采什么数据"（数据 hub 的独有价值）。
      </p>
      <div className="grid grid-cols-3 gap-3 mb-5">
        <StatCard label="覆盖率" value={`${d.coverage_pct}%`} />
        <StatCard label="已覆盖组合" value={`${d.covered}/${d.total_cells}`} />
        <StatCard label="空缺组合" value={d.gap_count} />
      </div>

      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 mb-2">最稀缺的任务概念（全球数据集数）</div>
        <div className="flex flex-wrap gap-1.5">
          {(d.scarcest_concepts || []).map((c) => (
            <span key={c.concept}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${
                c.total === 0 ? "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
                              : "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"}`}>
              {c.label.split(" / ")[0]} <span className="font-mono opacity-70">{c.total}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 mb-2">各本体覆盖了多少任务概念</div>
        <div className="flex flex-wrap gap-2">
          {(d.embodiment_coverage || []).map((e) => (
            <span key={e.embodiment} className="text-xs px-2 py-1 rounded-md bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-300 font-mono">
              {e.embodiment}: {e.covered}/{e.of}
            </span>
          ))}
        </div>
      </div>

      <details className="text-sm">
        <summary className="cursor-pointer text-slate-600 dark:text-zinc-400 hover:text-cyan-600">
          查看全部 {d.gap_count} 个空缺组合（本体 × 任务）
        </summary>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {(d.gaps || []).map((g, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-300 font-mono">
              {g.embodiment} × {g.concept_label.split(" / ")[0]}
            </span>
          ))}
        </div>
      </details>
    </div>
  );
}

function DatasetCard({ d, onOpen, inCart, onToggleCart, query, gallery }) {
  const dead = d.link_alive === false;
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-slate-200 dark:border-zinc-800 p-4 shadow-sm hover:shadow-md hover:border-cyan-500 transition">
      {gallery && (
        <div className="mb-3 cursor-pointer" onClick={() => onOpen(d.dataset_id)}>
          <Thumbnail datasetId={d.dataset_id} embodiment={d.embodiment} />
        </div>
      )}
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0 cursor-pointer" onClick={() => onOpen(d.dataset_id)}>
          <div className="font-semibold text-slate-900 dark:text-zinc-100 truncate flex items-center gap-1.5">
            {d.name}
            {dead && <span title="链接失效" className="text-rose-500"><WifiOff size={13} /></span>}
          </div>
          <div className="text-xs text-slate-400 dark:text-zinc-500 font-mono truncate">{d.dataset_id}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {d.quality_score != null && d.quality_score >= 0 && (
            <span className="text-sm font-semibold text-cyan-600 dark:text-cyan-400 font-mono"
              title={d.quality_report?.tier === "metadata" ? "元数据初筛分（非数据级深度质检）" : "深度质检分"}>
              {d.quality_report?.tier === "metadata" ? "初筛" : "质量"} {d.quality_score.toFixed(2)}
            </span>
          )}
          <button onClick={() => onToggleCart(d.dataset_id)} title={inCart ? "从训练集移除" : "加入训练集"}
            className={`p-1.5 rounded-lg border text-xs ${inCart
              ? "bg-cyan-600 border-cyan-600 text-white"
              : "border-slate-300 dark:border-zinc-700 text-slate-500 dark:text-zinc-400 hover:border-cyan-500"}`}>
            {inCart ? <Check size={14} /> : <ShoppingCart size={14} />}
          </button>
        </div>
      </div>
      {query && (() => {
        const hit = (d.tasks || []).find((t) => String(t).toLowerCase().includes(query.toLowerCase()));
        return hit ? <div className="mt-2 text-xs text-slate-500 dark:text-zinc-400 italic truncate">命中任务：{hit}</div> : null;
      })()}
      <div className="mt-2 cursor-pointer" onClick={() => onOpen(d.dataset_id)}>
        <Tag tone="cyan">{d.embodiment}</Tag>
        <Tag>{d.source_format}</Tag>
        <Tag tone={d.commercial_ok ? "emerald" : "amber"}>{d.commercial_ok ? "可商用" : "非商用"}</Tag>
        <Tag>{d.n_episodes} 轨迹</Tag>
        {d.has_failure_labels && <Tag tone="rose">含失败</Tag>}
        {dead && <Tag tone="rose">链接失效</Tag>}
      </div>
    </div>
  );
}

function AuthModal({ onClose, onAuthed }) {
  const [mode, setMode] = useState("login");
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      const r = mode === "login" ? await api.login(u, p) : await api.register(u, p);
      setToken(r.token);
      onAuthed(r.username);
      onClose();
    } catch (e) { setErr(String(e.message || e)); } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-6 shadow-2xl">
        <button onClick={onClose} className="absolute top-3 right-4 text-slate-400 hover:text-slate-700 dark:hover:text-zinc-200 text-xl">×</button>
        <div className="flex gap-2 mb-4">
          {[["login", "登录"], ["register", "注册"]].map(([k, label]) => (
            <button key={k} onClick={() => { setMode(k); setErr(""); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${mode === k ? "bg-cyan-600 text-white" : "bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400"}`}>
              {label}
            </button>
          ))}
        </div>
        <input placeholder="用户名" value={u} onChange={(e) => setU(e.target.value)}
          className="w-full mb-2 border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded-lg px-3 py-2 text-sm" />
        <input type="password" placeholder="密码（至少 6 位）" value={p} onChange={(e) => setP(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
          className="w-full mb-3 border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded-lg px-3 py-2 text-sm" />
        {err && <div className="text-rose-500 text-xs mb-2">{err}</div>}
        <button onClick={submit} disabled={busy}
          className="w-full bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50">
          {busy ? "…" : mode === "login" ? "登录" : "注册并登录"}
        </button>
        <div className="text-[11px] text-slate-400 dark:text-zinc-500 mt-3">
          demo 账户：登录后可把训练集保存为收藏集，随时取回。
        </div>
      </div>
    </div>
  );
}

function CollectionsPanel({ onClose, onLoad }) {
  const [cols, setCols] = useState(null);
  const load = () => api.listCollections().then((r) => setCols(r.collections || [])).catch(() => setCols([]));
  useEffect(() => { load(); }, []);
  const del = async (cid) => { await api.deleteCollection(cid); load(); };
  const open = async (cid) => { const r = await api.getCollection(cid); onLoad(r.ids || []); onClose(); };
  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md bg-white dark:bg-zinc-900 h-full overflow-y-auto p-6 shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-5 text-slate-400 hover:text-slate-700 dark:hover:text-zinc-200 text-2xl">×</button>
        <h2 className="text-lg font-bold text-slate-900 dark:text-zinc-100 mb-1 flex items-center gap-1.5"><FolderHeart size={18} /> 我的收藏集</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400 mb-4">保存的数据集合，点开可载回训练集。</p>
        {cols == null ? <div className="text-slate-400 text-sm py-8 text-center">加载中…</div>
          : cols.length === 0 ? <div className="text-slate-400 dark:text-zinc-500 text-sm py-8 text-center">还没有收藏集。把训练集里的数据集"保存为收藏集"吧。</div>
            : (
              <div className="space-y-2">
                {cols.map((c) => (
                  <div key={c.id} className="flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg border border-slate-200 dark:border-zinc-800">
                    <button onClick={() => open(c.id)} className="min-w-0 text-left flex-1">
                      <div className="font-medium text-slate-800 dark:text-zinc-100 truncate">{c.name}</div>
                      <div className="text-xs text-slate-400 dark:text-zinc-500">{c.count} 个数据集 · {c.created_at}</div>
                    </button>
                    <button onClick={() => del(c.id)} title="删除" className="p-1.5 text-slate-400 hover:text-rose-500"><Trash2 size={15} /></button>
                  </div>
                ))}
              </div>
            )}
      </div>
    </div>
  );
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [facets, setFacets] = useState({ embodiments: [], formats: [], provenances: [], concepts: [] });
  const [filters, setFilters] = useState({
    search: "", embodiment: "", format: "", provenance: "",
    commercial_only: false, failures_only: false, min_episodes: 0, min_quality: 0, concepts: [],
  });
  const [data, setData] = useState({ count: 0, pages: 1, datasets: [] });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [allDs, setAllDs] = useState([]);
  const [tab, setTab] = useState("list");
  const [selected, setSelected] = useState(null);
  const [cart, setCart] = useState(() => new Set());
  const [view, setView] = useState(() => localStorage.getItem("mdh-view") || "gallery");
  const [dark, setDark] = useState(() => localStorage.getItem("mdh-theme") === "dark");
  const [user, setUser] = useState(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [colsOpen, setColsOpen] = useState(false);

  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
    api.facets().then(setFacets).catch(() => {});
    api.datasets({ page: 1, page_size: 500 }).then((r) => setAllDs(r.datasets || [])).catch(() => {});
    if (getToken()) api.me().then((r) => setUser(r.username)).catch(() => setToken(""));
  }, []);

  const logout = async () => { try { await api.logout(); } catch {} setToken(""); setUser(null); };
  const saveCart = async () => {
    if (!user) { setAuthOpen(true); return; }
    const name = window.prompt("给这个收藏集起个名字：", "我的训练集");
    if (name == null) return;
    try { await api.createCollection(name, [...cart]); window.alert("已保存到收藏集。"); }
    catch (e) { window.alert("保存失败：" + e.message); }
  };

  useEffect(() => {
    let cancel = false;
    setLoading(true); setError(null);
    const q = filters.search.trim();
    const clientFilter = (rows) => rows.filter((d) =>
      (!filters.embodiment || d.embodiment === filters.embodiment) &&
      (!filters.format || d.source_format === filters.format) &&
      (!filters.provenance || d.provenance_type === filters.provenance) &&
      (!filters.commercial_only || d.commercial_ok) &&
      (!filters.failures_only || d.has_failure_labels) &&
      ((d.quality_score ?? 1) >= filters.min_quality));
    const done = (payload) => { if (!cancel) { setData(payload); setError(null); setLoading(false); } };
    const fail = () => { if (!cancel) { setError("请求失败，请稍后重试"); setLoading(false); } };

    const fetchOnce = () => q
      ? api.search(q).then((r) => {
          const all = clientFilter(r.datasets || []);
          const pages = Math.max(1, Math.ceil(all.length / PAGE_SIZE));
          return { count: all.length, pages, datasets: all.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE), mode: r.mode };
        })
      : api.datasets({
          embodiment: filters.embodiment, format: filters.format, provenance: filters.provenance,
          commercial_only: filters.commercial_only, failures_only: filters.failures_only,
          min_episodes: filters.min_episodes, min_quality: filters.min_quality,
          concept: filters.concepts.join(","), page, page_size: PAGE_SIZE,
        });

    // 失败自动重试一次（后端偶发繁忙时不至于把列表清空）
    fetchOnce()
      .then(done)
      .catch(() => new Promise((r) => setTimeout(r, 900)).then(fetchOnce).then(done).catch(fail));

    return () => { cancel = true; };
  }, [filters, page]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("mdh-theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => { localStorage.setItem("mdh-view", view); }, [view]);

  const set = (k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1); };
  const toggleConcept = (id) => { setFilters((f) => ({ ...f, concepts: f.concepts.includes(id) ? f.concepts.filter((x) => x !== id) : [...f.concepts, id] })); setPage(1); };
  const toggleCart = (id) => setCart((c) => { const n = new Set(c); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const exportCart = async () => {
    const m = await api.exportManifest([...cart]);
    const warns = m.license_gating?.warnings || [];
    if (warns.length && !window.confirm("License 提示：\n\n" + warns.join("\n") + "\n\n仍要导出训练清单吗？")) return;
    const blob = new Blob([JSON.stringify(m, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "training_manifest.json"; a.click();
    URL.revokeObjectURL(url);
  };

  const tabs = [["list", "数据集", LayoutGrid], ["coverage", "覆盖度地图", SlidersHorizontal], ["compare", "对比回放", Film]];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950">
      <header className="bg-white dark:bg-zinc-900 border-b border-slate-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 py-5 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-zinc-50">🤖 机器人 <span className="text-cyan-600 dark:text-cyan-400">DataHub</span></h1>
            <p className="text-slate-500 dark:text-zinc-400 mt-1 text-xs sm:text-sm">跨源聚合 · 语义检索 · 自动质检 · 覆盖度地图 · 跨源回放</p>
          </div>
          <div className="shrink-0 flex items-center gap-2">
            {user ? (
              <>
                <button onClick={() => setColsOpen(true)}
                  className="flex items-center gap-1.5 border border-slate-300 dark:border-zinc-700 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-zinc-300 hover:border-cyan-500">
                  <FolderHeart size={14} /> 收藏集
                </button>
                <span className="flex items-center gap-1 text-xs font-medium text-slate-600 dark:text-zinc-300"><User size={14} /> {user}</span>
                <button onClick={logout} title="登出" className="text-slate-400 hover:text-rose-500 p-1"><LogOut size={14} /></button>
              </>
            ) : (
              <button onClick={() => setAuthOpen(true)}
                className="flex items-center gap-1.5 border border-slate-300 dark:border-zinc-700 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-zinc-300 hover:border-cyan-500">
                <User size={14} /> 登录 / 注册
              </button>
            )}
            <button onClick={() => setDark((v) => !v)}
              className="flex items-center gap-1.5 border border-slate-300 dark:border-zinc-700 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-zinc-300 hover:border-cyan-500">
              {dark ? <Sun size={14} /> : <Moon size={14} />}{dark ? "浅色" : "深色"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-6">
        {stats && (
          <div className="grid grid-cols-3 gap-3 sm:gap-4 mb-6">
            <StatCard label="数据集数量" value={stats.n_datasets} />
            <StatCard label="轨迹总数" value={stats.n_episodes.toLocaleString()} />
            <StatCard label="总帧数" value={stats.n_frames.toLocaleString()} />
          </div>
        )}

        <div className="flex flex-wrap gap-2 mb-5">
          {tabs.map(([k, label, Icon]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition ${
                tab === k ? "bg-cyan-600 text-white"
                          : "bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-slate-600 dark:text-zinc-300 hover:border-cyan-500"}`}>
              <Icon size={15} />{label}
            </button>
          ))}
        </div>

        {tab === "coverage" ? <div className="space-y-4"><CoverageHeatmap /><GapReport /></div>
        : tab === "compare" ? <CompareView allDs={allDs} />
        : (
          <div className="flex flex-col md:flex-row gap-6">
            <aside className="w-full md:w-64 shrink-0 bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-5 shadow-sm h-fit">
              <h3 className="flex items-center gap-1.5 font-bold mb-3 text-slate-900 dark:text-zinc-100"><SlidersHorizontal size={15} /> 筛选</h3>
              <div className="relative mb-1">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-zinc-500" />
                <input placeholder="搜索名称 / ID / 任务内容…" value={filters.search}
                  onChange={(e) => set("search", e.target.value)}
                  className="w-full border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded-lg pl-8 pr-3 py-2 text-sm" />
              </div>
              <div className="text-xs text-slate-400 dark:text-zinc-500 mb-3">支持中文/英文语义搜索（搜"杯子"命中 cup）</div>
              <div className="mb-3"><ConceptChips concepts={facets.concepts} selected={filters.concepts} onToggle={toggleConcept} /></div>
              <Select label="本体类型" value={filters.embodiment} onChange={(v) => set("embodiment", v)} options={[["", "（不限）"], ...facets.embodiments.map((e) => [e, e])]} />
              <Select label="源格式" value={filters.format} onChange={(v) => set("format", v)} options={[["", "（不限）"], ...facets.formats.map((e) => [e, e])]} />
              <Select label="采集方式" value={filters.provenance} onChange={(v) => set("provenance", v)} options={[["", "（不限）"], ...facets.provenances.map((e) => [e, e])]} />
              <label className="flex items-center gap-2 text-sm mt-2 text-slate-700 dark:text-zinc-300"><input type="checkbox" checked={filters.commercial_only} onChange={(e) => set("commercial_only", e.target.checked)} /> 仅可商用</label>
              <label className="flex items-center gap-2 text-sm mt-1 text-slate-700 dark:text-zinc-300"><input type="checkbox" checked={filters.failures_only} onChange={(e) => set("failures_only", e.target.checked)} /> 仅含失败标注</label>
              <div className="text-sm mt-3 text-slate-700 dark:text-zinc-300">最低质量分：<span className="font-mono">{filters.min_quality}</span></div>
              <input type="range" min="0" max="1" step="0.05" value={filters.min_quality} onChange={(e) => set("min_quality", parseFloat(e.target.value))} className="w-full accent-cyan-600" />
            </aside>

            <section className="flex-1 min-w-0">
              <div className="mb-3 flex items-center gap-2 flex-wrap justify-between">
                <div className="text-sm text-slate-500 dark:text-zinc-400 flex items-center gap-2 flex-wrap">
                  共 {data.count} 个数据集
                  {filters.search && data.mode && (
                    <span className={`text-xs px-2 py-0.5 rounded ${data.mode === "semantic" ? "bg-cyan-100 text-cyan-700 dark:bg-cyan-400/15 dark:text-cyan-300" : "bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-400"}`}>
                      {data.mode === "semantic" ? "🧠 语义搜索（跨语言）" : "关键词搜索"}
                    </span>
                  )}
                </div>
                <div className="flex items-center rounded-lg border border-slate-200 dark:border-zinc-800 overflow-hidden">
                  {[["gallery", "画廊", LayoutGrid], ["list", "列表", List]].map(([k, label, Icon]) => (
                    <button key={k} onClick={() => setView(k)} title={label}
                      className={`inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium ${
                        view === k ? "bg-cyan-600 text-white" : "bg-white dark:bg-zinc-900 text-slate-500 dark:text-zinc-400 hover:text-cyan-600"}`}>
                      <Icon size={14} />{label}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div className="flex items-center justify-center gap-3 text-rose-600 dark:text-rose-400 text-sm mb-3 py-2 rounded-lg bg-rose-50 dark:bg-rose-500/10">
                  <span className="flex items-center gap-1.5"><WifiOff size={15} /> {error}</span>
                  <button onClick={() => setFilters((f) => ({ ...f }))}
                    className="px-2.5 py-1 rounded-md border border-rose-300 dark:border-rose-500/40 text-xs font-medium hover:bg-white dark:hover:bg-zinc-900">
                    重试
                  </button>
                </div>
              )}
              {error && data.datasets.length === 0 ? null : loading ? (
                <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-16 justify-center">
                  <Loader2 size={18} className="animate-spin" /> 加载中…
                </div>
              ) : data.datasets.length === 0 ? (
                <div className="text-slate-400 dark:text-zinc-500 text-sm py-16 text-center">没有符合条件的数据集，试试放宽筛选。</div>
              ) : (
                <>
                  <div className={view === "gallery"
                    ? "grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-3"
                    : "grid gap-3"}>
                    {data.datasets.map((d) => (
                      <DatasetCard key={d.dataset_id} d={d} onOpen={setSelected} query={filters.search}
                        inCart={cart.has(d.dataset_id)} onToggleCart={toggleCart}
                        gallery={view === "gallery"} />
                    ))}
                  </div>
                  {data.pages > 1 && (
                    <div className="flex items-center justify-center gap-3 mt-5 text-sm">
                      <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-zinc-700 text-slate-600 dark:text-zinc-300 disabled:opacity-40 hover:border-cyan-500">
                        <ChevronLeft size={15} /> 上一页
                      </button>
                      <span className="text-slate-500 dark:text-zinc-400 font-mono">{page} / {data.pages}</span>
                      <button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-zinc-700 text-slate-600 dark:text-zinc-300 disabled:opacity-40 hover:border-cyan-500">
                        下一页 <ChevronRight size={15} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </section>
          </div>
        )}
      </main>

      {/* 训练集购物车（底部悬浮条） */}
      {cart.size > 0 && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-20 bg-zinc-900 text-white rounded-full shadow-2xl px-5 py-3 flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-sm"><ShoppingCart size={16} /> 训练集：{cart.size} 个数据集</span>
          <button onClick={saveCart} title="保存为收藏集（需登录）"
            className="inline-flex items-center gap-1.5 border border-zinc-600 hover:border-cyan-400 text-zinc-100 text-sm font-semibold px-3 py-1.5 rounded-full">
            <Save size={14} /> 保存为收藏集
          </button>
          <button onClick={exportCart} className="inline-flex items-center gap-1.5 bg-cyan-500 hover:bg-cyan-400 text-white text-sm font-semibold px-3 py-1.5 rounded-full">
            <Download size={14} /> 导出训练清单
          </button>
          <button onClick={() => setCart(new Set())} className="text-zinc-400 hover:text-white" title="清空"><X size={16} /></button>
        </div>
      )}

      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuthed={setUser} />}
      {colsOpen && <CollectionsPanel onClose={() => setColsOpen(false)} onLoad={(ids) => setCart(new Set(ids))} />}
      {selected && <Detail id={selected} onClose={() => setSelected(null)} onOpen={setSelected} />}
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <div className="mb-3">
      <div className="text-sm text-slate-600 dark:text-zinc-400 mb-1">{label}</div>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded-lg px-2 py-2 text-sm bg-white">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}
