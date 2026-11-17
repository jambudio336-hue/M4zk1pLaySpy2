/* hub realtime operator */
import { toast, jitter } from './core.js';

const handlers = new Map();
export function on(type, fn) {
  if (!handlers.has(type)) handlers.set(type, new Set());
  handlers.get(type).add(fn);
  return () => handlers.get(type).delete(fn);
}

let sock = null;
let tries = 0;
let beat = null;

function emit(msg) {
  const set = handlers.get(msg.t);
  if (set) set.forEach((fn) => { try { fn(msg); } catch (e) { console.error(e); } });
}

export function connect() {
  if (sock && sock.readyState <= 1) return sock;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  sock = new WebSocket(proto + '://' + location.host + '/ws/operator');

  sock.onopen = () => {
    tries = 0;
    clearInterval(beat);
    beat = setInterval(() => {
      if (sock.readyState === 1) sock.send(JSON.stringify({ t: 'ping' }));
    }, jitter(19000, 4000));
    emit({ t: 'open' });
  };
  sock.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    emit(msg);
  };
  sock.onclose = () => {
    clearInterval(beat);
    emit({ t: 'close' });
    tries++;
    if (tries <= 8) setTimeout(connect, Math.min(9000, jitter(600, 900)));
    else toast('Koneksi C2 terputus.', 'wn');
  };
  sock.onerror = () => { try { sock.close(); } catch {} };
  return sock;
}

export const ready = () => !!sock && sock.readyState === 1;

export function send(type, target, args) {
  if (!ready()) { toast('Realtime belum tersambung.', 'wn'); return false; }
  sock.send(JSON.stringify({ t: 'cmd', type, target, args: args || {} }));
  return true;
}

export function statusLed(el) {
  on('open', () => el && el.classList.add('on'));
  on('close', () => el && el.classList.remove('on'));
}
