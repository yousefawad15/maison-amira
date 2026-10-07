// Story template shared by v3 / v4. Each page sets window.CFG before loading this.
(function () {
  const C = window.CFG;
  const stage = document.getElementById('stage');
  const img = k => `../assets/gen/${k}.jpg`;

  // ---------- scene photos ----------
  const scenes = C.scenes.map((sc, k) => {
    const wrap = el('div', 'scene', '', stage);
    const im = el('img', 'ph', '', wrap); im.src = img(sc.img);
    return { ...sc, wrap, im, k };
  });
  const sStart = k => ls(C.scenes[k].from) - 0.35;
  const sEnd = k => (k + 1 < C.scenes.length ? sStart(k + 1) : ls(C.end.from) - C.end.lead);
  on(t => {
    scenes.forEach((s, k) => {
      const a = sStart(k), b = sEnd(k);
      const v = env(t, a, b, 0.55, 0.55);
      S(s.wrap, { o: v });
      const kb = s.kb || {};
      kenburns(s.im, t, a, b + 0.6, { s0: kb.s0 ?? 1.04, s1: kb.s1 ?? 1.14, x0: kb.x0 ?? 0, x1: kb.x1 ?? 0, y0: kb.y0 ?? 0, y1: kb.y1 ?? -40 });
    });
  });

  // grading + vignette + grain
  el('div', 'grade', '', stage);
  const grain = el('div', 'grain', '', stage);
  on(t => { const f = Math.floor(t * 24); grain.style.backgroundPosition = `${(f * 137) % 300}px ${(f * 71) % 300}px`; });

  // ---------- intro title card ----------
  const intro = el('div', 'intro', '', stage);
  const ibg = el('img', 'ph', '', intro); ibg.src = img(C.intro.bg); ibg.style.filter = 'blur(6px) brightness(.35)';
  const ik = el('div', 'kicker', C.intro.kicker, intro);
  const it = el('div', 'script title', C.intro.title, intro);
  const il = el('div', 'rule', '', intro);
  on(t => {
    const b = sStart(0);
    S(intro, { o: env(t, -1, b - 0.1, 0, 0.6) });
    kenburns(ibg, t, 0, b + 0.6, { s0: 1.15, s1: 1.05, y1: 0 });
    S(ik, { o: p(t, 0.2, 0.6), y: (1 - p(t, 0.2, 0.8)) * 20 });
    it.style.clipPath = `inset(0 0 0 ${(100 - 100 * p(t, 0.45, 1.2, E.inOutCubic)).toFixed(1)}%)`;
    S(it, { o: 1, y: (1 - p(t, 0.45, 1.2)) * 20 });
    il.style.transform = `scaleX(${p(t, 1.2, 0.8).toFixed(3)})`;
  });

  // ---------- chapter titles ----------
  const chap = scenes.map(s => {
    const g = el('div', 'chap', `<div class="chk">${s.ch}</div><div class="script cht">${s.chapter}</div>`, stage);
    return g;
  });
  on(t => {
    scenes.forEach((s, k) => {
      const a = sStart(k) + 0.4, b = sEnd(k) - 0.15;
      const g = chap[k];
      S(g, { o: env(t, a, b, 0.3, 0.3) });
      g.lastChild.style.clipPath = `inset(0 0 0 ${(100 - 100 * p(t, a + 0.1, 0.9, E.inOutCubic)).toFixed(1)}%)`;
    });
  });

  // ---------- countdown card (optional) ----------
  if (C.countdown) {
    const cd = el('div', 'cd', `<div class="cdh">${C.countdown.label}</div><div class="cdn"><span class="n0"></span><span class="n1"></span></div><div class="cdu">${C.countdown.unit}</div>`, stage);
    const n0 = cd.querySelector('.n0'), n1 = cd.querySelector('.n1');
    on(t => {
      const vis = env(t, sStart(0) + 0.3, sEnd(scenes.length - 1) - 0.15, 0.4, 0.3);
      S(cd, { o: vis, y: (1 - p(t, sStart(0) + 0.3, 0.6, E.outBack)) * -60 });
      let k = 0; scenes.forEach((s, i) => { if (t >= sStart(i)) k = i; });
      const prev = scenes[Math.max(0, k - 1)].count, cur = scenes[k].count;
      const q = k === 0 ? 1 : p(t, sStart(k) + 0.35, 0.5, E.inOutCubic);
      n0.textContent = prev; n1.textContent = cur;
      n0.style.transform = `translateY(${(-q * 100).toFixed(1)}%)`; n0.style.opacity = (1 - q).toFixed(2);
      n1.style.transform = `translateY(${((1 - q) * 100).toFixed(1)}%)`; n1.style.opacity = q.toFixed(2);
      cd.classList.toggle('today', k === scenes.length - 1);
    });
  }

  // ---------- product info card ----------
  const pc = el('div', 'pcard', `
    <img src="../assets/gen/box_front.png">
    <div class="pct"><div class="pcn">سيميدونا فورت</div><div class="pcs">${C.card.sub}</div>
      <div class="pcc">${C.card.chips.map(c => `<span>${c[0]}</span>`).join('')}</div></div>`, stage);
  const pchips = Array.from(pc.querySelectorAll('.pcc span'));
  on(t => {
    const a = ls(C.card.from) - 0.1, b = sEnd(C.card.scene) - 0.3;
    S(pc, { o: env(t, a, b, 0.35, 0.3), y: (1 - p(t, a, 0.6, E.outBack)) * 120 });
    pchips.forEach((c, k) => { const [li, wi] = C.card.chips[k][1]; const at = wordT(li, wi) - 0.15; S(c, { o: p(t, at, 0.3), s: 0.6 + 0.4 * p(t, at, 0.45, E.outBack) }); });
  });

  // ---------- daily calendar card (optional) ----------
  if (C.calendar) {
    const cal = el('div', 'cal', `<div class="calh">حبّة × ١ يومياً</div><div class="calg">${Array.from({ length: 28 }, () => '<i></i>').join('')}</div>`, stage);
    const cells = Array.from(cal.querySelectorAll('.calg i'));
    on(t => {
      const a = ls(C.calendar.from) - 0.1, b = sEnd(C.calendar.scene) - 0.3;
      S(cal, { o: env(t, a, b, 0.35, 0.3), x: (1 - p(t, a, 0.6, E.outBack)) * -300 });
      const n = 28 * p(t, a + 0.3, b - a - 0.6, E.lin);
      cells.forEach((c, k) => c.classList.toggle('on', k < n));
    });
  }

  // ---------- end card ----------
  const end = el('div', 'end', `
    <div class="script etitle">${C.end.title}</div>
    <img class="ebox" src="../assets/gen/box_angle.png">
    <div class="eat">تلقينه في</div>
    <div class="ebtn">هيلث ستور</div>
    <div class="eurl">healthstore.sa</div>
    <div class="edisc">قصة تمثيلية · مستحضر عشبي · لا يُستخدم أثناء الحمل أو الرضاعة أو مع أمراض الكبد · استشيري طبيبك إذا كنتِ تستخدمين علاجاً هرمونياً</div>`, stage);
  const [et, eb, ea, ebtn, eu, ed] = Array.from(end.children);
  on(t => {
    const a = ls(C.end.from) - C.end.lead;
    const v = t >= a ? p(t, a, 0.7) : 0;
    S(end, { o: v });
    et.style.clipPath = `inset(0 0 0 ${(100 - 100 * p(t, a + 0.3, 1.2, E.inOutCubic)).toFixed(1)}%)`;
    S(eb, { o: p(t, a + 0.9, 0.5), y: (1 - p(t, a + 0.9, 0.8, E.outBack)) * 80 + Math.sin(t * 1.4) * 8, r: -3 + Math.sin(t) * 1.5 });
    S(ea, { o: p(t, ls(C.end.from) - 0.1, 0.4) });
    S(ebtn, { o: p(t, ls(C.end.from) + 0.1, 0.3), s: (0.7 + 0.3 * p(t, ls(C.end.from) + 0.1, 0.6, E.outBack)) * (1 + 0.025 * Math.sin(t * 5)) });
    S(eu, { o: p(t, ls(C.end.from) + 0.4, 0.4) });
    S(ed, { o: p(t, ls(C.end.from) + 0.6, 0.5) });
  });

  captions(stage, { mode: 'reveal', from: C.capFrom, to: C.capTo, cls: 'storycap' });
})();
