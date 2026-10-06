// Motor de referencia de animación — Formato Línea Oficial.
// ?static → estado final (portada/thumbnail) · ?guias → zonas seguras · ?ms=2500 → congela en ese ms
(function () {
  const q = new URLSearchParams(location.search);
  const mv = q.get('ms'), STATIC = q.has('static'), FREEZE = mv !== null && /^\d+$/.test(mv) ? +mv : null;
  const EIN = 'cubic-bezier(0.2,0,0,1)', EOUT = 'cubic-bezier(0.4,0,1,1)';
  const FX = {
    'wipe-l': [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    'wipe-r': [{ clipPath: 'inset(0 0 0 100%)' }, { clipPath: 'inset(0 0 0 0)' }],
    'wipe-t': [{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    'wipe-b': [{ clipPath: 'inset(100% 0 0 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    'up': [{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'none' }],
    'left': [{ opacity: 0, transform: 'translateX(-48px)' }, { opacity: 1, transform: 'none' }],
    'fade': [{ opacity: 0 }, { opacity: 1 }],
    'grow-y': [{ transform: 'scaleY(0)' }, { transform: 'scaleY(1)' }],
    'push': [{ transform: 'scale(1)' }, { transform: 'scale(1.04)' }]
  };
  const stage = document.querySelector('.stage');
  const LOOP = +document.body.dataset.loop || 9000;

  function fit() {
    const k = Math.min(innerWidth / 1080, innerHeight / 1920);
    stage.style.transform = `translate(-50%,-50%) scale(${k})`;
  }

  function buildSubs() {
    document.querySelectorAll('[data-subs]').forEach(host => {
      const cues = JSON.parse(host.querySelector('script').textContent);
      cues.forEach(c => {
        const p = document.createElement('p'); p.className = 'cue';
        let inner = p;
        if (host.dataset.wrap === 'box') { inner = document.createElement('span'); inner.className = 'box'; p.appendChild(inner); }
        const words = c.text.split(/\s+/); let hl = false;
        words.forEach((w, i) => {
          if (w.startsWith('*')) { hl = true; w = w.slice(1); }
          let end = false;
          if (/\*[.,!?;:]?$/.test(w)) { end = true; w = w.replace('*', ''); }
          const s = document.createElement('span'); s.className = 'w' + (hl ? ' hl' : ''); s.textContent = w;
          inner.appendChild(s);
          if (i < words.length - 1) inner.appendChild(document.createTextNode(' '));
          if (end) hl = false;
        });
        p.dataset.t = c.t; p.dataset.d = c.d; host.appendChild(p);
      });
    });
  }

  function guides() {
    const add = (css, label) => { const g = document.createElement('div'); g.className = 'guia'; g.style.cssText += css; g.textContent = label || ''; stage.appendChild(g); };
    if (document.body.dataset.guia === 'tapa') {
      add('left:0;top:240px;width:1080px;height:1440px;background:none;border-top:2px dashed #00C8FF;border-bottom:2px dashed #00C8FF;align-items:flex-start;padding-top:12px', 'Recorte 3:4 del perfil');
    } else {
      add('left:0;top:0;width:1080px;height:150px;border-bottom:2px dashed #00C8FF');
      add('right:0;top:720px;width:140px;height:820px;border-left:2px dashed #00C8FF');
      add('left:0;bottom:0;width:1080px;height:380px;border-top:2px dashed #00C8FF', 'Zona de interfaz TikTok');
    }
  }

  let timer;
  function run() {
    clearTimeout(timer);
    const t0 = performance.now();
    document.getAnimations().forEach(a => a.cancel());
    document.querySelectorAll('[data-fx]').forEach(el => {
      const fx = FX[el.dataset.fx], d = +el.dataset.dur || 400, i = +el.dataset.in || 0;
      el.animate(fx, { duration: d, delay: i, easing: el.dataset.ease || EIN, fill: 'both' });
      if (el.dataset.out) el.animate([...fx].reverse(), { duration: 300, delay: +el.dataset.out, easing: EOUT, fill: 'forwards' });
    });
    document.querySelectorAll('.cue').forEach(p => {
      const t = +p.dataset.t, d = +p.dataset.d, ws = p.querySelectorAll('.w');
      p.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 60, delay: t, fill: 'both' });
      p.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 60, delay: t + d - 60, fill: 'forwards' });
      ws.forEach((w, i) => w.animate(
        [{ opacity: 0, transform: 'translateY(0.15em)' }, { opacity: 1, transform: 'none' }],
        { duration: 140, delay: t + i * (d * 0.55 / ws.length), easing: EIN, fill: 'both' }));
    });
    document.querySelectorAll('[data-count]').forEach(el => {
      const to = +el.dataset.count, i = +el.dataset.countIn || 0, d = +el.dataset.countDur || 900, pre = el.dataset.prefix || '';
      const val = ms => { let k = Math.min(1, Math.max(0, (ms - i) / d)); k = 1 - Math.pow(1 - k, 3); return pre + Math.round(to * k); };
      if (FREEZE !== null) { el.textContent = val(FREEZE); return; }
      const tick = now => { el.textContent = val(now - t0); if (now - t0 < i + d) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
    });
    if (FREEZE !== null) { document.getAnimations().forEach(a => { a.currentTime = FREEZE; a.pause(); }); return; }
    timer = setTimeout(run, LOOP);
  }

  buildSubs(); fit(); addEventListener('resize', fit);
  if (q.has('guias')) guides();
  if (STATIC) {
    document.querySelectorAll('[data-subs]').forEach(h => h.querySelectorAll('.cue').forEach((c, i) => { if (i) c.style.display = 'none'; }));
    document.querySelectorAll('.outro').forEach(o => o.style.display = 'none');
    return;
  }
  run();
  stage.addEventListener('click', run);
})();
