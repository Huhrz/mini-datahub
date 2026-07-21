// 与 FastAPI 后端通信的小封装。开发时经 vite 代理转发到 :8000
const BASE = "/api";

// ---- 登录 token（存 localStorage，随请求带 Authorization 头）----
let _token = (typeof localStorage !== "undefined" && localStorage.getItem("mdh-token")) || "";
export function setToken(t) {
  _token = t || "";
  if (typeof localStorage === "undefined") return;
  if (t) localStorage.setItem("mdh-token", t);
  else localStorage.removeItem("mdh-token");
}
export function getToken() { return _token; }
function authHeaders() { return _token ? { Authorization: `Bearer ${_token}` } : {}; }

async function get(path, params) {
  const qs = params
    ? "?" + new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== "" && v !== false && v != null)
      ).toString()
    : "";
  const r = await fetch(`${BASE}${path}${qs}`, { headers: authHeaders() });
  if (!r.ok) throw new Error(`API ${path} ${r.status}`);
  return r.json();
}

async function send(path, method, body) {
  const r = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: body != null ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `API ${path} ${r.status}`);
  return data;
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
  thumbs: (id, make = 0) => get(`/thumbs/${id}`, make ? { make } : undefined),
  samples: (id) => get(`/samples/${id}`),
  episode: (id, ep = 0) => get(`/episode/${id}`, { ep }),
  croissantUrl: (id) => `${BASE}/croissant/${id}`,
  similar: (id) => get(`/similar/${id}`),
  gaps: () => get("/gaps"),
  benchmarks: (id) => get(`/benchmarks/${id}`),
  oxeHf: (id) => get(`/oxe_hf/${id}`),

  // ---- 账户 ----
  register: (username, password) => send("/auth/register", "POST", { username, password }),
  login: (username, password) => send("/auth/login", "POST", { username, password }),
  logout: () => send("/auth/logout", "POST"),
  me: () => get("/auth/me"),

  // ---- 收藏集 ----
  listCollections: () => get("/collections"),
  createCollection: (name, ids) => send("/collections", "POST", { name, ids }),
  getCollection: (cid) => get(`/collections/${cid}`),
  deleteCollection: (cid) => send(`/collections/${cid}`, "DELETE"),
};
