/* util inti */
export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];

export const fmt = {
  time: (ts) => new Date((ts || 0) * 1000).toLocaleTimeString('id-ID', { hour12: false }),
  date: (ts) => new Date((ts || 0) * 1000).toLocaleString('id-ID'),
  ago(ts) {
    const s = Math.max(0, Date.now() / 1000 - (ts || 0));
    if (s < 60) return `${s | 0}s lalu`;
    if (s < 3600) return `${(s / 60) | 0}m lalu`;
    if (s < 86400) return `${(s / 3600) | 0}j lalu`;
    return `${(s / 86400) | 0}h lalu`;
  },
  bytes(n) {
    n = Number(n) || 0;
    const u = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
  },
};

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export function toast(msg, kind = '') {
  let wrap = $('#tw');
  if (!wrap) { wrap = document.createElement('div'); wrap.id = 'tw'; wrap.className = 'toast-wrap'; document.body.appendChild(wrap); }
  const el = document.createElement('div');
  el.className = 'toast ' + kind;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

export async function api(path, opts = {}) {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) { location.href = '/403'; throw new Error('401'); }
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res;
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

export const post = (p, body) => api(p, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body || {}),
});
export const patch = (p, body) => api(p, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body || {}),
});

/* sidebar aktif */
export function markNav() {
  const here = location.pathname;
  $$('.nav a').forEach((a) => {
    if (a.getAttribute('href') === here) a.classList.add('on');
  });
}

/* jam */
export function clock(el) {
  const tick = () => { el.textContent = new Date().toLocaleTimeString('id-ID', { hour12: false }); };
  tick();
  return setInterval(tick, 1000);
}
