const { StatCard, Tag, Tabs, SearchInput, Select, Checkbox, Slider, DatasetCard, DetailDrawer, Alert, Button, CoverageHeatmap } =
  window.MiniDataHubDesignSystem_f6abe1;
const { STATS, FACETS, DATASETS, COVERAGE_CELLS } = window.MOCK;

const EMBODIMENT_OPTS = [{ value: "", label: "（不限）" }, ...FACETS.embodiments.map((e) => ({ value: e, label: e }))];
const FORMAT_OPTS = [{ value: "", label: "（不限）" }, ...FACETS.formats.map((e) => ({ value: e, label: e }))];
const PROV_OPTS = [{ value: "", label: "（不限）" }, ...FACETS.provenances.map((e) => ({ value: e, label: e }))];
const CONCEPT_OPTS = [{ value: "", label: "（不限）" }, ...FACETS.concepts.map((c) => ({ value: c.id, label: c.label }))];

const CONCEPT_LABELS = { 抓取放置: "pick_place", 推动: "pushing", 插入装配: "insertion", 折叠: "folding", 开启: "opening", 堆叠: "stacking", 导航: "navigation" };

function fmtNum(n) {
  return n.toLocaleString("en-US");
}

function Sidebar({ filters, setFilter }) {
  return (
    <aside
      style={{
        width: "var(--sidebar-width)",
        flexShrink: 0,
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-xl)",
        padding: 20,
        boxShadow: "var(--shadow-sm)",
        height: "fit-content",
      }}
    >
      <h3 style={{ fontSize: "var(--text-h3)", fontWeight: "var(--weight-bold)", margin: "0 0 14px", display: "flex", alignItems: "center", gap: 6, color: "var(--text-primary)" }}>
        <i data-lucide="sliders-horizontal" style={{ width: 16, height: 16 }} /> 筛选
      </h3>
      <div style={{ marginBottom: 14 }}>
        <SearchInput value={filters.search} onChange={(v) => setFilter("search", v)} />
      </div>
      <Select label="任务概念" value={filters.concept} onChange={(v) => setFilter("concept", v)} options={CONCEPT_OPTS} />
      <Select label="本体类型" value={filters.embodiment} onChange={(v) => setFilter("embodiment", v)} options={EMBODIMENT_OPTS} />
      <Select label="源格式" value={filters.format} onChange={(v) => setFilter("format", v)} options={FORMAT_OPTS} />
      <Select label="采集方式" value={filters.provenance} onChange={(v) => setFilter("provenance", v)} options={PROV_OPTS} />
      <Checkbox label="仅可商用" checked={filters.commercial_only} onChange={(v) => setFilter("commercial_only", v)} />
      <Checkbox label="仅含失败标注" checked={filters.failures_only} onChange={(v) => setFilter("failures_only", v)} />
      <Slider label="最低质量分" value={filters.min_quality} onChange={(v) => setFilter("min_quality", v)} format={(v) => v.toFixed(2)} />
    </aside>
  );
}

function Detail({ d, onClose }) {
  if (!d) return null;
  return (
    <DetailDrawer open={!!d} onClose={onClose} title={d.name} subtitle={d.dataset_id}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 20 }}>
        <StatCard label="本体" value={d.embodiment} />
        <StatCard label="轨迹数" value={fmtNum(d.n_episodes)} />
        <StatCard label="可商用" value={d.commercial_ok ? "是" : "否"} />
      </div>

      <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.8 }}>
        <div>
          许可证：<code style={{ background: "var(--surface-sunken)", padding: "2px 6px", borderRadius: 4, fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{d.license_spdx}</code>　
          源格式：<code style={{ background: "var(--surface-sunken)", padding: "2px 6px", borderRadius: 4, fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{d.source_format}</code>
        </div>
        <div>采集方式：{d.provenance_type}　来源：{d.source}</div>
        <div>
          质量分：<span style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)", fontWeight: 600 }}>{d.quality_score?.toFixed(2)}</span>
          {d.quality_tier === "metadata" && <span style={{ color: "var(--text-tertiary)" }}> （元数据初筛）</span>}
        </div>
      </div>

      {!d.commercial_ok && (
        <div style={{ marginBottom: 16 }}>
          <Alert tone="warning">该数据集不可商用，请勿混入商业训练集。</Alert>
        </div>
      )}

      {d.action_convention && (
        <div style={{ marginBottom: 12, fontSize: "var(--text-sm)" }}>
          <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>动作约定：</span>
          {Object.entries(d.action_convention).map(([k, v]) => (
            <Tag key={k}>{k}={String(v)}</Tag>
          ))}
        </div>
      )}

      {["tasks", "scenes", "modalities"].map((f) =>
        (d[f] || []).length > 0 ? (
          <div key={f} style={{ marginBottom: 10, fontSize: "var(--text-sm)" }}>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
              {{ tasks: "任务", scenes: "场景", modalities: "模态" }[f]}：
            </span>
            {d[f].map((v) => (
              <Tag key={v} tone="accent">{v}</Tag>
            ))}
          </div>
        ) : null
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
        {(d.source === "huggingface" || String(d.source_format).includes("lerobot")) && (
          <Button variant="primary" icon="play" href={`https://huggingface.co/spaces/lerobot/visualize_dataset?dataset=${d.dataset_id}`} target="_blank">
            在线可视化
          </Button>
        )}
        {d.homepage && (
          <Button variant="secondary" icon="external-link" href={d.homepage} target="_blank">
            数据集主页
          </Button>
        )}
      </div>
    </DetailDrawer>
  );
}

function App() {
  const [tab, setTab] = React.useState("list");
  const [selected, setSelected] = React.useState(null);
  const [theme, setTheme] = React.useState("dark");
  const [filters, setFilters] = React.useState({
    search: "", embodiment: "", format: "", provenance: "", concept: "",
    commercial_only: false, failures_only: false, min_quality: 0,
  });
  const setFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v }));

  React.useEffect(() => {
    window.lucide && window.lucide.createIcons();
  });

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
  }, [theme]);

  const filtered = DATASETS.filter((d) => {
    if (filters.search && !(`${d.name} ${d.dataset_id}`.toLowerCase().includes(filters.search.toLowerCase()))) return false;
    if (filters.embodiment && d.embodiment !== filters.embodiment) return false;
    if (filters.format && d.source_format !== filters.format) return false;
    if (filters.provenance && d.provenance_type !== filters.provenance) return false;
    if (filters.commercial_only && !d.commercial_ok) return false;
    if (filters.failures_only && !d.has_failure_labels) return false;
    if (filters.min_quality && (d.quality_score || 0) < filters.min_quality) return false;
    if (filters.concept) {
      const ids = (d.tasks || []).map((t) => CONCEPT_LABELS[t]);
      if (!ids.includes(filters.concept)) return false;
    }
    return true;
  });

  const selectedDataset = DATASETS.find((d) => d.dataset_id === selected);

  return (
    <div style={{ minHeight: "100vh" }}>
      <header style={{ background: "var(--surface-inverse)", color: "var(--text-on-inverse)", padding: "28px 0", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", padding: "0 32px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ fontSize: "var(--text-h1)", fontWeight: 700, margin: 0, letterSpacing: "var(--tracking-hero)", textTransform: "uppercase", color: "var(--text-on-inverse)" }}>
              机器人 DataHub
            </h1>
            <p style={{ color: "var(--gray-400)", marginTop: 6, fontSize: "var(--text-sm)" }}>
              跨源聚合 · 统一检索 · 自动质检 · 覆盖度地图 —— 具身智能数据的联邦门户
            </p>
          </div>
          <button
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              background: "transparent", border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius-md)", padding: "7px 12px",
              color: "var(--text-on-inverse)", fontSize: "var(--text-xs)",
              fontFamily: "var(--font-sans)", cursor: "pointer",
            }}
          >
            <i data-lucide={theme === "dark" ? "sun" : "moon"} style={{ width: 14, height: 14 }} />
            {theme === "dark" ? "浅色" : "深色"}
          </button>
        </div>
      </header>

      <main style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", padding: "24px 32px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
          <StatCard label="数据集数量" value={fmtNum(STATS.n_datasets)} icon="database" />
          <StatCard label="轨迹总数" value={fmtNum(STATS.n_episodes)} icon="git-branch" />
          <StatCard label="总帧数" value={fmtNum(STATS.n_frames)} icon="film" />
        </div>

        <div style={{ marginBottom: 20 }}>
          <Tabs items={[{ key: "list", label: "数据集" }, { key: "coverage", label: "覆盖度地图" }]} active={tab} onChange={setTab} />
        </div>

        {tab === "coverage" ? (
          <CoverageHeatmap embodiments={FACETS.embodiments} concepts={FACETS.concepts} cells={COVERAGE_CELLS} />
        ) : (
          <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
            <Sidebar filters={filters} setFilter={setFilter} />
            <section style={{ flex: 1 }}>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 12 }}>
                共 {filtered.length} 个数据集
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filtered.map((d) => (
                  <DatasetCard key={d.dataset_id} dataset={d} onClick={() => setSelected(d.dataset_id)} />
                ))}
                {filtered.length === 0 && (
                  <div style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "40px 0", textAlign: "center" }}>
                    没有符合条件的数据集，试试放宽筛选。
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>

      <Detail d={selectedDataset} onClose={() => setSelected(null)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
