import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { Loader2, ExternalLink, ChevronLeft, ChevronRight, Film } from "lucide-react";

// 自建播放器：HTML5 <video>（媒体直连源 CDN）+ 与视频同步的状态/动作曲线。
// 完全我们自己控制的 UI，不嵌任何第三方网站。
export default function EpisodePlayer({ datasetId, compact = false, initialEp = 0 }) {
  const [ep, setEp] = useState(initialEp);
  useEffect(() => { setEp(initialEp); }, [initialEp]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const videoRef = useRef(null);
  const slaveRefs = useRef([]);
  const canvasRef = useRef(null);
  const [prog, setProg] = useState(0); // 0..1

  useEffect(() => {
    let cancel = false;
    setLoading(true); setErr(null); setData(null); setProg(0);
    api.episode(datasetId, ep)
      .then((d) => { if (!cancel) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancel) { setErr("加载失败，请确认后端在运行"); setLoading(false); } });
    return () => { cancel = true; };
  }, [datasetId, ep]);

  // 主视频驱动进度 + 同步其它相机
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    let raf;
    const cams = data?.cameras || [];
    const mClip = cams[0]?.clip;               // 主相机的时间片 [from,to]（v3.0 才有）
    const tick = () => {
      if (v.duration) {
        let t = v.currentTime;
        if (mClip) {
          // v3.0：把播放约束在该集的 [from,to] 区间里循环
          if (t >= mClip[1] || t < mClip[0] - 0.1) { v.currentTime = mClip[0]; t = mClip[0]; }
          setProg((t - mClip[0]) / ((mClip[1] - mClip[0]) || 1));
        } else {
          setProg(t / v.duration);
        }
        slaveRefs.current.forEach((s, i) => {
          if (!s) return;
          const sClip = cams[i]?.clip;
          const target = (sClip && mClip) ? sClip[0] + (t - mClip[0]) : t;
          if (Math.abs(s.currentTime - target) > 0.15) s.currentTime = target;
        });
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [data]);

  // 画曲线 + 移动游标
  useEffect(() => {
    const cv = canvasRef.current;
    if (!cv || !data?.series) return;
    const names = Object.keys(data.series);
    const w = cv.width, h = cv.height;
    const ctx = cv.getContext("2d");
    ctx.clearRect(0, 0, w, h);
    if (names.length === 0) return;
    const palette = ["#06b6d4", "#f59e0b", "#22c55e", "#ef4444", "#a855f7", "#3b82f6",
                     "#ec4899", "#14b8a6", "#eab308", "#f97316", "#8b5cf6", "#10b981"];
    names.forEach((n, i) => {
      const arr = data.series[n];
      if (!arr || arr.length < 2) return;
      let mn = Infinity, mx = -Infinity;
      for (const v of arr) { if (v < mn) mn = v; if (v > mx) mx = v; }
      const rng = mx - mn || 1;
      ctx.strokeStyle = palette[i % palette.length];
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      arr.forEach((v, j) => {
        const x = (j / (arr.length - 1)) * w;
        const y = h - ((v - mn) / rng) * (h - 8) - 4;
        j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
    });
    // 游标
    const cx = prog * w;
    ctx.strokeStyle = "rgba(148,163,184,0.9)";
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, h); ctx.stroke();
  }, [data, prog]);

  if (loading) {
    return <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-10 justify-center">
      <Loader2 size={16} className="animate-spin" /> 加载回放…</div>;
  }
  if (err) return <div className="text-rose-500 text-sm py-6 text-center">{err}</div>;
  if (!data) return null;

  if (!data.playable) {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 p-5 text-sm text-slate-500 dark:text-zinc-400">
        {data.reason || "该数据集暂不支持内嵌回放。"}
        {data.homepage && (
          <a href={data.homepage} target="_blank" rel="noreferrer"
             className="inline-flex items-center gap-1 text-cyan-600 dark:text-cyan-400 ml-1 underline">
            前往数据集主页 <ExternalLink size={12} />
          </a>
        )}
      </div>
    );
  }

  const cams = data.cameras || [];
  const seriesNames = Object.keys(data.series || {});
  slaveRefs.current = [];

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100 flex items-center gap-1.5">
          <Film size={15} /> 回放 · 自建播放器
        </div>
        {data.total_episodes > 1 && (
          <div className="flex items-center gap-2 text-sm">
            <button disabled={ep <= 0} onClick={() => setEp((e) => Math.max(0, e - 1))}
              className="p-1 rounded border border-slate-300 dark:border-zinc-700 disabled:opacity-40 text-slate-600 dark:text-zinc-300"><ChevronLeft size={14} /></button>
            <span className="font-mono text-slate-600 dark:text-zinc-300">第 {ep} / {data.total_episodes - 1} 集</span>
            <button disabled={ep >= data.total_episodes - 1} onClick={() => setEp((e) => Math.min(data.total_episodes - 1, e + 1))}
              className="p-1 rounded border border-slate-300 dark:border-zinc-700 disabled:opacity-40 text-slate-600 dark:text-zinc-300"><ChevronRight size={14} /></button>
            <input type="number" min={0} max={data.total_episodes - 1} placeholder="跳转"
              onKeyDown={(e) => { if (e.key === "Enter") { const v = parseInt(e.target.value); if (!isNaN(v)) setEp(Math.max(0, Math.min(data.total_episodes - 1, v))); } }}
              className="w-16 border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded px-1.5 py-0.5 text-xs" title="输入集号回车跳转" />
          </div>
        )}
      </div>

      <div className={`grid gap-2 ${cams.length > 1 ? "grid-cols-2" : "grid-cols-1"}`}>
        {cams.map((c, i) => (
          <div key={c.name}>
            <div className="text-xs text-slate-400 dark:text-zinc-500 mb-1 font-mono">{c.name}</div>
            <video
              ref={i === 0 ? videoRef : (el) => { if (el) slaveRefs.current[i] = el; }}
              src={c.clip ? `${c.url}#t=${c.clip[0]}` : c.url}
              controls={i === 0}
              muted loop={!c.clip} playsInline preload="metadata"
              onLoadedMetadata={(e) => { if (c.clip) e.currentTarget.currentTime = c.clip[0]; }}
              className="w-full rounded-lg border border-slate-200 dark:border-zinc-800 bg-black"
              style={{ maxHeight: compact ? 260 : 340 }}
            />
          </div>
        ))}
      </div>

      {seriesNames.length > 0 && (
        <div className="mt-3">
          <div className="text-xs text-slate-500 dark:text-zinc-400 mb-1">状态 / 动作曲线（随视频游标同步）</div>
          <canvas ref={canvasRef} width={640} height={140}
            className="w-full rounded-lg border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-950" />
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
            {seriesNames.slice(0, 12).map((n, i) => (
              <span key={n} className="inline-flex items-center gap-1 text-[11px] text-slate-500 dark:text-zinc-400 font-mono">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: ["#06b6d4","#f59e0b","#22c55e","#ef4444","#a855f7","#3b82f6","#ec4899","#14b8a6","#eab308","#f97316","#8b5cf6","#10b981"][i % 12] }} />
                {n}
              </span>
            ))}
          </div>
        </div>
      )}
      {data.note && <div className="text-xs text-amber-600 dark:text-amber-400 mt-2">{data.note}</div>}
    </div>
  );
}

// 官方 LeRobot 可视化：直接嵌 HF 官方 Space（原生支持 v2.x/v3.0、含 3D URDF、
// 动作分析、大数据集分页等）。有现成好轮子就不自己造。
export function OfficialViz({ repoId, totalEpisodes = 0 }) {
  const [ep, setEp] = useState(0);
  const base = "https://lerobot-visualize-dataset.hf.space";
  const src = `${base}/${repoId}/episode_${ep}`;
  const maxEp = totalEpisodes > 0 ? totalEpisodes - 1 : null;
  return (
    <div>
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <div className="text-xs text-slate-500 dark:text-zinc-400">
          由 LeRobot 官方可视化提供 · 支持 v2.x/v3.0、3D 姿态、动作分析
        </div>
        <div className="flex items-center gap-2 text-sm">
          <input type="number" min={0} max={maxEp ?? undefined} placeholder="集号"
            onKeyDown={(e) => { if (e.key === "Enter") { const v = parseInt(e.target.value); if (!isNaN(v)) setEp(Math.max(0, maxEp != null ? Math.min(maxEp, v) : v)); } }}
            className="w-20 border border-slate-300 dark:border-zinc-700 dark:bg-zinc-950 text-slate-800 dark:text-zinc-100 rounded px-1.5 py-0.5 text-xs" title="输入集号回车跳转" />
          <a href={src} target="_blank" rel="noreferrer"
             className="inline-flex items-center gap-1 text-cyan-600 dark:text-cyan-400 hover:underline">
            <ExternalLink size={13} /> 新标签打开
          </a>
        </div>
      </div>
      <iframe title={`official-${repoId}`} src={src}
        className="w-full rounded-lg border border-slate-200 dark:border-zinc-800 bg-white"
        style={{ height: 620 }} allow="fullscreen" />
    </div>
  );
}

// 一条样本的迷你片段：定位到该集时间片，悬停在区间内循环播放。
function SampleClip({ cam }) {
  const vref = useRef(null);
  const clip = cam.clip;
  const src = clip ? `${cam.url}#t=${clip[0]}` : cam.url;
  return (
    <video ref={vref} src={src} muted loop={!clip} playsInline preload="metadata"
      onLoadedMetadata={(e) => { if (clip) e.currentTarget.currentTime = clip[0]; }}
      onTimeUpdate={(e) => { const v = e.currentTarget; if (clip && (v.currentTime >= clip[1] || v.currentTime < clip[0])) v.currentTime = clip[0]; }}
      onMouseEnter={() => vref.current && vref.current.play().catch(() => {})}
      onMouseLeave={() => { if (vref.current) { vref.current.pause(); if (clip) vref.current.currentTime = clip[0]; } }}
      className="w-full aspect-video object-cover bg-black" />
  );
}

// 代表性样本条：~10 条轨迹的迷你片段，点选加载完整回放。
export function SampleStrip({ datasetId, onPick, activeEp }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancel = false;
    setLoading(true);
    api.samples(datasetId)
      .then((d) => { if (!cancel) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [datasetId]);

  if (loading) return (
    <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-6 justify-center">
      <Loader2 size={15} className="animate-spin" /> 采样代表性轨迹…</div>
  );
  const samples = data?.samples || [];
  if (!samples.length) return (
    <div className="text-slate-400 dark:text-zinc-500 text-sm py-3">暂无可视化样本（该来源/格式尚未适配，或视频不可切片）。</div>
  );
  return (
    <div>
      <div className="text-xs text-slate-500 dark:text-zinc-400 mb-2">
        代表性样本（共展示 {samples.length} 条，点选加载完整回放 + 曲线）
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
        {samples.map((s) => (
          <button key={s.episode} onClick={() => onPick(s.episode)} title={`第 ${s.episode} 集`}
            className={`relative rounded-lg overflow-hidden border transition ${
              activeEp === s.episode ? "border-cyan-500 ring-2 ring-cyan-500"
                                     : "border-slate-200 dark:border-zinc-800 hover:border-cyan-400"}`}>
            {s.cameras?.[0] ? <SampleClip cam={s.cameras[0]} />
              : <div className="w-full aspect-video bg-slate-100 dark:bg-zinc-800" />}
            <span className="absolute bottom-0 left-0 right-0 bg-black/55 text-white text-[10px] px-1 py-0.5 font-mono">#{s.episode}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// 卡片缩略图：懒加载预览视频（首帧即缩略图，悬停播放）。拿不到则占位。
export function Thumbnail({ datasetId, embodiment }) {
  const [state, setState] = useState("loading"); // loading|ok|none
  const [url, setUrl] = useState(null);
  const ref = useRef(null);
  const vref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let done = false;
    const io = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !done) {
        done = true; io.disconnect();
        api.preview(datasetId)
          .then((r) => { r?.video ? (setUrl(r.video), setState("ok")) : setState("none"); })
          .catch(() => setState("none"));
      }
    }, { rootMargin: "200px" });
    io.observe(el);
    return () => io.disconnect();
  }, [datasetId]);

  return (
    <div ref={ref}
      onMouseEnter={() => vref.current && vref.current.play().catch(() => {})}
      onMouseLeave={() => vref.current && vref.current.pause()}
      className="relative w-full aspect-video rounded-lg overflow-hidden bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-800">
      {state === "ok" && url ? (
        <video ref={vref} src={url} muted loop playsInline preload="metadata"
          onError={() => setState("none")}
          className="w-full h-full object-cover" />
      ) : state === "loading" ? (
        <div className="w-full h-full flex items-center justify-center">
          <Loader2 size={16} className="animate-spin text-slate-300 dark:text-zinc-600" />
        </div>
      ) : (
        <div className="w-full h-full flex items-center justify-center text-slate-300 dark:text-zinc-600 text-4xl">
          {{ bimanual: "🦾", humanoid: "🤖", mobile: "🚗", single_arm: "🦾" }[embodiment] || "🤖"}
        </div>
      )}
    </div>
  );
}
