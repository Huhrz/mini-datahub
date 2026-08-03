import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api.js";
import { GraduationCap, HelpCircle, Loader2, CheckCircle2, Circle, ArrowRight } from "lucide-react";

/* ============ 术语词典（全局加载一次，供悬停讲解） ============ */
const GlossaryCtx = createContext({});

export function GlossaryProvider({ children }) {
  const [terms, setTerms] = useState({});
  useEffect(() => { api.glossary().then((r) => setTerms(r.terms || {})).catch(() => {}); }, []);
  return <GlossaryCtx.Provider value={terms}>{children}</GlossaryCtx.Provider>;
}

/* 可悬停的术语：包住任意文字，鼠标移上去显示解释气泡 */
export function Term({ k, children, className = "" }) {
  const terms = useContext(GlossaryCtx);
  const [open, setOpen] = useState(false);
  const t = terms[k];
  if (!t) return <span className={className}>{children}</span>;
  return (
    <span className={`relative inline-flex items-center gap-0.5 ${className}`}
      onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <span className="border-b border-dashed border-slate-400 dark:border-zinc-500 cursor-help">{children}</span>
      <HelpCircle size={11} className="text-slate-400 dark:text-zinc-500 shrink-0" />
      {open && (
        <span className="absolute left-0 top-full z-50 mt-1.5 w-80 max-w-[80vw] p-3 rounded-xl shadow-xl
          bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 text-left font-normal">
          <span className="block font-semibold text-slate-900 dark:text-zinc-100 text-sm mb-1">{t.term}</span>
          <span className="block text-[13px] text-slate-600 dark:text-zinc-300 leading-relaxed mb-1.5">{t.what}</span>
          <span className="block text-[13px] text-cyan-700 dark:text-cyan-300 leading-relaxed">
            <b>为什么重要：</b>{t.why}
          </span>
          {t.values && (
            <span className="block mt-2 pt-2 border-t border-slate-100 dark:border-zinc-800">
              {Object.entries(t.values).map(([v, d]) => (
                <span key={v} className="block text-[12px] text-slate-500 dark:text-zinc-400 leading-relaxed">
                  <code className="text-slate-700 dark:text-zinc-200">{v}</code> — {d}
                </span>
              ))}
            </span>
          )}
        </span>
      )}
    </span>
  );
}

/* ============ 学习路径页 ============ */
export function LearnView({ onOpenDataset }) {
  const [steps, setSteps] = useState(null);
  const [done, setDone] = useState(() => {
    try { return new Set(JSON.parse(localStorage.getItem("mdh-learn-done") || "[]")); }
    catch { return new Set(); }
  });
  const [openStep, setOpenStep] = useState("S1");

  useEffect(() => { api.learningPath().then((r) => setSteps(r.steps || [])).catch(() => setSteps([])); }, []);
  const toggle = (id) => setDone((d) => {
    const n = new Set(d); n.has(id) ? n.delete(id) : n.add(id);
    try { localStorage.setItem("mdh-learn-done", JSON.stringify([...n])); } catch {}
    return n;
  });

  if (!steps) return (
    <div className="flex items-center gap-2 text-slate-400 dark:text-zinc-500 text-sm py-16 justify-center">
      <Loader2 size={16} className="animate-spin" /> 加载学习路径…</div>
  );

  const pct = steps.length ? Math.round(100 * done.size / steps.length) : 0;

  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-800 p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
          <GraduationCap size={20} className="text-cyan-600" /> 机器人数据入门路径
        </h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          面向刚接触机器人数据的同学：6 步，从「看懂一条轨迹」到「为训练选数据、找研究空白」。
          每步都能在本站真做一遍，示例数据集来自当前目录。
        </p>
        <div className="mt-4 flex items-center gap-3">
          <div className="flex-1 h-2 bg-slate-100 dark:bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-cyan-600 transition-all" style={{ width: pct + "%" }} />
          </div>
          <span className="text-xs text-slate-500 dark:text-zinc-400 font-mono whitespace-nowrap">
            {done.size}/{steps.length} 已完成
          </span>
        </div>
      </div>

      {steps.map((s) => {
        const isOpen = openStep === s.id;
        const isDone = done.has(s.id);
        return (
          <div key={s.id}
            className={`bg-white dark:bg-zinc-900 rounded-2xl border shadow-sm overflow-hidden transition
              ${isDone ? "border-cyan-300 dark:border-cyan-700" : "border-slate-200 dark:border-zinc-800"}`}>
            <button onClick={() => setOpenStep(isOpen ? null : s.id)}
              className="w-full flex items-center gap-3 p-5 text-left">
              <span onClick={(e) => { e.stopPropagation(); toggle(s.id); }}
                className={isDone ? "text-cyan-600" : "text-slate-300 dark:text-zinc-600 hover:text-cyan-500"}>
                {isDone ? <CheckCircle2 size={20} /> : <Circle size={20} />}
              </span>
              <span className="flex-1 min-w-0">
                <span className="block font-semibold text-slate-900 dark:text-zinc-100">{s.title}</span>
                <span className="block text-sm text-slate-500 dark:text-zinc-400 truncate">{s.goal}</span>
              </span>
              <span className="text-slate-400 text-sm shrink-0">{isOpen ? "收起" : "展开"}</span>
            </button>

            {isOpen && (
              <div className="px-5 pb-5 space-y-4 border-t border-slate-100 dark:border-zinc-800 pt-4">
                <div>
                  <div className="text-xs font-semibold text-slate-400 dark:text-zinc-500 mb-1.5 tracking-wide">要理解的概念</div>
                  <ul className="space-y-1.5">
                    {s.learn.map((l, i) => (
                      <li key={i} className="text-sm text-slate-700 dark:text-zinc-300 leading-relaxed flex gap-2">
                        <span className="text-cyan-500 shrink-0">·</span>
                        <span dangerouslySetInnerHTML={{ __html: l.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>") }} />
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-cyan-50 dark:bg-cyan-500/10 rounded-xl p-3.5">
                  <div className="text-xs font-semibold text-cyan-700 dark:text-cyan-300 mb-1">动手做</div>
                  <div className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed">{s.do}</div>
                </div>

                {s.terms?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-400 dark:text-zinc-500 mb-1.5">相关术语（悬停看解释）</div>
                    <div className="flex flex-wrap gap-2">
                      {s.terms.map((k) => (
                        <span key={k} className="text-xs px-2 py-1 rounded-md bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-300">
                          <Term k={k}>{k}</Term>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {s.examples?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-400 dark:text-zinc-500 mb-1.5">用这些数据集练手</div>
                    <div className="space-y-1.5">
                      {s.examples.map((e) => (
                        <button key={e.dataset_id} onClick={() => onOpenDataset(e.dataset_id)}
                          className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg border
                            border-slate-200 dark:border-zinc-800 hover:border-cyan-500 text-left transition">
                          <span className="min-w-0">
                            <span className="block text-sm font-medium text-slate-800 dark:text-zinc-100 truncate">{e.name}</span>
                            <span className="block text-xs text-slate-400 dark:text-zinc-500 font-mono truncate">{e.dataset_id}</span>
                          </span>
                          <span className="shrink-0 flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400">
                            {e.embodiment} · {e.n_episodes} 轨迹
                            <ArrowRight size={14} className="text-cyan-600" />
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-sm text-slate-600 dark:text-zinc-400 border-l-2 border-slate-200 dark:border-zinc-700 pl-3">
                  <b className="text-slate-700 dark:text-zinc-300">自检：</b>{s.check}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
