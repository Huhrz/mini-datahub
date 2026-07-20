// 与 FastAPI 后端通信的小封装。开发时经 vite 代理转发到 :8000
const BASE = "/api";

async function get(path, params) {
  const qs = params
    ? "?" + new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== "" && v !== false && v != null)
      ).toString()
    : "";
  const r = await fetch(`${BASE}${path}${qs}`);
  if (!r.ok) throw new Error(`API ${path} ${r.status}`);
  return r.json();
}

export const api = {
  stats: () => get("/stats"),
  facets: () => get("/facets"),
  datasets: (filters) => get("/datasets", filters),
  detail: (id) => get(`/datasets/${id}`),
  coverage: () => get("/coverage"),
  search: (q, page, page_size) => get("/search", { q, page, page_size }),
  exportManifest: (ids) => get("/export", { ids: ids.join(",") }),
  preview: (id) => get(`/preview/${id}`),
  samples: (id) => get(`/samples/${id}`),
  episode: (id, ep = 0) => get(`/episode/${id}`, { ep }),
  croissantUrl: (id) => `${BASE}/croissant/${id}`,
  similar: (id) => get(`/similar/${id}`),
  gaps: () => get("/gaps"),
  benchmarks: (id) => get(`/benchmarks/${id}`),
};
