/* util inti */
export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];

export const fmt = {
  time: (ts) => new Date((ts || 0) * 1000).toLocaleTimeString('id-ID', { hour12: false }),
  date: (ts) => new Date((ts || 0) * 1000).toLocaleString('id-ID'),
  ago(ts) {
    const s = Math.max(0, Date.now() / 1000 - (ts || 0));
    if (s < 60) return `${s | 0}s`;
    if (s < 3600) return `${(s / 60) | 0}m`;
    if (s < 86400) return `${(s / 3600) | 0}j`;
    return `${(s / 86400) | 0}h`;
  },
  bytes(n) {
    n = Number(n) || 0;
    const u = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
  },
};

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function toast(msg, kind = '') {
  let wrap = $('#tw');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'tw';
    wrap.className = 'toast-wrap';
    document.body.appendChild(wrap);
  }
  const el = document.createElement('div');
  el.className = 'toast ' + kind;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3600);
}

export async function api(path, opts = {}) {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) { location.href = '/403'; throw new Error('sesi habis'); }
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res;
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

const json = (m) => (p, body) => api(p, {
  method: m, headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body || {}),
});
export const post = json('POST');
export const patch = json('PATCH');
export const del = (p) => api(p, { method: 'DELETE' });

export function clock(el) {
  if (!el) return;
  const tick = () => { el.textContent = new Date().toLocaleTimeString('id-ID', { hour12: false }); };
  tick();
  return setInterval(tick, 1000);
}

export const copy = async (t) => {
  try { await navigator.clipboard.writeText(t); toast('Disalin.', 'ok'); }
  catch { toast('Gagal menyalin.', 'wn'); }
};

export function led(el, online, web) {
  if (!el) return;
  el.className = 'led' + (online ? (web ? ' web' : ' on') : '');
}
