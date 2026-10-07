// Deterministic timeline helpers. Every composition registers updaters with
// on(fn); the renderer calls window.seek(t) once per frame and screenshots.
(function () {
  const W = 1080, H = 1920;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const E = {
    lin: t => t,
    outCubic: t => 1 - Math.pow(1 - t, 3),
    inCubic: t => t * t * t,
    inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    outExpo: t => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
    outElastic: t => (t === 0 || t === 1 ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
    inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  };
  // 0→1 progress of [start, start+dur]
  const p = (t, start, dur, ease = E.outCubic) => ease(clamp((t - start) / Math.max(dur, 1e-4)));
  // visibility envelope: fades in at a, out at b
  const env = (t, a, b, fi = 0.35, fo = 0.35) => {
    if (t < a || t > b + fo) return 0;
    const i = fi > 0 ? clamp((t - a) / fi) : 1;
    const o = fo > 0 ? 1 - clamp((t - b) / fo) : (t <= b ? 1 : 0);
    return E.outCubic(Math.min(i, o));
  };

  const updaters = [];
  const on = fn => updaters.push(fn);

  // style setter: o opacity, x/y px, s scale, r deg, blur px, extra transform
  function S(el, { o, x = 0, y = 0, s = 1, r = 0, blur, tf = '', vis } = {}) {
    if (!el) return;
    if (o !== undefined) {
      el.style.opacity = o.toFixed(4);
      el.style.visibility = o <= 0.001 ? 'hidden' : 'visible';
    }
    if (vis !== undefined) el.style.visibility = vis ? 'visible' : 'hidden';
    el.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) scale(${s.toFixed(4)}) rotate(${r.toFixed(2)}deg) ${tf}`;
    if (blur !== undefined) el.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
  }

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  function el(tag, cls, html, parent) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    (parent || document.getElementById('stage')).appendChild(e);
    return e;
  }

  // seeded random for particles etc.
  function rng(seed) {
    let s = seed >>> 0;
    return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  }

  // timing helpers (window.TIMING injected by renderer)
  const T = () => window.TIMING;
  const L = i => T().lines[i];
  const ls = i => L(i).start;
  const le = i => L(i).end;
  const wordT = (i, w) => L(i).words[Math.min(w, L(i).words.length - 1)].s;

  // Captions: one line at a time. mode 'karaoke' shows full line with
  // unspoken words dimmed; 'reveal' pops words in as they are spoken.
  function captions(parent, opts = {}) {
    const { mode = 'karaoke', from = 0, to = 1e9, hold = 0.25 } = opts;
    const box = el('div', 'cap ' + (opts.cls || ''), '', parent);
    const lines = T().lines.map((ln, i) => {
      const row = el('div', 'cap-line', '', box);
      const spans = ln.words.map(w => {
        const sp = el('span', 'w' + (w.hl ? ' hl' : ''), w.w, row);
        return sp;
      });
      return { row, spans, i };
    });
    on(t => {
      lines.forEach(({ row, spans, i }) => {
        const ln = L(i);
        const next = i + 1 < T().lines.length ? L(i + 1).start : 1e9;
        const a = ln.start - 0.08, b = Math.min(next - 0.05, ln.end + (opts.linger || 0.6));
        const inRange = i >= from && i <= to;
        const v = inRange ? env(t, a, b, 0.18, 0.18) : 0;
        S(row, { o: v, y: (1 - p(t, a, 0.3)) * 18 });
        spans.forEach((sp, k) => {
          const w = ln.words[k];
          const said = p(t, w.s - 0.04, 0.16, E.outCubic);
          if (mode === 'reveal') {
            sp.style.opacity = said.toFixed(3);
            sp.style.transform = `translateY(${((1 - said) * 14).toFixed(1)}px)`;
          } else {
            sp.style.opacity = (0.32 + 0.68 * said).toFixed(3);
          }
          sp.classList.toggle('on', t >= w.s - 0.04);
        });
      });
    });
    return box;
  }

  // Ken Burns on an <img> covering its container
  function kenburns(img, t, a, b, { s0 = 1.0, s1 = 1.12, x0 = 0, x1 = 0, y0 = 0, y1 = -30 } = {}) {
    const k = E.inOutSine(clamp((t - a) / Math.max(b - a, 0.01)));
    img.style.transform = `translate(${lerp(x0, x1, k).toFixed(2)}px, ${lerp(y0, y1, k).toFixed(2)}px) scale(${lerp(s0, s1, k).toFixed(4)})`;
  }

  window.seek = t => { for (const u of updaters) u(t); };
  window.ready = async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(i => (i.complete ? Promise.resolve() : new Promise(r => { i.onload = i.onerror = r; }))));
    await Promise.all(Array.from(document.images).map(i => (i.decode ? i.decode().catch(() => {}) : null)));
    return true;
  };
  Object.assign(window, { W, H, clamp, lerp, E, p, env, on, S, $, $$, el, rng, T, L, ls, le, wordT, captions, kenburns });
})();
