#!/usr/bin/env python3
"""Build the 'Hire Your First AI Agent' deck.

Every slide is written below as (file, label, section, theme, body-attrs, css, html, notes).
Run:  python3 build.py   → writes slides/*.html and index.html (the deck shell with speaker notes).
Then: python3 make_thumbs.py   → refreshes the overview pictures in thumbs/ (needs Python Playwright).
Content source: ../seminar-syllabus.md ("On the slide" = what is on screen, "Say" = speaker notes).
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SHELL_SRC = os.path.expanduser('~/.claude/skills/huashu-design/assets/deck_index.html')
A = '../assets/'

# ---------- small line icons (stroke = currentColor) ----------
def ic(path, size=40, sw=2):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="%s" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>') % (size, size, sw, path)
PEN = '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>'
CHECK = '<path d="M4 12.5l5 5L20 6.5"/>'
KEY = '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3M14 9l2 2"/>'
SNOW = '<path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9 4l3 2 3-2M9 20l3-2 3 2"/>'
TANGLE = '<path d="M3 12c3-6 6 6 9 0s6 6 9 0"/><path d="M3 7c4 4 7-4 10 1M11 16c3 4 6-3 10 1"/>'
EYE = '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'
HAND = '<path d="M8 13V5.5a1.5 1.5 0 013 0V12M11 11V4a1.5 1.5 0 013 0v7M14 11V5.5a1.5 1.5 0 013 0V14c0 4-3 7-7 7-3 0-4.6-1.6-6-4l-2-4a1.5 1.5 0 012.6-1.5L8 15"/>'
DESK = '<path d="M3 9h18M5 9v11M19 9v11M5 14h14"/><rect x="8" y="4" width="8" height="5" rx="1"/>'
NOTE = '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>'
CAB = '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 6h4M10 12h4M10 18h4"/>'
LOCK = '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 018 0v4"/>'
COIN = '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.6-1-1.7-1.5-3-1.5-1.7 0-3 .9-3 2s1 1.7 3 2 3 .9 3 2-1.3 2-3 2c-1.3 0-2.4-.5-3-1.5M12 6v2M12 16v2"/>'
CHAT = '<path d="M4 5h16v11H9l-5 4V5z"/>'
LIST = '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>'
POWER = '<path d="M12 3v9"/><path d="M6.3 7a8 8 0 1011.4 0"/>'
STAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c.6 6.4 5.6 11.4 12 12-6.4.6-11.4 5.6-12 12-.6-6.4-5.6-11.4-12-12C6.4 11.4 11.4 6.4 12 0z"/></svg>'

def ws(box, text, d='1.6s'):
    return '<div class="ws r" style="--d:%s">%s<b>BOX %s</b>%s</div>' % (d, ic(PEN, 30), box, text)

def qr(label, sub, d='.2s'):
    return ('<div class="qr glass pop" style="--d:%s"><div class="frame"></div><div class="scan"></div>'
            '<div class="ql"><b>%s</b>%s</div></div>') % (d, label, sub)

def page(title, section, theme, attrs, css, html):
    cls = theme
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>%s</title>\n'
            '<link rel="stylesheet" href="../shared/deck.css">\n<style>\n%s\n</style>\n</head>\n'
            '<body class="%s" data-section="%s" %s>\n<main class="slide">\n%s\n</main>\n'
            '<script src="../shared/deck.js"></script>\n</body>\n</html>\n') % (title, css.strip(), cls, section, attrs, html.strip())

S = []  # slides
def slide(file, label, section, theme, attrs, css, html, notes):
    S.append(dict(file=file, label=label, section=section, theme=theme, attrs=attrs, css=css, html=html, notes=notes))

SEC = ['Opening', 'The problem', 'What is AI?', 'SuDu AI and live demo', 'Break', 'Workshop', 'How to start', 'Questions', 'Spare']

# ---- minimal kit for the "What is an AI Agent?" chapter: big type, 1 idea per slide, soft motion ----
MIN_CSS = '''
body.light { background: #FAFAF7; } body.light .bg { display: none; }
body.dark { background: #03201C; } body.dark .bg .spark { display: none; }
.slide { padding-top: 92px; }
.mk { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: var(--green); }
body.dark .mk { color: var(--neon); }
.mt { font-size: 78px; font-weight: 750; letter-spacing: -.035em; line-height: 1.04; margin-top: 16px; max-width: 1560px; text-wrap: balance; }
.mt em { font-style: normal; color: var(--green); } body.dark .mt em { color: var(--neon); }
.ml { font-size: 34px; line-height: 1.42; color: var(--ink-2); margin-top: 22px; max-width: 1320px; text-wrap: pretty; }
body.dark .ml { color: var(--on-dark-2); }
.ml b { color: var(--ink); font-weight: 650; } body.dark .ml b { color: var(--on-dark); }
.m3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 60px; margin-top: auto; margin-bottom: 64px; }
.m3 > div { border-top: 3px solid var(--ink); padding-top: 22px; }
body.dark .m3 > div { border-color: var(--neon); }
.m3 b { display: block; font-size: 38px; font-weight: 750; letter-spacing: -.02em; line-height: 1.15; }
.m3 p { font-size: 27px; line-height: 1.42; color: var(--ink-2); margin-top: 10px; }
body.dark .m3 p { color: var(--on-dark-2); }
.mn { font-size: 180px; font-weight: 800; letter-spacing: -.05em; line-height: .9; }
.mn small { font-size: .32em; letter-spacing: -.02em; color: var(--green); } body.dark .mn small { color: var(--neon); }
.mq { display: inline-block; font-size: 32px; font-weight: 600; padding: 18px 28px; border-radius: 6px 26px 26px 26px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 24px 40px -30px rgba(2,34,31,.45); }
.mnote { font-size: 23px; color: var(--ink-3); } body.dark .mnote { color: var(--on-dark-3); }
/* motion: soft rise, staggered with --d */
.u { opacity: 0; transform: translateY(26px); animation: mUp .95s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--d, 0s); }
.uf { opacity: 0; animation: mFade 1.1s ease forwards; animation-delay: var(--d, 0s); }
.ux { opacity: 0; transform: translateX(-30px); animation: mUp .95s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--d, 0s); }
.ug { transform-origin: left; transform: scaleX(0); animation: mGrow 1.4s cubic-bezier(.65,0,.25,1) forwards; animation-delay: var(--d, 0s); }
@keyframes mUp { to { opacity: 1; transform: none; } }
@keyframes mFade { to { opacity: 1; } }
@keyframes mGrow { to { transform: none; } }
html.static .u, html.static .uf, html.static .ux { opacity: 1; transform: none; animation: none; }
html.static .ug { transform: none; animation: none; }
'''

# ============================================================ 1 · OPENING
slide('01-cover', 'Cover', SEC[0], 'dark bare', 'data-sparks="6,1 9,2 8,5 5,4" style="--gx:72%;--gy:46%;--mx:72%;--my:50%"', '''
.wrap { display:grid; grid-template-columns: 1fr 760px; align-items:center; height:100%; }
.display { font-size: 150px; margin: 26px 0 40px; }
.lead { max-width: 900px; }
.partner { position:absolute; left:128px; bottom:64px; display:flex; align-items:center; gap:28px; color: var(--on-dark-3); font-size: 24px; }
.partner img { height: 40px; } .partner img.sql { height: 30px; }
.hero { position:relative; width:760px; height:760px; display:grid; place-items:center; }
.hero svg.orbit { position:absolute; inset:0; }
.hero .av { width: 500px; height: 500px; position:relative; }
.ring { transform-origin: 380px 380px; animation: spin 60s linear infinite; }
.ring.b { animation-duration: 90s; animation-direction: reverse; }
@keyframes spin { to { transform: rotate(360deg); } }
''', '''
<div class="wrap">
  <div>
    <div class="kicker r" style="--d:.2s;font-size:26px">SQL seminar for all partners and clients</div>
    <h1 class="display r" style="--d:.35s">Hire Your First <span class="sig" style="--sd:1.3s">AI Agent</span></h1>
    <p class="lead r" style="--d:.6s">What AI needs, what it does, and where your company should start.</p>
  </div>
  <div class="hero">
    <svg class="orbit" viewBox="0 0 760 760" fill="none">
      <g class="ring"><circle cx="380" cy="380" r="340" stroke="rgba(242,251,247,.14)" stroke-dasharray="2 10"/><circle cx="380" cy="40" r="7" fill="#00F5A9"/></g>
      <g class="ring b"><circle cx="380" cy="380" r="290" stroke="rgba(0,245,169,.22)"/><circle cx="670" cy="380" r="5" fill="#00F5A9" opacity=".7"/></g>
    </svg>
    <img class="av pop" style="--d:.5s" src="../assets/av/agent-hi.svg" alt="The SuDu agent waving">
  </div>
</div>
<div class="partner f" style="--d:1.1s"><img src="../assets/logo-white.png" alt="SuDu AI"><span>×</span><img class="sql" src="../assets/sql-h-white.png" alt="SQL Account"><span class="pill">Official Partner</span></div>
''', "Nothing. The MC welcomes the room and hands over in one sentence. Straight to slide 2.")

# ---- SuDu intro: vision, map, road to autorun (spliced into build.py) ----
def words(text, d0, step, cls=''):
    out = []
    for i, w in enumerate(text.split(' ')):
        out.append('<span class="w"><i class="%s" style="--d:%.2fs">%s</i></span>' % (cls, d0 + i * step, w))
    return ' '.join(out)

VISION_H = ('<span class="w"><i class="" style="--d:0.30s">To build an AI that</i></span><br>'
            '<span class="w"><i class="n" style="--d:0.55s">runs a company</i></span><span class="w"><i class="" style="--d:0.75s">on its own</i></span>')

GLOBE_JS = r'''
<script>
(function () {
  const STATIC = navigator.webdriver || location.hash === '#static' || document.documentElement.classList.contains('static');
  const t0 = performance.now();

  /* ---------------- the globe: the business running on its surface ---------------- */
  const cv = document.getElementById('globe'), ctx = cv.getContext('2d');
  const W = 900, H = 820, DPR = 2;
  cv.width = W * DPR; cv.height = H * DPR; ctx.scale(DPR, DPR);
  const cx = 450, cy = 405, R = 270, TILT = -0.32, FOV = 1100;
  const rad = d => d * Math.PI / 180;
  const sph = (lat, lon) => [Math.cos(rad(lat)) * Math.sin(rad(lon)), -Math.sin(rad(lat)), Math.cos(rad(lat)) * Math.cos(rad(lon))];
  const P = [], N = 1100, ga = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < N; i++) { const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), t = ga * i; P.push([Math.cos(t) * r, y, Math.sin(t) * r]); }
  // main cycle (big nodes) plus the jobs around it (smaller nodes)
  const MAIN = [['ORDER', 18, 0], ['BUY', -14, 46], ['RECEIVE', 30, 92], ['STORE', -26, 138], ['MAKE', 14, 184], ['SHIP', -32, 228], ['BILL', 26, 272], ['COLLECT', -8, 318]];
  const MORE = [['QUOTE', 46, 338], ['CREDIT CHECK', 50, 22], ['APPROVE', -12, 18], ['PAY SUPPLIER', -52, 52], ['REORDER', 22, 56],
    ['QC CHECK', 58, 100], ['PUT AWAY', -2, 112], ['COUNT', -56, 120], ['PICK', 4, 158], ['PLAN', 48, 170], ['ISSUE', -54, 182],
    ['PACK', -8, 206], ['ROBOTS', 44, 220], ['DELIVER', -56, 250], ['REPORT', 54, 270], ['BOOKS', -40, 290], ['REMIND', 16, 342]];
  const EXTRA = ['PRICE LIST','PROMOTION','REPEAT ORDER','WHATSAPP ORDER','SALES ORDER','DELIVERY ORDER','PROOF OF DELIVERY','RETURN','CREDIT NOTE',
    'E-INVOICE','RECEIPT','BANK SLIP','STATEMENT','AGEING','CASH FLOW','PAYMENT VOUCHER','SUPPLIER INVOICE','PURCHASE REQUEST','PURCHASE ORDER','GRN',
    'SCAN','LABEL','BIN','BATCH','EXPIRY','FIFO','TRANSFER','CYCLE COUNT','STOCK ALERT','LOAD TRUCK','ROUTE','DISPATCH',
    'FORECAST','MRP','BOM','WORK ORDER','MACHINE','OEE','SCRAP','COSTING','RAW MATERIAL','FINISHED GOODS',
    'DASHBOARD','AUDIT TRAIL','APPROVAL RULE','AMR','ROBOT ARM','DRONE COUNT'];
  const NODES = MAIN.map(([n, la, lo]) => ({ n, v: sph(la, lo), main: true })).concat(MORE.map(([n, la, lo]) => ({ n, v: sph(la, lo), main: false })));
  {
    const ang = (p, q) => Math.acos(Math.min(1, p[0]*q[0] + p[1]*q[1] + p[2]*q[2]));
    const M = 110, cand = [];
    for (let i = 0; i < M; i++) {
      const y = 1 - ((i + 0.5) / M) * 2, r = Math.sqrt(1 - y * y), th = ga * i + 0.9, v = [Math.cos(th) * r, y, Math.sin(th) * r];
      if (Math.abs(y) > 0.94) continue;
      if (NODES.some(o => ang(o.v, v) < (o.main ? 0.2 : 0.16))) continue;
      cand.push(v);
    }
    EXTRA.forEach((n, k) => NODES.push({ n, v: cand[Math.floor(k * cand.length / EXTRA.length)], main: false, small: true }));
  }
  const byName = Object.fromEntries(NODES.map(o => [o.n, o]));
  // links: the main cycle, plus every node tied to its two nearest neighbours
  const key = (a, b) => [a, b].sort().join('|'), seen = new Set(), LINKS = [];
  const add = (a, b, main) => { const k = key(a, b); if (a === b || seen.has(k)) return; seen.add(k); LINKS.push({ a: byName[a].v, b: byName[b].v, main, ph: (LINKS.length * 0.37) % 1, sp: main ? 0.55 : 0.32 + (LINKS.length % 5) * 0.06 }); };
  MAIN.forEach((m, i) => add(m[0], MAIN[(i + 1) % MAIN.length][0], true));
  NODES.forEach(o => {
    NODES.filter(q => q !== o).map(q => ({ q, d: Math.acos(Math.min(1, o.v[0]*q.v[0] + o.v[1]*q.v[1] + o.v[2]*q.v[2])) }))
      .sort((x, y) => x.d - y.d).slice(0, 2).forEach(({ q }) => add(o.n, q.n, false));
  });
  const slerp = (a, b, t) => { const d = Math.acos(Math.min(1, a[0]*b[0]+a[1]*b[1]+a[2]*b[2])), s = Math.sin(d) || 1e-6;
    const k1 = Math.sin((1 - t) * d) / s, k2 = Math.sin(t * d) / s; return [a[0]*k1+b[0]*k2, a[1]*k1+b[1]*k2, a[2]*k1+b[2]*k2]; };
  function proj(v, rot, scale, lift) {
    let [x, y, z] = v; const c = Math.cos(rot), s = Math.sin(rot);
    [x, z] = [x * c + z * s, -x * s + z * c];
    const ct = Math.cos(TILT), st = Math.sin(TILT); [y, z] = [y * ct - z * st, y * st + z * ct];
    const r = R * scale, k = FOV / (FOV - z * r);
    return { x: cx + x * r * k, y: cy + lift + y * r * k, z, k };
  }
  const arcPt = (a, b, u, hgt, rot, scale, lift) => { const v = slerp(a, b, u), h = 1 + hgt * Math.sin(Math.PI * u); return proj([v[0]*h, v[1]*h, v[2]*h], rot, scale, lift); };
  function drawGlobe(t) {
    const intro = STATIC ? 1 : Math.min(1, Math.max(0, (t - 0.7) / 2.2)), e = 1 - Math.pow(1 - intro, 3);
    const scale = 0.7 + 0.3 * e, lift = (1 - e) * 160, rot = t * 0.16 + 0.4;
    ctx.clearRect(0, 0, W, H); ctx.globalAlpha = e;
    let g = ctx.createRadialGradient(cx, cy + lift, 0, cx, cy + lift, R * scale * 1.25);
    g.addColorStop(0, 'rgba(0,245,169,.22)'); g.addColorStop(.62, 'rgba(0,165,122,.10)'); g.addColorStop(1, 'rgba(0,245,169,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy + lift, R * scale * 1.25, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(0,245,169,.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(cx, cy + lift, R * scale * 1.003, 0, 7); ctx.stroke();
    [[1.22, 0.3, 0.5, 0], [1.36, 0.2, -0.35, 2.1]].forEach(([m, flat, ang, ph], i) => {
      const rx = R * scale * m, ry = rx * flat;
      ctx.save(); ctx.translate(cx, cy + lift); ctx.rotate(ang);
      ctx.strokeStyle = 'rgba(242,251,247,.16)'; ctx.setLineDash([3, 9]); ctx.beginPath(); ctx.ellipse(0, 0, rx, ry, 0, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      const a = t * (0.5 - i * 0.18) + ph; ctx.fillStyle = '#00F5A9';
      ctx.beginPath(); ctx.arc(Math.cos(a) * rx, Math.sin(a) * ry, 5 - i, 0, 7); ctx.fill(); ctx.restore();
    });
    for (const v of P) {
      const p = proj(v, rot, scale, lift), f = (p.z + 1) / 2;
      ctx.fillStyle = 'rgba(0,245,169,' + (0.05 + 0.4 * f * f).toFixed(3) + ')';
      ctx.beginPath(); ctx.arc(p.x, p.y, (0.6 + 1.2 * f) * p.k, 0, 7); ctx.fill();
    }
    // arcs: main cycle bright and high, the rest finer and lower
    LINKS.forEach(L => {
      const hgt = L.main ? 0.08 : 0.04, steps = L.main ? 22 : 10; let prev = null;
      ctx.lineWidth = L.main ? 2.2 : 1.5;
      for (let s = 0; s <= steps; s++) {
        const p = arcPt(L.a, L.b, s / steps, hgt, rot, scale, lift);
        if (prev) { const f = Math.max(0, (p.z + 1) / 2) ** 2;
          ctx.strokeStyle = 'rgba(0,245,169,' + ((L.main ? 0.08 : 0.07) + (L.main ? 0.5 : 0.48) * f).toFixed(3) + ')';
          ctx.beginPath(); ctx.moveTo(prev.x, prev.y); ctx.lineTo(p.x, p.y); ctx.stroke(); }
        prev = p;
      }
      const p = arcPt(L.a, L.b, (t * L.sp + L.ph) % 1, hgt, rot, scale, lift);
      if (p.z > -0.2) { ctx.fillStyle = L.main ? '#F2FBF7' : 'rgba(242,251,247,.8)'; ctx.beginPath(); ctx.arc(p.x, p.y, (L.main ? 4.5 : 3) * p.k, 0, 7); ctx.fill(); }
    });
    // nodes, then labels (front side only, no overlapping labels)
    const boxes = [], hit = (x, y, w, h) => boxes.some(q => x < q.x + q.w && x + w > q.x && y < q.y + q.h && y + h > q.y);
    const shown = NODES.map(o => ({ o, p: proj(o.v, rot, scale, lift) })).filter(({ p }) => p.z > -0.15)
      .sort((a, b) => (b.o.main - a.o.main) || (b.p.z - a.p.z));
    shown.forEach(({ o, p }) => {
      const f = Math.max(0, p.z), r0 = o.main ? 7 : o.small ? 4 : 4.8;
      if (!o.main) { ctx.fillStyle = 'rgba(0,245,169,' + (0.12 + 0.18 * f).toFixed(2) + ')'; ctx.beginPath(); ctx.arc(p.x, p.y, r0 * 2.2 * p.k, 0, 7); ctx.fill(); }
      ctx.fillStyle = o.main ? '#00F5A9' : 'rgba(0,245,169,' + (0.6 + 0.4 * f).toFixed(2) + ')';
      ctx.beginPath(); ctx.arc(p.x, p.y, r0 * p.k, 0, 7); ctx.fill();
      if (o.main) {
        ctx.strokeStyle = 'rgba(0,245,169,' + (0.5 * f).toFixed(2) + ')'; ctx.lineWidth = 1.5;
        const ring = 12 + 6 * ((t * 1.2 + o.v[0] + 2) % 1); ctx.beginPath(); ctx.arc(p.x, p.y, ring * p.k, 0, 7); ctx.stroke();
      }
      if (!(o.main || f > (o.small ? 0.62 : 0.4))) return;
      ctx.font = o.main ? '600 19px "JetBrains Mono", Menlo, monospace' : '500 16px "JetBrains Mono", Menlo, monospace'; ctx.textBaseline = 'middle';
      const tw = ctx.measureText(o.n).width, gap = o.main ? 16 : 10, lx = p.x + gap + tw > 770 ? p.x - gap - tw : p.x + gap, ly = p.y - gap;
      if (!o.main && hit(lx - 4, ly - 11, tw + 8, 22)) return;
      boxes.push({ x: lx - 4, y: ly - 11, w: tw + 8, h: 22 });
      const th = o.small ? 0.62 : 0.4;
      ctx.fillStyle = o.main ? 'rgba(242,251,247,' + Math.min(1, 0.25 + f).toFixed(2) + ')' : 'rgba(169,196,186,' + Math.min(1, (f - th) * 3).toFixed(2) + ')';
      ctx.fillText(o.n, lx, ly);
    });
    ctx.globalAlpha = 1;
  }

  /* ---------------- the floor: perspective grid drawn on canvas (no CSS 3D) ---------------- */
  const fv = document.getElementById('floor'), fx = fv.getContext('2d');
  const FW = 1920, FH = 385; fv.width = FW * DPR; fv.height = FH * DPR; fx.scale(DPR, DPR);
  const F = 900, CAM = 0.684, GAP = 0.12, VX = 960;   // focal length, camera height, grid spacing, vanishing x
  function drawFloor(t) {
    const fin = STATIC ? 1 : Math.min(1, Math.max(0, (t - 0.6) / 2));
    fx.clearRect(0, 0, FW, FH); if (!fin) return;
    const off = (t * 0.06) % GAP;                      // the grid slides toward us
    for (let k = 0; k < 110; k++) {
      const Z = 1.55 + k * GAP - off; if (Z < 1.4) continue;
      const y = F * CAM / Z; if (y < 2) continue;
      const a = Math.min(1, (y / FH) * 1.7) * 0.8 * fin, sz = Math.max(1, 6.2 / Z);
      const stepX = Z > 7 ? GAP * 2 : GAP, maxX = (VX + 40) * Z / F;
      fx.fillStyle = 'rgba(0,245,169,' + a.toFixed(3) + ')';
      for (let X = -Math.floor(maxX / stepX) * stepX; X <= maxX; X += stepX) fx.fillRect(VX + F * X / Z - sz / 2, y - sz / 4, sz, sz / 2);
    }
    // lanes converging on the horizon
    fx.lineWidth = 1.5;
    for (let i = -10; i <= 10; i++) {
      const X = i * 0.96, xn = VX + F * X / 1.4;
      const grd = fx.createLinearGradient(0, FH, 0, 0);
      grd.addColorStop(0, 'rgba(0,245,169,' + (0.28 * fin).toFixed(2) + ')'); grd.addColorStop(1, 'rgba(0,245,169,0)');
      fx.strokeStyle = grd; fx.beginPath(); fx.moveTo(xn, F * CAM / 1.4); fx.lineTo(VX, 0); fx.stroke();
    }
    // light beams rushing toward the viewer
    [0, 0.5].forEach(ph => {
      const u = ((t / 3.6) + ph) % 1, Z = 14 / (1 + u * 9), y = F * CAM / Z, th = Math.max(2, 90 / Z);
      const grd = fx.createLinearGradient(0, y - th, 0, y + th);
      grd.addColorStop(0, 'rgba(0,245,169,0)'); grd.addColorStop(.5, 'rgba(0,245,169,' + (0.28 * fin * Math.min(1, u * 4)).toFixed(3) + ')'); grd.addColorStop(1, 'rgba(0,245,169,0)');
      fx.fillStyle = grd; fx.fillRect(0, y - th, FW, th * 2);
    });
  }

  function frame(now) {
    const t = STATIC ? 9 : (now - t0) / 1000;
    drawGlobe(t); drawFloor(t);
    if (!STATIC) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* ---------------- "runs a company." decodes from machine characters ---------------- */
  if (!STATIC) {
    const GL = '01<>/#*+=∆□◇';
    const els = [...document.querySelectorAll('.vh .n')], fins = els.map(el => el.textContent);
    els.forEach(el => { el.style.visibility = 'hidden'; });
    document.fonts.ready.then(() => els.forEach((el, k) => {
      const fin = fins[k];
      el.style.width = el.getBoundingClientRect().width + 'px';   // measured with the real font: no jitter while decoding
      el.style.whiteSpace = 'nowrap'; el.style.visibility = '';
      el.textContent = fin.replace(/\S/g, () => GL[Math.random() * GL.length | 0]);
      setTimeout(() => {
        const t1 = performance.now();
        (function tick(n) {
          const p = Math.min(1, (n - t1) / 900), keep = Math.floor(p * fin.length);
          el.textContent = fin.split('').map((c, i) => i < keep ? c : GL[Math.random() * GL.length | 0]).join('');
          if (p < 1) requestAnimationFrame(tick); else { el.textContent = fin; el.style.width = ''; }
        })(t1);
      }, 1300 + k * 160);
    }));
  }
})();
</script>
'''

slide('02-vision', 'Our vision', SEC[0], 'dark', 'data-sparks="none" style="--gx:78%;--gy:62%"', '''
.bg .tiles { display: none; }
.bg .glow { width: 1300px; height: 900px; opacity: .45; animation: none; }
.bg .glow.b { display: none; }
body { background: #010C0A; }
#globe { position:absolute; left: 1135px; top: 0; width: 900px; height: 820px; z-index: 0; pointer-events:none; }
#floor { position:absolute; left: 0; top: 695px; width: 1920px; height: 385px; z-index: 0; pointer-events:none; }
.horizon { position:absolute; left: 0; right: 0; top: 694px; height: 2px; z-index: 0; background: linear-gradient(90deg, transparent, rgba(0,245,169,.9) 25%, #F2FBF7 80%, rgba(0,245,169,.9) 90%, transparent); box-shadow: 0 0 40px 8px rgba(0,245,169,.35); transform: scaleX(0); animation: grow 1.6s var(--ease) .4s forwards; }
.dawn { position:absolute; left: 1135px; width: 900px; top: 560px; height: 280px; z-index: 0; background: radial-gradient(50% 50% at 50% 50%, rgba(0,245,169,.32), transparent 70%); opacity: 0; animation: fadein 2s ease 1.2s forwards; }
@keyframes grow { to { transform: scaleX(1); } }
@keyframes fadein { to { opacity: 1; } }
.slide { padding-top: 120px; }
.kicker { font-size: 24px; letter-spacing: .3em; color: var(--neon); display:flex; align-items:center; gap: 18px; }
.kicker::after { content:""; width: 120px; height: 2px; background: linear-gradient(90deg, var(--neon), transparent); }
.vh { position:relative; z-index: 1; font-size: 120px; line-height: 1.02; font-weight: 650; letter-spacing: -.048em; margin-top: 36px; }
.vh .w { display:inline-block; overflow:hidden; vertical-align: bottom; padding-bottom: .08em; margin-bottom: -.08em; }
.vh .w i { display:inline-block; font-style: normal; transform: translateY(108%); animation: up 1.1s var(--ease) forwards; animation-delay: var(--d); }
.vh .w i:not(.n) { background: linear-gradient(105deg, #F2FBF7 42%, #00F5A9 50%, #F2FBF7 58%) 100% 0 / 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: up 1.1s var(--ease) forwards, sheen 2.2s ease-in-out forwards; animation-delay: var(--d), 2.6s; }
@keyframes sheen { to { background-position: -50% 0; } }
.vh .w i.n { color: var(--neon); font-variant-ligatures: none; }
.vh .w + .w:lang(en) { display: table; }   /* English runs longer: 3rd line */
@keyframes up { to { transform: none; } }
.say { position:absolute; left: 128px; top: 744px; max-width: none; white-space: nowrap; font-size: 34px; line-height: 1.42; color: var(--on-dark-2); z-index: 1; }
.say b { color: var(--on-dark); font-weight: 650; }
''', '''
<canvas id="floor"></canvas><div class="dawn"></div><div class="horizon"></div>
<canvas id="globe"></canvas>
<div class="kicker f" style="--d:.1s">OUR VISION</div>
<h1 class="vh">%s</h1>
<p class="say r" style="--d:1.9s"><b>SuDu AI is the AI ERP built for this, to serve businesses</b><br>1 system runs every process. AI executes, analyses and reminds. People make the decisions.</p>
%s
''' % (VISION_H, GLOBE_JS),
"(Let the line land. Pause for two seconds before speaking.)\n\n\"Our vision at SuDu is to build an AI that runs a company on its own. Not a chatbot. Not a report. An AI that runs the operation. Look at the sphere: every point is a job in your company. Order, buy, receive, store, make, ship, bill, collect, and all the jobs around them: quote, credit check, pick, pack, count, plan, quality check, pay the supplier, report. Every one is connected, and the work keeps moving around it on its own.\n\nThat is why SuDu is the AI ERP built for this, to serve businesses: 1 system runs every process, AI executes, analyses and reminds, and people make the decisions. Most software adds AI on top: a chatbot sits beside the old system, and people still key in, click and chase. We built the system itself for AI, so it can read every order, every stock count and every payment, decide, and do the work, with people approving what matters. And the last step is physical: robots that move, pick and count, run by the same system.\n\nThat is where we are going. Let me show you what it looks like today.\"\n\nNext: the map.")

ROBOT_AMR = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="10" y="30" width="44" height="16" rx="4"/><circle cx="20" cy="50" r="4"/><circle cx="44" cy="50" r="4"/><rect x="18" y="14" width="28" height="16" rx="2"/><path d="M32 14v16"/></svg>'
ROBOT_ARM = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 56h26"/><path d="M18 56v-8h14v8"/><path d="M25 48L20 30l22-12"/><circle cx="20" cy="30" r="4"/><circle cx="42" cy="18" r="4"/><path d="M46 18l8-4M46 20l8 4"/></svg>'
ROBOT_DRONE = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="24" y="26" width="16" height="12" rx="3"/><path d="M24 28L12 18M40 28l12-10M24 36L12 46M40 36l12 10"/><path d="M4 18h16M44 18h16M4 46h16M44 46h16"/><path d="M32 38v8"/><circle cx="32" cy="49" r="3"/></svg>'
UFO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="13" rx="10" ry="4"/><path d="M7 11.5a5 5 0 0110 0"/><path d="M8 19l-1 2M16 19l1 2M12 17v4"/></svg>'

def pulse(d, dur, begin='0s', r=6, color='#00A57A', cls='cn'):
    return ('<path d="%s" class="%s"/><circle r="%d" fill="%s"><animateMotion dur="%s" begin="%s" repeatCount="indefinite" path="%s"/></circle>'
            % (d, cls, r, color, dur, begin, d))

WA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 20.5l1.3-4A8.5 8.5 0 1 1 8 19.6z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1.2-1.6-2-1-1 .8a5 5 0 0 1-2.4-2.4l.8-1-1-2z"/></svg>'
MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6l8.5 7 8.5-7"/></svg>'
BOX = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/></svg>'
PEOPLE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16.5 14.6c2.6.2 4.3 1.9 5 4.9"/></svg>'
HUMANOID = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="22" y="6" width="20" height="15" rx="5"/><path d="M27 13h.01M37 13h.01"/><path d="M32 2v4"/><rect x="20" y="24" width="24" height="20" rx="4"/><path d="M20 28l-8 10 4 6M44 28l8 10-4 6"/><path d="M26 44v16M38 44v16"/></svg>'
TRUCK = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="22" width="34" height="22" rx="2"/><path d="M38 30h12l8 9v5H38z"/><circle cx="16" cy="48" r="5"/><circle cx="48" cy="48" r="5"/><path d="M44 12a10 10 0 0 1 10 0M41 7a16 16 0 0 1 16 0"/><circle cx="49" cy="17" r="1.5" fill="currentColor"/></svg>'
TICK = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>'

OV_LINES = ''.join([
    pulse('M210 250 H222', '0.9s', '0s'), pulse('M210 450 H222', '0.9s', '.4s'),
    pulse('M318 250 H364', '1.1s', '.2s'), pulse('M318 450 H364', '1.1s', '.6s'),
    pulse('M494 128 V158', '1s', '0s', 5, '#00F5A9'), pulse('M832 128 V158', '1s', '.25s', 5, '#00F5A9'),
    pulse('M1170 128 V158', '1s', '.5s', 5, '#00F5A9'), pulse('M1508 128 V158', '1s', '.75s', 5, '#00F5A9'),
    pulse('M760 596 V522', '1.2s', '0s'), pulse('M1080 596 V522', '1.2s', '.4s'), pulse('M1220 596 V522', '1.2s', '.8s'),
])

IC_SELL = '<path d="M3 4h2.5l2.2 10.5h10.8L21 7H7"/><circle cx="9.5" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>'
IC_WH = '<path d="M3 9.5L12 4l9 5.5V20H3z"/><path d="M7 20v-6h10v6M7 17h10"/>'
IC_FAC = '<path d="M3 20V10l5 3V10l5 3V10l5 3V5h3v15z"/><path d="M7 17h2M12 17h2"/>'
IC_FIN = '<path d="M6 3h12v18l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21z"/><path d="M9 8h6M9 11.5h6M9 15h4"/>'
BW, BG = 256, 82          # block width and gap inside the ERP box
BX = [26 + i * (BW + BG) for i in range(4)]
def blk(i, cid, tag, icon, name, line, badge, d, extra=''):
    return ('<div class="glass blk r" id="n-' + cid + '" style="left:' + str(BX[i]) + 'px;--d:' + '%.2f' % d + 's">'
            '<div class="hd"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + icon + '</svg></span><b>' + tag + '</b></div>'
            '<h3>' + name + '</h3>' + extra + '<p>' + line + '</p><div class="badge">' + TICK + badge + '</div></div>')
OV_BLOCKS = ''.join([
    blk(0, 'scm', 'SCM', IC_SELL, 'Sell &amp; buy', 'Takes orders and buys stock.', 'Orders in 1 place', .6),
    blk(1, 'wms', 'WMS', IC_WH, 'Warehouse', 'Every carton scanned, in and out.', 'Stock accurate', .8),
    blk(2, 'mes', 'MES', IC_FAC, 'Factory', 'Every job planned and tracked.', 'Production<br>you can see', 1.0),
    blk(3, 'fin', 'FIN', IC_FIN, 'Finance', 'Invoices and payments recorded automatically.', 'Accounts up to date', 1.2,
        '<img class="sqll" src="../assets/sql-h.png" alt="SQL Account">'),
])
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
FLOWS = [('orders', 0), ('materials', 1), ('invoices', 2)]
OV_FLOW = ''.join('<div class="fl pop" style="left:' + str(BX[k] + BW + BG // 2) + 'px;--d:' + '%.2f' % (1.5 + k * .15) + 's"><i>' + ARROW + '</i><span>' + t + '</span></div>' for t, k in FLOWS)

slide('03-the-map', 'The SuDu map', SEC[0], 'light', 'data-sparks="none" style="--gx:62%;--gy:55%;--mx:60%;--my:55%"', '''
.slide { padding-top: 84px; }
.h1 { font-size: 66px; }
.map { position:relative; width: 1664px; height: 722px; margin-top: 26px; }
.map svg.lines { position:absolute; inset:0; width:100%; height:100%; overflow:visible; z-index: 3; pointer-events:none; }
.map .cn { stroke: rgba(2,34,31,.3); stroke-width: 3; stroke-dasharray: 2 8; stroke-linecap: round; fill:none; }
.side { position:absolute; left: 0; width: 210px; height: 150px; padding: 20px 20px; border-radius: 22px; }
.side svg { width: 40px; height: 40px; color: var(--green); }
.side b { display:block; font-size: 28px; font-weight: 650; margin-top: 8px; }
.side span { display:block; font-size: 22px; color: var(--ink-3); margin-top: 2px; }
.conn { position:absolute; left: 222px; top: 175px; width: 96px; height: 350px; border-radius: 48px; background: var(--ink); color: var(--on-dark); display:flex; flex-direction:column; align-items:center; justify-content:space-around; padding: 18px 0; }
.conn .c { display:flex; flex-direction:column; align-items:center; gap: 6px; border-radius: 16px; padding: 8px 4px; }
.conn svg { width: 44px; height: 44px; color: var(--neon); }
.conn span { font-family: var(--mono); font-size: 16px; font-weight: 600; letter-spacing: .02em; }
.conn-k { position:absolute; left: 222px; width: 96px; top: 140px; text-align:center; font-family: var(--mono); font-size: 16px; font-weight: 600; letter-spacing: .1em; color: var(--ink-3); }
.erp { position:absolute; left: 340px; top: 0; width: 1324px; height: 548px; border-radius: 34px; border: 2.5px solid var(--ink); background: rgba(255,255,255,.4); }
.erp .tab { position:absolute; left: 26px; top: 12px; font-family: var(--mono); font-size: 19px; letter-spacing: .1em; font-weight: 600; color: var(--ink); }
.ai { position:absolute; left: 26px; right: 26px; top: 48px; height: 80px; border-radius: 20px; background: var(--ink); color: var(--on-dark); display:flex; align-items:center; gap: 18px; padding: 0 24px; box-shadow: 0 0 50px rgba(0,245,169,.22); }
.ai > svg { width: 46px; height: 46px; color: var(--neon); flex:none; }
.ai .t { flex:none; } .ai .t b { font-size: 28px; font-weight: 650; } .ai .t span { font-size: 22px; color: var(--on-dark-2); margin-left: 10px; }
.ai .chips { margin-left: auto; display:flex; gap: 6px; }
.ai .chips i { white-space: nowrap; font-style: normal; font-size: 18px; font-weight: 600; padding: 7px 11px; border-radius: 999px; background: rgba(0,245,169,.12); color: var(--neon); }
.blk { position:absolute; top: 158px; width: 256px; height: 364px; padding: 22px 16px 18px 20px; border-radius: 24px; display:flex; flex-direction:column; }
.blk .hd { display:flex; align-items:center; justify-content:space-between; }
.blk .ico { width: 64px; height: 64px; border-radius: 18px; background: var(--ink); color: var(--neon); display:grid; place-items:center; }
.blk .ico svg { width: 36px; height: 36px; }
.blk .hd b { font-family: var(--mono); font-size: 18px; font-weight: 700; color: var(--green); background: var(--mint); padding: 4px 9px; border-radius: 7px; letter-spacing: .06em; }
.blk h3 { font-size: 36px; font-weight: 700; letter-spacing: -.02em; margin-top: 16px; }
.blk .sqll { height: 24px; margin-top: 6px; align-self: flex-start; }
.blk p { font-size: 25px; line-height: 1.32; color: var(--ink-2); margin-top: 8px; }
.badge { margin-top: auto; display:flex; align-items:center; gap: 6px; white-space: nowrap; letter-spacing: -.01em; font-size: 19px; font-weight: 700; color: var(--ink); background: var(--mint); border: 1.5px solid rgba(0,165,122,.35); padding: 9px 9px; border-radius: 12px; }
.badge svg { color: var(--green); flex:none; }
.blk .badge { line-height: 1.15; }
.fl { position:absolute; top: 340px; width: 0; z-index: 4; }
.fl i { position:absolute; left: -26px; top: -26px; width: 52px; height: 52px; border-radius: 50%; background: var(--neon); color: var(--ink); display:grid; place-items:center; box-shadow: 0 0 0 6px rgba(0,245,169,.2), 0 10px 24px -8px rgba(2,34,31,.4); }
.fl i svg { width: 28px; height: 28px; }
.fl span { position:absolute; left: -41px; width: 82px; top: 34px; text-align:center; font-size: 18px; line-height: 1.2; font-weight: 700; color: var(--green); }
#n-fin { background: linear-gradient(160deg, #F4EEFF, #EAF3FF); }
.phys { position:absolute; left: 340px; top: 582px; width: 1324px; height: 138px; border-radius: 28px; border: 2.5px dashed rgba(2,34,31,.35); display:flex; align-items:center; gap: 22px; padding: 0 24px; }
.phys .lbl b { display:block; font-size: 30px; font-weight: 700; }
.phys .lbl span { font-size: 22px; color: var(--ink-3); }
.robot { position:absolute; top: 14px; height: 106px; display:flex; align-items:center; gap: 16px; padding: 0 22px 0 16px; border-radius: 20px; }
.robot svg { width: 64px; height: 64px; color: var(--ink); flex:none; }
.robot b { display:block; font-size: 26px; font-weight: 700; }
.robot span { font-size: 22px; color: var(--ink-2); }
.phys .pill { position:absolute; right: 24px; background: var(--neon); color: var(--ink); }
.token { position:absolute; left: -15px; top: -15px; width: 30px; height: 30px; border-radius: 50%; z-index: 5; pointer-events:none; opacity: 0; transition: opacity .4s;
  background: radial-gradient(circle, #F2FBF7 0 28%, #00F5A9 30% 55%, rgba(0,245,169,0) 72%); box-shadow: 0 0 30px 10px rgba(0,245,169,.45); }
.token.on { opacity: 1; }
.cap { position:absolute; right: 26px; top: 8px; display:flex; align-items:center; gap: 12px; opacity: 0; }
.cap.in { animation: capin .5s var(--ease) forwards; }
@keyframes capin { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.cap b { font-family: var(--mono); font-size: 17px; letter-spacing: .1em; font-weight: 600; color: var(--ink); background: var(--neon); padding: 4px 9px; border-radius: 8px; }
.cap span { font-size: 23px; font-weight: 600; color: var(--ink); }
.side, .blk, .robot, .conn .c, .ai .chips i { transition: box-shadow .45s, transform .45s, background .45s, color .45s; }
.side.hot, .blk.hot, .robot.hot { box-shadow: 0 0 0 3px var(--neon), 0 0 40px rgba(0,245,169,.45), 0 30px 60px -30px rgba(2,34,31,.4); transform: translateY(-4px); }
.conn .c.hot { background: rgba(0,245,169,.22); }
.ai .chips i.hot { background: var(--neon); color: var(--ink); }
''', '''
<h1 class="h1 r" style="--d:.1s">1 AI ERP to run your company</h1>
<div class="map">
  <div class="glass side r" id="n-cust" style="top:175px;--d:.3s">%(people)s<b>Customers</b><span>order and pay</span></div>
  <div class="glass side r" id="n-sup" style="top:375px;--d:.4s">%(box)s<b>Suppliers</b><span>sell you stock</span></div>
  <div class="conn-k f" style="--d:.5s">CONNECT</div>
  <div class="conn r" style="--d:.5s"><div class="c" id="c-wa">%(wa)s<span>WhatsApp</span></div><div class="c" id="c-mail">%(mail)s<span>Email</span></div></div>
  <div class="erp f" style="--d:.2s">
    <div class="tab">SUDU ERP WITH AI</div><div class="cap" id="cap"><b id="cap-n"></b><span id="cap-t"></span></div>
    <div class="ai r" style="--d:1.4s">%(ufo)s<div class="t"><b>AI agents</b><span>read, decide and act</span></div>
      <div class="chips"><i id="a-sales">Sales</i><i id="a-purchase">Purchase</i><i id="a-inventory">Inventory</i><i id="a-collection">Collection</i><i>Payment</i><i>Up Sales</i><i id="a-finance">Finance</i></div></div>
    %(blocks)s
    %(flow)s
  </div>
  <div class="phys r" style="--d:1.8s"><div class="lbl"><b>Physical AI</b><span>robots run by<br>the same system</span></div>
    <div class="glass robot" id="r-truck" style="left:262px">%(truck)s<div><b>Auto-driving truck</b><span>delivers the goods</span></div></div>
    <div class="glass robot" id="r-hum" style="left:624px">%(hum)s<div><b>Humanoid robot</b><span>moves, picks and makes</span></div></div>
    <span class="pill">Next</span></div>
  <svg class="lines f" style="--d:1.2s" viewBox="0 0 1664 722" fill="none">%(lines)s</svg>
  <div class="token" id="token"></div>
</div>
<script>
(function () {
  if (navigator.webdriver || location.hash === '#static' || document.documentElement.classList.contains('static')) return;
  const STEPS = [
    [210, 250, 'A customer orders on WhatsApp', ['n-cust', 'c-wa', 'a-sales']],
    [494, 158, 'Sales takes the order and checks credit', ['n-scm', 'a-sales']],
    [210, 450, 'Missing stock is ordered from the supplier by email', ['n-sup', 'c-mail', 'a-purchase']],
    [832, 158, 'Warehouse scans every carton in: stock stays accurate', ['n-wms', 'a-inventory']],
    [1170, 158, 'Factory makes it, every step visible', ['n-mes', 'r-hum']],
    [760, 522, 'Warehouse packs it; the truck delivers it', ['n-wms', 'r-truck', 'a-inventory']],
    [1508, 158, 'Invoice and payment go into SQL Account', ['n-fin', 'a-collection', 'a-finance']],
  ];
  const tok = document.getElementById('token'), capN = document.getElementById('cap-n'), capT = document.getElementById('cap-t'), cap = document.getElementById('cap');
  const MOVE = 750, STAY = 1700, START = 3000;
  let i = -1, from = [STEPS[0][0], STEPS[0][1]];
  function go() {
    document.querySelectorAll('.hot').forEach(e => e.classList.remove('hot'));
    i = (i + 1) %% STEPS.length;
    const [x, y, txt, on] = STEPS[i], a = [...from], t0 = performance.now();
    cap.classList.remove('in'); void cap.offsetWidth;
    capN.textContent = 'STEP ' + (i + 1) + ' / ' + STEPS.length; capT.textContent = txt; cap.classList.add('in');
    tok.classList.add('on');
    (function mv(n) {
      const p = Math.min(1, (n - t0) / MOVE), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      tok.style.transform = 'translate(' + (a[0] + (x - a[0]) * e) + 'px,' + (a[1] + (y - a[1]) * e) + 'px)';
      if (p < 1) requestAnimationFrame(mv);
      else { on.forEach(id => document.getElementById(id).classList.add('hot')); from = [x, y]; setTimeout(go, STAY); }
    })(t0);
  }
  tok.style.transform = 'translate(' + from[0] + 'px,' + from[1] + 'px)';
  setTimeout(go, START);
})();
</script>
''' % dict(people=PEOPLE, box=BOX, wa=WA, mail=MAIL, ufo=UFO, blocks=OV_BLOCKS, flow=OV_FLOW, truck=TRUCK, hum=HUMANOID, lines=OV_LINES),
"\"First, the big picture, in plain words.\n\nThe big box is SuDu: one ERP, one system, one database. Inside it the work flows left to right. Supply chain: selling and buying, so orders are in one place. The warehouse, WMS: every carton is scanned, so stock is accurate. The factory, MES: every job is tracked, so you can see every job. And finance: everything goes into SQL Account, so your accounts are always up to date.\n\nOn the left, customers and suppliers reach the system the way they already work: WhatsApp and email. Across the top, the AI agents read everything and do the work at every step. At the bottom, the next step: physical AI, an auto-driving truck and a humanoid robot, run by the same system.\n\nWatch one order travel through it.\" (It loops by itself, about 17 seconds.)\n\nNote: physical AI is the roadmap, not on sale today.\nNext: \"Every company is walking the same road. Where is yours?\"")


def pulse(d, dur, begin='0s', r=6, color='#00A57A', cls='cn'):
    return ('<path d="%s" class="%s"/><circle r="%d" fill="%s"><animateMotion dur="%s" begin="%s" repeatCount="indefinite" path="%s"/></circle>'
            % (d, cls, r, color, dur, begin, d))

WA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 20.5l1.3-4A8.5 8.5 0 1 1 8 19.6z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1.2-1.6-2-1-1 .8a5 5 0 0 1-2.4-2.4l.8-1-1-2z"/></svg>'
MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6l8.5 7 8.5-7"/></svg>'
DOC = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/></svg>'
HUMANOID = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="22" y="6" width="20" height="15" rx="5"/><path d="M27 13h.01M37 13h.01"/><path d="M32 2v4"/><rect x="20" y="24" width="24" height="20" rx="4"/><path d="M20 28l-8 10 4 6M44 28l8 10-4 6"/><path d="M26 44v16M38 44v16"/></svg>'
TRUCK = '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="22" width="34" height="22" rx="2"/><path d="M38 30h12l8 9v5H38z"/><circle cx="16" cy="48" r="5"/><circle cx="48" cy="48" r="5"/><path d="M44 12a10 10 0 0 1 10 0M41 7a16 16 0 0 1 16 0"/><circle cx="49" cy="17" r="1.5" fill="currentColor"/></svg>'


STACK = [  # bottom to top: key, title, sub, chips on the plate
    ('sql', 'SQL Account', 'Layer 1 · Accounting', ['Invoices', 'Payments', 'Tax', 'Reports']),
    ('wms', 'WMS', 'Layer 2 · Warehouse', ['Receive', 'Put away', 'Pick', 'Ship', 'Count']),
    ('mes', 'MES', 'Layer 3 · Factory', ['Plan', 'Issue', 'Make', 'QC', 'Cost']),
    ('ai', 'AI agents', 'Layer 4 · Operates all 3', ['Sales', 'Purchase', 'Inventory', 'Collection', 'Finance']),
]
def _plates():
    out = ''
    for i, (k, t, sub, chips) in enumerate(STACK):
        z = i * 235
        ch = ''.join('<i>' + c + '</i>' for c in chips)
        nm = '<img src="../assets/sql-h.png" alt="SQL Account">' if k == 'sql' else '<b>' + t + '</b>'
        out += ('<div class="pl ' + k + '" style="--z:' + str(z) + 'px;--d:' + '%.2f' % (0.3 + i * 0.25) + 's">'
                '<div class="tx">' + nm + '<span>' + sub + '</span><div class="ch">' + ch + '</div></div></div>')
    for x, y in [(70, 50), (630, 50), (70, 350), (630, 350)]:
        out += '<span class="pil" style="left:' + str(x) + 'px;top:' + str(y) + 'px"></span>'
    return out

STACK_LEGEND = [('4', 'AI agents', 'operate everything below'), ('3', 'MES', 'production you can see'),
                ('2', 'WMS', 'stock accurate'), ('1', 'SQL Account', 'accounts right')]

# deep-dive boards, one per layer (step 1 = layer 1 ... step 4 = layer 4), page-7 style: big tilted board, cards with every document
DEEP = [
    ('1', 'sql', 'SQL Account', 'The foundation: accounting', 'Accounts right', 'Every SuDu document goes in here automatically.', [
        ('Customers', 'Money in', ['Sales Invoice', 'Credit Note', 'Customer Payment', 'Payment allocation']),
        ('Suppliers', 'Money out', ['Purchase Invoice', 'Supplier Payment', 'Payment Voucher']),
        ('Ledger and tax', 'Compliance', ['Journal entries', 'Tax and SST', 'e-Invoice (LHDN)', 'Stock value']),
        ('Reports', 'Owner view', ['Profit and Loss', 'Balance Sheet', 'Debtor ageing', 'Cash flow']),
    ]),
    ('2', 'wms', 'WMS', 'Warehouse, in real time', 'Stock accurate', 'Stock value and goods received flow down to SQL Account.', [
        ('Inbound', 'Goods come in', ['Goods Receiving', 'Receiving inspection', 'Putaway to bin', 'Return Receiving']),
        ('Inventory', 'Goods stored', ['Bins and locations', 'Batch and expiry', 'Stock Transfer', 'Stock Adjustment', 'Stock Count']),
        ('Outbound', 'Goods go out', ['Reservation', 'Picking', 'Packing (Handling Units)', 'Goods Delivery', 'Proof of delivery']),
        ('Rules', 'Kept automatically', ['Barcode and QR scan', 'FIFO / FEFO', 'Reorder level', 'Min / max stock']),
    ]),
    ('3', 'mes', 'MES', 'Factory, in real time', 'Production you can see', 'Finished goods flow back into WMS.', [
        ('Plan', 'Before the job', ['BOM', 'Production Order', 'Production schedule', 'Machine and line']),
        ('Make', 'During the job', ['Material Issue', 'Traveller / flow card', 'Output reporting', 'Machine time (OEE)']),
        ('Quality', 'Check every batch', ['QC check', 'Scrap and rework', 'Batch traceability']),
        ('Results', 'After the job', ['Production Receipt', 'Finished goods to stock', 'True cost per job']),
    ]),
    ('4', 'ai', 'AI agents', 'Operates all 3 layers', 'Runs the company', 'Nothing is saved until a person approves.', [
        ('Sales AI', 'Takes orders', ['Reads WhatsApp and email', 'Creates Sales Orders', 'Asks when unsure']),
        ('Purchase AI', 'Buys stock', ['Reorder suggestions', 'Drafts Purchase Orders', 'Sends to supplier']),
        ('Inventory AI', 'Watches stock', ['Low-stock alerts', 'Expiry warnings', 'Count reminders']),
        ('Collection AI', 'Gets paid', ['Sends statements', 'Polite reminders', 'Matches bank slips']),
        ('Payment AI', 'Pays suppliers', ['Prepares Payment Vouchers', 'You release the money']),
        ('Up Sales AI', 'Brings customers back', ['Spots lost customers', 'Repeat-order nudges']),
        ('Finance AI', 'Tracks the numbers', ['Debtor ageing', 'Daily sales report', 'Answers the boss']),
        ('You', 'Stay the boss', ['Approve what matters', 'Everything logged', 'Switch any agent off']),
    ]),
]
def _deep():
    out = ''
    for n, key, name, role, badge, flow, groups in DEEP:
        cols = 4
        cards = ''
        for gi, (g, sub, docs) in enumerate(groups):
            li = ''.join('<li>' + DOC + '<span>' + d + '</span></li>' for d in docs)
            cards += '<div class="dc' + (' you' if g == 'You' else '') + '"><div class="dh"><b>' + g + '</b><span>' + sub + '</span></div><ul>' + li + '</ul></div>'
        out += ('<div class="deep ' + key + '" data-s="' + n + '">'
                '<div class="dtop"><div><div class="lv">LAYER ' + n + ' OF 4</div><h2>' + name + ' <em>' + role + '</em></h2></div>'
                '<div class="dft"><span class="bd">' + TICK + badge + '</span><span class="fl">' + flow + '</span></div></div>'
                '<div class="dview"><div class="dtilt"><div class="dboard"><div class="dgrid g' + ('7' if len(groups) > 4 else '4') + '">' + cards + '</div></div></div></div></div>')
    return out

# ---- layer boards: 1 card per document, joined by its real relationship (sudu-erp-full-process-2026-10-05.md) ----
# canvas 1620 x 700. node: id -> (x, y, w, h, title, sub, cls). edge: (points, label, cls)
W, H = 200, 84
def N(x, y, t, s, cls='', w=W, h=H): return (x, y, w, h, t, s, cls)

FLOWS = {
  'sql': {
    'lanes': [(10, 10, 1600, 110, 'SET UP ONCE'), (10, 140, 1050, 250, 'MONEY IN'), (10, 410, 1050, 145, 'MONEY OUT'), (10, 570, 1050, 120, 'STOCK VALUE'), (1090, 140, 520, 550, 'INTO SQL ACCOUNT')],
    'nodes': {
      'sync': N(30, 28, 'Sync Agent', 'connects SQL Account', w=230, h=78), 'mast': N(300, 28, 'Customers &amp; suppliers', 'copied from SQL Account', w=250, h=78),
      'item': N(590, 28, 'Items &amp; UOM', 'codes, units, cost', w=230, h=78), 'open': N(860, 28, 'Opening stock', 'balance template', w=230, h=78),
      'perm': N(1130, 28, 'Users &amp; permissions', 'who can do what', w=250, h=78),
      'gd': N(30, 175, 'Goods Delivery', 'completed in WMS', 'ext'), 'so': N(30, 290, 'Sales Order', 'or direct invoice', 'ext'),
      'si': N(300, 232, 'Sales Invoice', 'complete, then send', 'hub'),
      'cp': N(570, 175, 'Customer Payment', 'from the customer', w=240), 'cn': N(570, 280, 'Credit Note', 'return or discount', w=240),
      'al': N(840, 175, 'Allocation', 'match to invoices', w=210),
      'gr': N(30, 445, 'Goods Receiving', 'from WMS', 'ext'), 'pi': N(300, 445, 'Purchase Invoice', 'from PO / GR', 'hub'),
      'sp': N(570, 445, 'Supplier Payment', 'paid in SQL Account'),
      'sa': N(30, 600, 'Stock Adjustment', 'completed in WMS', 'ext'),
      'pend': N(1140, 260, 'Waiting', 'queued for SQL Account', w=220), 'post': N(1140, 400, 'Saved', 'in SQL Account', 'hub', w=220),
      'ver': N(1140, 540, 'Check &amp; match', 'check every line', w=220),
      'book': N(1400, 300, 'SQL Account records', 'accounts &middot; who owes you &middot; tax &middot; reports', 'end', w=190, h=200),
      'note': N(1400, 560, 'Send GD <u>or</u> SI, GR <u>or</u> PI', 'never both: stock would count twice', 'note', w=200, h=110),
    },
    'edges': [
      ([(260, 67), (300, 67)], '', ''), ([(550, 67), (590, 67)], '', ''), ([(820, 67), (860, 67)], '', ''),
      ([(230, 217), (265, 217), (265, 274), (300, 274)], 'convert', ''), ([(230, 332), (265, 332), (265, 274)], '', ''),
      ([(500, 274), (535, 274), (535, 217), (570, 217)], 'paid', ''), ([(535, 274), (535, 322), (570, 322)], 'credit', ''),
      ([(810, 217), (840, 217)], '', ''),
      ([(230, 487), (300, 487)], 'convert', ''), ([(500, 487), (570, 487)], 'pay', ''),
      ([(1050, 217), (1100, 217), (1100, 302), (1140, 302)], 'send', 'ps', (1100, 250)), ([(810, 322), (1100, 322)], '', 'ps'),
      ([(400, 316), (400, 382), (1100, 382), (1100, 302)], '', 'ps'), ([(400, 529), (400, 560), (1100, 560), (1100, 382)], '', 'ps'),
      ([(230, 642), (1100, 642), (1100, 560)], '', 'ps'),
      ([(1250, 344), (1250, 400)], '', 'ps'), ([(1250, 484), (1250, 540)], '', 'ps'), ([(1360, 442), (1400, 442)], '', 'ps'),
    ],
  },
  'wms': {
    'lanes': [(10, 10, 1600, 160, 'BUY &amp; RECEIVE'), (10, 190, 1600, 175, 'STORE &amp; CONTROL'), (10, 385, 1600, 170, 'SELL &amp; DELIVER'), (10, 575, 1600, 120, 'RETURNS')],
    'nodes': {
      'pr': N(30, 60, 'Purchase Requisition', 'optional request'), 'po': N(290, 60, 'Purchase Order', 'issued to supplier'),
      'gr': N(550, 60, 'Goods Receiving', 'scan against PO', 'hub'), 'qi': N(810, 60, 'Inspection', 'if required', 'cond'),
      'pa': N(1070, 60, 'Put on shelf', 'to the right shelf'), 'pi': N(1390, 60, 'Purchase Invoice', 'in SQL Account', 'ext'),
      'mr': N(30, 250, 'Misc Receipt', 'stock in, no PO'),
      'st': N(290, 250, 'Stock by bin &amp; batch', 'transfer &middot; category &middot; handling unit', 'hub', w=380),
      'sc': N(740, 250, 'Stock Count', 'count, see the difference'), 'sa': N(1000, 250, 'Stock Adjustment', 'fix the difference'),
      'mi': N(1260, 250, 'Misc Issue &middot; Disposal', 'no SO &middot; expired, damaged', w=330),
      'qt': N(30, 450, 'Quotation', 'optional'), 'so': N(260, 450, 'Sales Order', 'issued'), 'rs': N(490, 450, 'Reservation', 'stock held'),
      'pk': N(720, 450, 'Picking', 'scan item &amp; bin'), 'pc': N(950, 450, 'Packing', 'if required'),
      'gd': N(1180, 450, 'Goods Delivery', 'complete', 'hub'), 'si': N(1410, 450, 'Sales Invoice', 'in SQL Account', 'ext'),
      'pr2': N(30, 605, 'Purchase Return', 'against PO / GR', h=74), 'srr': N(720, 605, 'Return Receiving', 'saleable or blocked', h=74),
      'sr': N(980, 605, 'Sales Return', 'from SO / GD', h=74),
    },
    'edges': [
      ([(230, 102), (290, 102)], 'convert', ''), ([(490, 102), (550, 102)], 'receive', ''), ([(750, 102), (810, 102)], '', 'cond'),
      ([(1010, 102), (1070, 102)], '', ''), ([(650, 60), (650, 36), (1490, 36), (1490, 60)], 'invoice', 'ps'),
      ([(1170, 144), (1170, 205), (600, 205), (600, 250)], 'into stock', ''),
      ([(230, 292), (290, 292)], '', ''), ([(670, 292), (740, 292)], '', ''), ([(940, 292), (1000, 292)], 'difference', ''),
      ([(430, 334), (430, 356), (1425, 356), (1425, 334)], 'stock out', '', (1210, 356)),
      ([(230, 492), (260, 492)], '', ''), ([(460, 492), (490, 492)], '', ''), ([(480, 334), (480, 405), (590, 405), (590, 450)], 'reserve', ''),
      ([(690, 492), (720, 492)], '', ''), ([(920, 492), (950, 492)], '', ''), ([(1150, 492), (1180, 492)], '', ''),
      ([(1380, 492), (1410, 492)], '', 'ps'),
      ([(1280, 534), (1280, 568), (1080, 568), (1080, 605)], 'return', ''), ([(980, 642), (920, 642)], '', ''),
      ([(720, 642), (705, 642), (705, 372), (640, 372), (640, 334)], 'back to stock', '', (705, 588)),
    ],
  },
  'mes': {
    'lanes': [(10, 10, 1600, 320, 'PLAN'), (10, 350, 1600, 170, 'MAKE &amp; CHECK')],
    'nodes': {
      'so': N(30, 70, 'Sales Order', 'demand', 'ext'), 'po': N(290, 70, 'Production Order', 'linked to SO line', 'hub'),
      'sch': N(550, 70, 'Schedule', 'equipment, dates'), 'pb': N(810, 70, 'Production BOM', 'for this order'),
      'mi': N(1070, 70, 'Material Issue', 'to the line'), 'stk': N(1390, 70, 'Stock', 'raw material in WMS', 'ext'),
      'bom': N(290, 220, 'BOM &amp; routing', 'recipe and steps'),
      'tr': N(1070, 410, 'Traveller card', 'order, schedule, batch'), 'out': N(810, 410, 'Output reporting', 'quantity per process'),
      'qc': N(550, 410, 'QC check', 'first piece, during the job, at receipt'), 'rc': N(290, 410, 'Production Receipt', 'finished goods', 'hub'),
      'fg': N(30, 410, 'Finished stock', 'into WMS', 'ext'),
      'n1': N(30, 560, 'Material use', 'issued (USE) &middot; auto-deducted (AUX) &middot; from previous step (REF) &middot; deducted on receipt (BACK)', 'note', w=1000, h=110),
      'n2': N(1070, 560, 'Design stage', 'MES steps follow the SuDu design. Confirm on the live system.', 'note', w=520, h=110),
    },
    'edges': [
      ([(230, 112), (290, 112)], '', ''), ([(490, 112), (550, 112)], '', ''), ([(750, 112), (810, 112)], '', ''),
      ([(1010, 112), (1070, 112)], '', ''), ([(1390, 112), (1270, 112)], 'issue', ''),
      ([(390, 220), (390, 154)], 'uses', ''),
      ([(1170, 154), (1170, 410)], 'start job', ''), ([(1070, 452), (1010, 452)], '', ''), ([(810, 452), (750, 452)], 'report', ''),
      ([(550, 452), (490, 452)], 'pass', ''), ([(290, 452), (230, 452)], 'receipt', ''),
    ],
  },
  'ai': {
    'lanes': [(10, 10, 270, 590, 'COMES IN'), (300, 10, 900, 590, 'THE AGENT'), (1220, 10, 390, 590, 'JOINS THE NORMAL FLOW')],
    'nodes': {
      'wa': N(40, 50, 'WhatsApp text', 'customer or supplier', w=210), 'vo': N(40, 160, 'Voice message', 'spoken order', w=210),
      'ph': N(40, 270, 'Photo', 'handwritten list', w=210), 'pdf': N(40, 380, 'PDF', 'purchase order', w=210),
      'ch': N(40, 490, 'AI chat', 'web and mobile', w=210),
      'un': N(360, 230, 'Understand', 'customer, item, qty, unit', 'hub', w=230), 'ask': N(360, 430, 'Ask', 'when unclear, never guess', 'cond', w=230),
      'ru': N(650, 230, 'Check rules', 'price, stock, credit', w=230), 'ap': N(650, 430, 'You approve', 'when a rule is broken', 'cond', w=230),
      'pr': N(940, 230, 'Prepare', 'drafts the document', 'hub', w=230),
      'o1': N(1260, 50, 'Sales Order', 'to WMS', 'ext', w=320), 'o2': N(1260, 160, 'Sales Invoice', 'to SQL Account', 'ext', w=320),
      'o3': N(1260, 270, 'Purchase Order', 'to WMS', 'ext', w=320), 'o4': N(1260, 380, 'Customer Payment', 'to SQL Account', 'ext', w=320),
      'o5': N(1260, 490, 'Answers &amp; reports', 'to you', 'ext', w=320),
      'nt': N(300, 620, '6 agents, 1 path', 'Sales, Purchase, Inventory, Collection, Up Sales and Finance AI all work this way.', 'note', w=1310, h=70),
    },
    'edges': [
      ([(250, 92), (300, 92), (300, 272), (360, 272)], '', ''), ([(250, 202), (300, 202)], '', ''), ([(250, 312), (300, 312), (300, 272)], '', ''),
      ([(250, 422), (300, 422), (300, 312)], '', ''), ([(250, 532), (300, 532), (300, 422)], '', ''),
      ([(410, 314), (410, 430)], 'unclear', 'cond', (410, 372)), ([(540, 430), (540, 314)], 'answer', 'cond', (540, 372)),
      ([(590, 272), (650, 272)], '', ''), ([(740, 314), (740, 430)], 'rule broken', 'cond'), ([(790, 430), (880, 430), (880, 272), (880, 272)], '', 'cond'),
      ([(880, 272), (940, 272)], '', ''),
      ([(1170, 272), (1220, 272), (1220, 92), (1260, 92)], '', 'ps'), ([(1220, 202), (1260, 202)], '', 'ps'), ([(1220, 272), (1220, 532), (1260, 532)], '', 'ps'),
      ([(1220, 312), (1260, 312)], '', 'ps'), ([(1220, 422), (1260, 422)], '', 'ps'),
    ],
  },
}

def _lab_pos(pts):
    best, bl = None, -1
    for a, b in zip(pts, pts[1:]):
        L = abs(a[0] - b[0]) + abs(a[1] - b[1])
        if L > bl: bl, best = L, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return best

def _flow_board(key):
    f = FLOWS[key]
    lanes = ''.join('<div class="ln" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><span>%s</span></div>' % l for l in f['lanes'])
    svg = ('<defs>' + ''.join('<marker id="ar%s%s" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="%s"/></marker>'
                              % (key, c, col) for c, col in (('', '#00C389'), ('ps', '#9B85FF'), ('cond', '#FFB547'))) + '</defs>')
    labs = ''
    for k, e in enumerate(f['edges']):
        pts, lab, cls = e[:3]
        d = 'M' + ' L'.join('%d %d' % p for p in pts)
        svg += '<path d="%s" class="fl %s" marker-end="url(#ar%s%s)"/>' % (d, cls, key, cls)
        if cls != 'cond':
            svg += '<circle r="7" class="dot %s"><animateMotion dur="%.1fs" begin="%.1fs" repeatCount="indefinite" path="%s"/></circle>' % (cls, 1.8 + (k % 4) * .3, (k % 5) * .35, d)
        if lab:
            x, y = e[3] if len(e) > 3 else _lab_pos(pts)
            labs += '<span class="tg %s" style="left:%dpx;top:%dpx">%s</span>' % (cls, x, y, lab)
    nodes = ''
    for nid, (x, y, w, h, t, s_, cls) in f['nodes'].items():
        nodes += '<div class="dn %s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><b>%s</b><span>%s</span></div>' % (cls, x, y, w, h, t, s_)
    return '<div class="fb">' + lanes + '<svg class="fsv" viewBox="0 0 1620 700" fill="none">' + svg + '</svg>' + nodes + labs + '</div>'

FLOW_CSS = '''
.lay { height: 760px !important; }
.ffront { padding: 0; }
.fb { position:absolute; left: 30px; top: 30px; width: 1620px; height: 700px; }
.ln { position:absolute; border-radius: 18px; background: rgba(242,251,247,.05); border: 1px solid rgba(242,251,247,.12); }
.ln span { position:absolute; left: 14px; top: 6px; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .12em; color: var(--neon); opacity: .8; }
.fsv { position:absolute; inset: 0; width: 100%; height: 100%; overflow: visible; z-index: 1; }
.fsv .fl { stroke: #00C389; stroke-width: 4; stroke-linejoin: round; stroke-linecap: round; }
.fsv .fl.ps { stroke: #9B85FF; stroke-dasharray: 10 8; }
.fsv .fl.cond { stroke: #FFB547; stroke-dasharray: 3 9; }
.fsv .dot { fill: #F2FBF7; } .fsv .dot.ps { fill: #C9BCFF; }
.dn { position:absolute; z-index: 2; border-radius: 14px; background: #fff; padding: 9px 14px; color: var(--ink); display:flex; flex-direction:column; justify-content:center;
  box-shadow: 0 14px 24px -14px rgba(0,0,0,.6); border-left: 6px solid #00C389; }
.dn b { font-size: 24px; font-weight: 700; letter-spacing: -.01em; line-height: 1.1; }
.dn span { font-size: 17px; color: var(--ink-3); margin-top: 3px; line-height: 1.2; }
.dn.hub { box-shadow: 0 0 0 3px var(--neon), 0 14px 24px -14px rgba(0,0,0,.6); }
.dn.ext { background: rgba(242,251,247,.1); color: var(--on-dark); border: 2px dashed rgba(242,251,247,.45); border-left: 6px solid #9B85FF; box-shadow: none; }
.dn.ext span { color: var(--on-dark-2); }
.dn.cond { border-left-color: #FFB547; background: #FFF7E8; }
.dn.end { background: var(--ink); color: var(--on-dark); border-left-color: #9B85FF; box-shadow: 0 0 0 2px #9B85FF; }
.dn.end b { font-size: 28px; } .dn.end span { color: var(--on-dark-2); font-size: 20px; margin-top: 10px; }
.dn.note { background: transparent; box-shadow: none; border: 0; border-left: 4px solid #FFB547; color: var(--on-dark); padding: 6px 16px; justify-content:flex-start; }
.dn.note b { font-size: 21px; color: #FFD27A; } .dn.note span { color: var(--on-dark-2); font-size: 19px; }
.tg { position:absolute; z-index: 3; transform: translate(-50%, -50%); white-space: nowrap; font-size: 17px; font-weight: 700; padding: 3px 10px; border-radius: 999px;
  background: #0B2E29; color: var(--neon); border: 1.5px solid #00C389; }
.tg.ps { color: #C9BCFF; border-color: #9B85FF; } .tg.cond { color: #FFD27A; border-color: #FFB547; }
.lay.sql .ln { background: rgba(255,255,255,.06); }
.lay.sql .dn.ext { background: rgba(255,255,255,.12); }
'''

DOC_PATH = '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/>'
PL_TILES = {'sql': ['Invoices', 'Payments', 'Credit notes', 'Tax &amp; SST', 'Accounts', 'Reports'],
            'wms': ['Receive', 'Put on shelf', 'Pick &amp; pack', 'Deliver', 'Count', 'Returns'],
            'mes': ['BOM', 'Production', 'Material issue', 'Output', 'QC', 'Receipt'],
            'ai':  ['Sales', 'Purchase', 'Inventory', 'Collection', 'Up Sales', 'Finance']}
PL_ICON = {'Receive': '<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M12 8v7M9 12l3 3 3-3"/>', 'Deliver': '<rect x="2" y="7" width="12" height="10" rx="1"/><path d="M14 10h4l3 3v4h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
           'Count': '<path d="M4 6h16M4 12h16M4 18h10"/>', 'QC': '<path d="M4 12.5l5 5L20 6.5"/>', 'Accounts': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
           'Reports': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>', 'Payments': '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M2 10h20"/>',
           'Sales': '<path d="M4 5h16v11H9l-5 4z"/>', 'Finance': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>', 'Inventory': '<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/>',
           'Collection': '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.6-1-1.7-1.5-3-1.5-1.7 0-3 .9-3 2s1 1.7 3 2 3 .9 3 2-1.3 2-3 2c-1.3 0-2.4-.5-3-1.5M12 6v2M12 16v2"/>',
           'Up Sales': '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>', 'Purchase': '<path d="M3 4h2.5l2.2 10.5h10.8L21 7H7"/><circle cx="9.5" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
           'Production': '<path d="M3 20V10l5 3V10l5 3V10l5 3V5h3v15z"/>', 'BOM': '<path d="M12 3v6M6 9h12M6 9v4M18 9v4M12 9v4"/><rect x="3" y="13" width="6" height="5" rx="1"/><rect x="9" y="13" width="6" height="5" rx="1"/><rect x="15" y="13" width="6" height="5" rx="1"/>'}

def _flip_layers():
    out = ''
    for i, (n, key, name, role, badge, flow, groups) in enumerate(DEEP):
        plate = STACK[i]
        chips = ''.join('<i>' + c + '</i>' for c in plate[3])
        nm = '<img src="../assets/sql-h.png" alt="SQL Account">' if key == 'sql' else '<b>' + name + '</b>'
        out += ('<div class="lay ' + key + ' hide" id="lay' + n + '" style="--z:' + str(i * 225) + 'px">'
                '<div class="fiso"><div class="pl-l"><em>0' + n + '</em>' + nm + '<span>' + plate[2] + '</span><strong>' + TICK + badge + '</strong></div>'
                '<div class="pl-g">' + ''.join('<div class="pt"><i>' + ic(PL_ICON.get(k, DOC_PATH), 64, 1.8) + '</i><b>' + k + '</b></div>' for k in PL_TILES[key]) + '</div>'
                '<div class="sweep"></div></div>'
                '<div class="ffront">' + _flow_board(key) + '</div></div>')
    return out

def _flip_heads():
    out = ''
    for n, key, name, role, badge, flow, groups in DEEP:
        out += ('<div class="lh" id="lh' + n + '"><div><div class="lv">LAYER ' + n + ' OF 4</div><h2>' + name + ' <em>' + role + '</em></h2></div>'
                '<div class="dft"><span class="bd">' + TICK + badge + '</span><span class="fl">' + flow + '</span></div></div>')
    return out

FLIP_CSS = '''
.slide { padding-top: 90px; }
.h1 { font-size: 66px; }
.lead { margin-top: 12px; font-size: 30px; }
.intro, .lg, .lh { transition: opacity .6s ease, transform .7s cubic-bezier(.2,.8,.2,1); }
.lg { position:absolute; left: 128px; top: 380px; display:grid; gap: 22px; z-index: 3; }
.lg > div { display:grid; grid-template-columns: 52px 1fr; align-items:center; gap: 16px; transition: opacity .5s ease; }
.lg b { width: 52px; height: 52px; border-radius: 14px; display:grid; place-items:center; font-size: 26px; font-weight: 700; background: rgba(242,251,247,.08); color: var(--on-dark); }
.lg h4 { font-size: 32px; font-weight: 700; }
.lg span { display:block; font-size: 22px; color: var(--on-dark-2); }
.lh { position:absolute; left: 128px; right: 128px; top: 92px; display:flex; align-items:flex-end; justify-content:space-between; gap: 30px; opacity: 0; transform: translateY(-14px); z-index: 6; }
.lh .lv { font-family: var(--mono); font-size: 19px; font-weight: 700; letter-spacing: .14em; color: var(--neon); }
.lh h2 { font-size: 72px; font-weight: 750; letter-spacing: -.035em; line-height: 1; margin-top: 8px; }
.lh h2 em { font-style: normal; font-size: 34px; font-weight: 600; color: var(--on-dark-2); letter-spacing: -.01em; margin-left: 14px; }
.lh .dft { display:flex; flex-direction:column; align-items:flex-end; gap: 8px; }
.lh .bd { display:flex; align-items:center; gap: 8px; font-size: 26px; font-weight: 700; padding: 10px 18px; border-radius: 12px; background: var(--neon); color: var(--ink); white-space: nowrap; }
.lh .fl { font-size: 22px; color: var(--on-dark-2); }
.scene { position:absolute; inset: 0; perspective: 2100px; perspective-origin: 50% -10%; pointer-events: none; }
/* one box per layer; every state uses the same transform list so the browser tweens it smoothly */
.lay { position:absolute; left: 120px; top: 250px; width: 1680px; height: 620px; transform-origin: 50% 40%; border-radius: 34px; transform-style: preserve-3d;
  transition: transform 1.1s cubic-bezier(.65,0,.25,1), opacity .7s ease, filter .8s ease; will-change: transform;
  background: linear-gradient(135deg, #12423A, #0A2C27); border: 2px solid rgba(0,245,169,.55); box-shadow: 0 50px 100px -30px rgba(0,0,0,.7); }
.lay.sql { background: linear-gradient(135deg, #4A35B8, #2A1E78); border-color: #A793FF; }
.lay.ai { background: linear-gradient(135deg, #0F5A48, #083A30); border-color: var(--neon); box-shadow: 0 0 90px rgba(0,245,169,.35), 0 50px 100px -30px rgba(0,0,0,.7); }
.lay.iso, .lay.stack { transform: translate3d(200px, 225px, 0) rotateX(58deg) rotateZ(-34deg) scale(.29) translateZ(var(--z)); }
.lay.iso { transform: translate3d(330px, 120px, 0) rotateX(58deg) rotateZ(-34deg) scale(.42) translateZ(0px); box-shadow: 0 0 0 3px var(--neon), 0 0 120px rgba(0,245,169,.4); }
.lay.front { transform: translate3d(0, -40px, 0) rotateX(36deg) rotateZ(0deg) scale(.8) translateZ(0px); }
.lay.back1 { transform: translate3d(0, 70px, 0) rotateX(36deg) rotateZ(0deg) scale(.8) translateZ(-130px); filter: blur(3px) brightness(.55); }
.lay.back2 { transform: translate3d(0, 70px, 0) rotateX(36deg) rotateZ(0deg) scale(.8) translateZ(-260px); filter: blur(5px) brightness(.4); }
.lay.back3 { transform: translate3d(0, 70px, 0) rotateX(36deg) rotateZ(0deg) scale(.8) translateZ(-390px); filter: blur(7px) brightness(.3); }
.lay.hide { transform: translate3d(0, 70px, 0) rotateX(36deg) rotateZ(0deg) scale(.8) translateZ(520px); opacity: 0; }
/* the two faces of a layer: the plate (in the stack) and the detail board (facing you) */
.fiso, .ffront { position:absolute; inset: 0; transition: opacity .5s ease; }
.ffront { padding: 36px; opacity: 0; }
.dgrid { height: 100%; } .dc { height: 100%; } .g8 .dc { height: auto; }
.lay.front .ffront, .lay[class*="back"] .ffront { opacity: 1; transition-delay: .35s; }
.lay.front .fiso, .lay[class*="back"] .fiso { opacity: 0; }
.fiso { padding: 0 70px; display:flex; flex-direction:column; justify-content:center; }
.fiso b { font-size: 120px; font-weight: 800; letter-spacing: -.03em; color: var(--on-dark); line-height: 1; }
.lay.ai .fiso b { color: var(--neon); }
.fiso img { height: 110px; align-self:flex-start; background: #fff; border-radius: 20px; padding: 14px 22px; }
.fiso span { font-family: var(--mono); font-size: 40px; font-weight: 600; letter-spacing: .08em; color: var(--neon); margin-top: 16px; text-transform: uppercase; }
.fiso .ch { display:flex; flex-wrap: wrap; gap: 16px; margin-top: 30px; }
.fiso .ch i { font-style: normal; font-size: 44px; font-weight: 600; padding: 12px 28px; border-radius: 999px; background: rgba(242,251,247,.12); color: var(--on-dark); }
.lay.ai .fiso .ch i { background: var(--neon); color: var(--ink); }
.dgrid { display:grid; grid-template-columns: repeat(4, 1fr); gap: 22px; align-items: start; }
.dgrid.g8 { gap: 16px; }
.dc { background: #fff; border-radius: 22px; padding: 22px 24px; color: var(--ink); box-shadow: 0 24px 40px -24px rgba(0,0,0,.5); }
.dc .dh b { display:block; font-size: 46px; font-weight: 750; letter-spacing: -.02em; }
.dc .dh span { display:block; font-size: 27px; font-weight: 600; color: var(--green); margin-top: 2px; }
.dc ul { list-style:none; margin-top: 18px; display:grid; gap: 14px; }
.dc li { display:flex; align-items:center; gap: 10px; font-size: 33px; line-height: 1.15; color: var(--ink-2); }
.dc li svg { width: 24px; height: 24px; color: var(--emerald); flex:none; }
.g8 .dc { padding: 16px 20px; }
.g8 .dc .dh b { font-size: 36px; }
.g8 .dc ul { margin-top: 8px; gap: 6px; }
.g8 .dc li { font-size: 26px; }
.dc.you { background: var(--neon); }
.dc.you .dh span, .dc.you li, .dc.you li svg { color: var(--ink); }
/* step-driven visibility of the flat texts */
body:not([data-s="0"]):not([data-s="5"]) .intro, body:not([data-s="0"]):not([data-s="5"]) .lg { opacity: 0; transform: translateY(-14px); }
body[data-s="1"] #lh1, body[data-s="2"] #lh2, body[data-s="3"] #lh3, body[data-s="4"] #lh4 { opacity: 1; transform: none; }
'''


LIGHT9 = '''
body { background: #F4FBF8; }
.lg b { background: #fff !important; color: var(--ink) !important; box-shadow: 0 0 0 1px var(--line); }
.lg > div:first-child b { background: var(--neon) !important; }
.lg h4 { color: var(--ink); } .lg span { color: var(--ink-2); }
.lh h2 { color: var(--ink); } .lh h2 em { color: var(--ink-2); } .lh .lv { color: var(--green); } .lh .fl { color: var(--ink-2); }
/* plates and boards: light, like the detail map */
.lay { background: radial-gradient(circle, rgba(2,34,31,.12) 1.4px, transparent 1.8px) 0 0 / 40px 40px, linear-gradient(160deg, #FFFFFF, #E3F3EC) !important;
  border: 2px solid rgba(0,165,122,.55) !important; box-shadow: 0 0 0 1px rgba(2,34,31,.06), 0 60px 100px -40px rgba(2,34,31,.45) !important; }
.lay.sql { background: radial-gradient(circle, rgba(91,67,214,.14) 1.4px, transparent 1.8px) 0 0 / 40px 40px, linear-gradient(160deg, #F6F2FF, #E6DEFF) !important; border-color: #A793FF !important; }
.lay.ai { background: radial-gradient(circle, rgba(2,34,31,.12) 1.4px, transparent 1.8px) 0 0 / 40px 40px, linear-gradient(160deg, #EFFFF8, #C9F7E6) !important; border-color: var(--emerald) !important; box-shadow: 0 0 0 2px rgba(0,245,169,.5), 0 60px 100px -40px rgba(2,34,31,.45) !important; }
.fiso b { color: var(--ink) !important; } .lay.ai .fiso b { color: var(--green) !important; }
.fiso span { color: var(--green) !important; } .lay.sql .fiso span { color: #5B43D6 !important; }
.fiso .ch i { background: #fff !important; color: var(--ink) !important; box-shadow: 0 0 0 1px var(--line); }
.lay.ai .fiso .ch i { background: var(--ink) !important; color: var(--neon) !important; }
.lay.iso, .lay.stack { box-shadow: 0 0 0 1px rgba(2,34,31,.08), 0 40px 70px -30px rgba(2,34,31,.4) !important; }
.lay[class*="back"] { filter: blur(3px) brightness(.97) saturate(.7) !important; opacity: .75; }
/* lanes and cards */
.ln { background: rgba(255,255,255,.55) !important; border: 1px solid rgba(2,34,31,.08) !important; }
.ln span { color: var(--green) !important; opacity: 1 !important; }
.lay.sql .ln span { color: #5B43D6 !important; }
.dn { border-radius: 16px; border: 1px solid rgba(2,34,31,.08); border-left: 6px solid #00C389; box-shadow: 0 16px 26px -18px rgba(2,34,31,.5); padding: 8px 14px 8px 46px; }
.dn::before { content:""; position:absolute; left: 12px; top: 50%; width: 22px; height: 26px; margin-top: -13px; border-radius: 4px;
  background: linear-gradient(135deg, transparent 6px, #E6F6EE 0) ; box-shadow: inset 0 0 0 2px #00A57A; }
.dn.hub { box-shadow: 0 0 0 3px #00C389, 0 16px 26px -18px rgba(2,34,31,.5); background: #F0FFF8; }
.dn.ext { background: rgba(255,255,255,.6); color: var(--ink); border: 2px dashed rgba(124,92,255,.55); border-left: 6px solid #9B85FF; }
.dn.ext::before { box-shadow: inset 0 0 0 2px #7C5CFF; background: #F1EDFF; }
.dn.ext span { color: #5B43D6; font-weight: 600; }
.dn.cond { background: #FFF7E8; border-left-color: #FFB547; } .dn.cond::before { box-shadow: inset 0 0 0 2px #E59A1A; background: #FFF1D6; }
.dn.end { background: #2E2180; color: #fff; } .dn.end::before { display:none; } .dn.end { padding-left: 18px; } .dn.end span { color: #DCD3FF; }
.dn.note { color: var(--ink); background: #FFF7E8; border-left: 4px solid #FFB547; border-radius: 12px; box-shadow: none; padding-left: 16px; }
.dn.note::before { display: none; } .dn.note b { color: #9A5B00; } .dn.note span { color: var(--ink-2); }
.tg { background: #fff; color: var(--green); border-color: #00C389; box-shadow: 0 6px 12px -8px rgba(2,34,31,.4); }
.tg.ps { color: #5B43D6; } .tg.cond { color: #9A5B00; }
.fsv .dot { fill: #00A57A; } .fsv .dot.ps { fill: #7C5CFF; }
/* pro plate faces (stack view) */
.fiso { padding: 56px 64px !important; display:grid !important; grid-template-columns: 640px 1fr; gap: 50px; align-items:center; overflow:hidden; border-radius: 32px; }
.pl-l em { display:block; font-style: normal; font-size: 150px; font-weight: 800; line-height: .9; letter-spacing: -.05em; color: transparent; -webkit-text-stroke: 3px rgba(0,165,122,.55); }
.lay.sql .pl-l em { -webkit-text-stroke-color: rgba(124,92,255,.6); }
.pl-l b { display:block; font-size: 120px !important; margin-top: 10px; }
.pl-l img { height: 120px !important; margin-top: 16px; box-shadow: 0 0 0 2px rgba(124,92,255,.3); }
.pl-l span { display:block; font-size: 38px !important; margin-top: 14px !important; white-space: nowrap; }
.pl-l strong { display:inline-flex; align-items:center; gap: 12px; margin-top: 28px; font-size: 44px; font-weight: 800; padding: 14px 28px; border-radius: 18px; background: var(--neon); color: var(--ink); }
.pl-l strong svg { width: 44px; height: 44px; }
.lay.sql .pl-l strong { background: #7C5CFF; color: #fff; }
.pl-g { display:grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.pt { background: #fff; border-radius: 26px; padding: 26px 26px 24px; box-shadow: 0 0 0 1px rgba(2,34,31,.08), 0 18px 30px -18px rgba(2,34,31,.45); display:flex; flex-direction:column; gap: 14px; }
.pt i { width: 96px; height: 96px; border-radius: 24px; display:grid; place-items:center; background: #E6F6EE; color: var(--green); }
.lay.sql .pt i { background: #EEE9FF; color: #5B43D6; }
.lay.ai .pt i { background: var(--ink); color: var(--neon); }
.pt b { font-size: 46px; font-weight: 750; letter-spacing: -.02em; color: var(--ink); line-height: 1.05; }
.sweep { position:absolute; inset: 0; pointer-events:none; background: linear-gradient(105deg, transparent 35%, rgba(255,255,255,.75) 50%, transparent 65%) -100% 0 / 250% 100% no-repeat; animation: sweep 5s ease-in-out infinite; }
#lay2 .sweep { animation-delay: 1.2s; } #lay3 .sweep { animation-delay: 2.4s; } #lay4 .sweep { animation-delay: 3.6s; }
@keyframes sweep { 0% { background-position: 150% 0; } 35%, 100% { background-position: -100% 0; } }
.lay.stack.ai { box-shadow: 0 0 0 4px rgba(0,245,169,.6), 0 0 120px rgba(0,245,169,.45), 0 40px 70px -30px rgba(2,34,31,.4) !important; animation: glow 3s ease-in-out infinite alternate; }
@keyframes glow { to { box-shadow: 0 0 0 4px rgba(0,245,169,.9), 0 0 180px rgba(0,245,169,.7), 0 40px 70px -30px rgba(2,34,31,.4); } }
html.static .sweep, html.static .lay { animation: none !important; }
.lay.drop { transform: translate3d(330px, -260px, 0) rotateX(58deg) rotateZ(-34deg) scale(.38) translateZ(calc(var(--z) + 900px)); opacity: 0; }
'''

FLIP_JS = '''
<script>
(function () {
  const L = [1, 2, 3, 4].map(n => document.getElementById('lay' + n));
  function cls(el, c) { el.className = el.className.replace(/\\b(hide|iso|front|back1|back2|back3|stack|drop)\\b/g, '').trim() + ' ' + c; }
  // 0: SQL plate in 3D; 1: it flips up; 2-4: the next layer lands on top, earlier ones go back and blur; 5: all fold into the stack
  function set(s) {
    document.body.dataset.s = String(s);
    L.forEach((el, i) => {
      if (s === 0) cls(el, 'stack');
      else if (s >= 5) cls(el, 'stack');
      else { const top = s - 1, d = top - i; cls(el, d < 0 ? 'hide' : d === 0 ? 'front' : 'back' + Math.min(d, 3)); }
    });
  }
  const STATIC = navigator.webdriver || location.hash === '#static';
  if (STATIC) set(5);
  else { L.forEach(el => cls(el, 'drop')); document.body.dataset.s = '0';
    L.forEach((el, i) => setTimeout(() => cls(el, 'stack'), 500 + i * 380)); }
  addEventListener('message', e => { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
'''

slide('03-layers-3d', '4 layers in 3D', SEC[0], 'light', 'data-sparks="none" style="--gx:62%;--gy:60%;--mx:60%;--my:55%"', FLIP_CSS + FLOW_CSS + LIGHT9, '''
<div class="intro"><div class="kicker">How SuDu is built</div>
<h1 class="h1">4 layers. 1 system.</h1>
<p class="lead">Each layer stands on the one below. The AI runs them all.</p></div>
<div class="lg">''' + ''.join('<div class="l%s"><b>%s</b><div><h4>%s</h4><span>%s</span></div></div>' % (n, n, t, s_) for n, t, s_ in STACK_LEGEND) + '''</div>
''' + _flip_heads() + '''
<div class="scene">''' + _flip_layers() + '''</div>
''' + FLIP_JS,
"\"Here is how SuDu is built, one layer at a time. It starts with the foundation: SQL Account.\"\n\n(Next: the plate flips up.) Layer 1, SQL Account: \"Your accounting. Invoices, credit notes, payments, e-invoice, tax, your P&L. It keeps your accounts right, and it records what has already happened. Every document SuDu creates goes down here automatically.\"\n\n(Next: WMS lands on top.) Layer 2, WMS: \"On top sits the warehouse. Receiving, putting on the shelf, picking, packing, delivery, transfers, counts, batch and expiry. Every carton is scanned the moment it moves, so the stock figure is always true.\"\n\n(Next: MES lands on top.) Layer 3, MES: \"If you manufacture, the factory. The BOM, the production order, material issue, output, QC, scrap and machine time. Every job planned, tracked and costed as it happens.\"\n\n(Next: AI agents land on top.) Layer 4, AI agents: \"And on top, the AI agents, reading every layer below and doing the routine work. Nothing is saved until a person approves.\"\n\n(Next: all four fold into the stack.) \"4 layers, 1 system. Each stands on the one below, and the AI runs them all.\"\n\nThis slide has 5 extra Next presses.\nNext: \"That is SuDu. Now let's talk about you.\"")

STAGE_ICONS = [
    '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 11h7M9 15h7M9 19h4"/>',
    '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/>',
    '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/><path d="M7 8h6M7 11h4"/>',
    '<path d="M12 2c.5 4.7 3.3 7.5 8 8-4.7.5-7.5 3.3-8 8-.5-4.7-3.3-7.5-8-8 4.7-.5 7.5-3.3 8-8z"/><path d="M19 15l.6 2.4L22 18l-2.4.6L19 21l-.6-2.4L16 18l2.4-.6z"/>',
    '<rect x="8" y="2.5" width="8" height="6" rx="2"/><path d="M10.5 5.5h.01M13.5 5.5h.01"/><rect x="7" y="10" width="10" height="7" rx="1.5"/><path d="M7 11.5L4 15l1.5 2M17 11.5l3 3.5-1.5 2M9.5 17v4.5M14.5 17v4.5"/>',
]
STAGES = [
    ('1.0', 'BEFORE 1980', 'Handwritten', 'Paperwork and record books', 'Slow, lost forms', 100, 100),
    ('2.0', '1980s – 90s', 'Spreadsheets', 'Excel files typed and emailed', 'Many files, typos', 85, 85),
    ('3.0', '1990s – 2020s', 'Software', 'Separate systems, keyed in by staff', 'Data typed 2x', 65, 70),
    ('4.0', 'SINCE 2025', 'AI agents', 'AI does the office work. You approve.', 'Stock still moved by hand', 25, 35),
]
SW, FW, GAP = 282, 432, 26
CX = [0, SW + GAP, 2 * (SW + GAP), 3 * (SW + GAP), 3 * (SW + GAP) + FW + GAP]   # card left edges
CW = [SW, SW, SW, FW, SW]
SX = [CX[i] + CW[i] / 2 for i in range(5)]   # node x = card centre
SY = [250, 228, 186, 124, 52]                                                     # rising curve
WARN = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/></svg>'

def _stage_curve():
    pts = [(-30, 262)] + list(zip(SX, SY)) + [(1700, 20)]
    d = 'M%d %d' % (pts[1][0], pts[1][1])
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += ' C%.1f %.1f %.1f %.1f %d %d' % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    return d
STAGE_CURVE = _stage_curve()

def _stage_graph():
    out = ''
    for i in range(5):
        d = 0.6 + i * 0.35
        cls = 'fin' if i == 3 else ('next' if i == 4 else '')
        out += ('<div class="nd %s pop" style="left:%dpx;top:%dpx;--d:%.2fs"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg></div>'
                % (cls, SX[i], SY[i], d, STAGE_ICONS[i]))
        out += '<span class="stem f" style="left:%dpx;top:%dpx;height:%dpx;--d:%.2fs"></span>' % (SX[i], SY[i] + 40, 310 - SY[i] - 40, d + 0.2)
    for i, (ver, yrs, name, how, pain, manual, cost) in enumerate(STAGES):
        d = 0.75 + i * 0.35
        now = i == 3
        if now:
            out += ('<div class="fc pop" style="left:%dpx;--d:%.2fs"><div class="in"><span class="n"><b>%s</b>%s<span class="nowt">NOW</span></span>'
                    '<h3>%s</h3><p>%s</p>'
                    '<div class="bars"><div class="mw"><span>Manual work</span><i><b style="--w:%d%%;--d:%.2fs"></b></i></div>'
                    '<div class="mw c"><span>Cost</span><i><b style="--w:%d%%;--d:%.2fs"></b></i></div></div></div></div>'
                    % (CX[i], d, ver, yrs, name, how, manual, d + 0.6, cost, d + 0.75))
            continue
        out += ('<div class="st r%s" style="left:%dpx;--d:%.2fs"><div class="n"><b>%s</b>%s%s</div><h3>%s</h3><p>%s</p><div class="pain">%s<span>%s</span></div>'
                '<div class="bars"><div class="mw"><span>Manual work</span><i><b style="--w:%d%%;--d:%.2fs"></b></i></div>'
                '<div class="mw c"><span>Cost</span><i><b style="--w:%d%%;--d:%.2fs"></b></i></div></div></div>'
                % (' now' if now else '', CX[i], d, ver, yrs, '<span class="nowt">NOW</span>' if now else '', name, how, WARN, pain,
                   manual, d + 0.6, cost, d + 0.75))
    return out

slide('04-five-stages', '5 stages', SEC[0], 'dark', 'data-sparks="none" style="--gx:86%;--gy:22%;--mx:85%;--my:30%"', '''
.slide { padding-top: 88px; }
.h1 { font-size: 66px; }
.lead { font-size: 29px; margin-top: 10px; }
.lead b { color: var(--on-dark); font-weight: 650; }
.graph { position:relative; width: 1664px; height: 730px; margin-top: 10px; }
.graph svg.cv { position:absolute; inset: 0; width: 1664px; height: 300px; overflow: visible; }
.streak { stroke-dasharray: 160 2400; stroke-dashoffset: 160; animation: streak 3.4s cubic-bezier(.5,0,.3,1) 2.2s infinite; }
@keyframes streak { to { stroke-dashoffset: -2240; } }
html.static .streak { display: none; }
.nd { position:absolute; width: 76px; height: 76px; margin: -38px 0 0 -38px; border-radius: 50%%; background: #0B2E29; border: 2px solid rgba(242,251,247,.25); display:grid; place-items:center; color: var(--on-dark-2); z-index: 3; }
.nd svg { width: 36px; height: 36px; }
.nd.next { border: 2px dashed rgba(0,245,169,.55); color: var(--neon); background: #0A2622; }
.nd.now { border-color: var(--neon); color: var(--neon); box-shadow: 0 0 0 8px rgba(0,245,169,.12), 0 0 40px rgba(0,245,169,.4); }
.nd.fin { width: 104px; height: 104px; margin: -52px 0 0 -52px; background: var(--neon); border-color: var(--neon); color: var(--ink); box-shadow: 0 0 0 14px rgba(0,245,169,.14), 0 0 80px rgba(0,245,169,.7); }
.nd.fin svg { width: 50px; height: 50px; }
.nd.fin::before, .nd.fin::after { content:""; position:absolute; inset: -2px; border-radius: 50%%; border: 2px solid rgba(0,245,169,.7); animation: ring 2.4s ease-out infinite; }
.nd.fin::after { animation-delay: 1.2s; }
@keyframes ring { from { transform: scale(1); opacity: .9; } to { transform: scale(2.3); opacity: 0; } }
.stem { position:absolute; width: 0; border-left: 2px dashed rgba(242,251,247,.18); z-index: 1; }
.st { position:absolute; top: 310px; width: 282px; height: 420px; padding: 20px 22px; border-radius: 22px; background: rgba(242,251,247,.04); border: 1px solid rgba(242,251,247,.1); display:flex; flex-direction:column; }
.st .n, .fc .n { font-family: var(--mono); font-size: 17px; letter-spacing: .1em; font-weight: 600; color: var(--on-dark-3); display:flex; align-items:center; gap: 10px; }
.st .n b, .fc .n b { font-size: 19px; color: var(--on-dark); background: rgba(242,251,247,.1); padding: 2px 8px; border-radius: 6px; }
.nowt { margin-left: auto; color: var(--ink); background: var(--neon); padding: 2px 8px; border-radius: 6px; font-size: 16px; }
.st.now { background: rgba(0,245,169,.1); border: 1.5px solid rgba(0,245,169,.6); box-shadow: 0 0 60px rgba(0,245,169,.16); }
.st.now .n b { background: var(--neon); color: var(--ink); }
.st.now .mw b { background: linear-gradient(90deg, #00F5A9, #00A57A); }
.st h3 { font-size: 38px; font-weight: 700; letter-spacing: -.02em; margin-top: 12px; }
.bars { margin-top: auto; display:grid; gap: 20px; }
.pain, .win { display:flex; align-items:center; gap: 8px; margin-top: 14px; font-size: 21px; font-weight: 600; white-space: nowrap; padding: 7px 11px; border-radius: 10px; width: fit-content; }
.pain { color: #FFB08F; background: rgba(255,138,91,.1); }
.pain svg { flex: none; }
.st.now .pain { color: #FFD27A; background: rgba(255,210,122,.1); }
.win { color: var(--ink); background: var(--neon); }
.mw.c b { background: linear-gradient(90deg, #FFD27A, #FFB547); }
.st.now .mw.c b, .fc .mw.c b { background: linear-gradient(90deg, #9FFFE0, #4FE3B8); }
.k { font-family: var(--mono); font-size: 16px; letter-spacing: .12em; font-weight: 600; color: var(--on-dark-3); margin-top: 14px; display:flex; align-items:center; gap: 8px; }
.k.warn { color: #FFB08F; }
.st p { font-size: 25px; line-height: 1.3; color: var(--on-dark); margin-top: 6px; }
.st p:not(.pb) { min-height: 90px; }
.st p.pb { color: var(--on-dark-2); }
.mw { }
.mw span { font-size: 22px; font-weight: 600; color: var(--on-dark-2); }
.mw i { display:block; height: 14px; border-radius: 7px; background: rgba(242,251,247,.08); margin-top: 8px; overflow:hidden; }
.mw b { display:block; height: 100%%; width: 0; border-radius: 4px; background: linear-gradient(90deg, #FFB08F, #FF8A5B); animation: fillw 1.2s var(--ease) forwards; animation-delay: var(--d); }
@keyframes fillw { to { width: var(--w); } }
.fc { position:absolute; top: 310px; width: 432px; height: 420px; border-radius: 26px; padding: 2px; overflow: hidden; }
.fc::before { content:""; position:absolute; inset: -60%%; background: conic-gradient(from 0deg, rgba(0,245,169,0) 0deg, #00F5A9 60deg, rgba(0,245,169,0) 140deg, rgba(0,245,169,.25) 220deg, rgba(0,245,169,0) 300deg); animation: spin 5s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fc .in { position:relative; height: 100%%; border-radius: 24px; background: linear-gradient(170deg, #0C3A33, #062621 60%%); padding: 20px 26px 20px; display:flex; flex-direction:column; box-shadow: inset 0 0 80px rgba(0,245,169,.12); }
.fc .n { color: var(--neon); }
.fc h3 { font-size: 52px; line-height: 1.04; font-weight: 750; letter-spacing: -.025em; margin-top: 4px; }
.eq { display:flex; align-items:center; gap: 10px; margin-top: 12px; }
.eq span { font-size: 21px; font-weight: 700; padding: 7px 13px; border-radius: 12px; background: var(--neon); color: var(--ink); white-space: nowrap; }
.eq span.o { background: transparent; color: var(--neon); border: 1.5px solid var(--neon); }
.eq em { font-style: normal; font-size: 26px; font-weight: 700; color: var(--on-dark-2); }
.fc p { font-size: 25px; line-height: 1.3; color: var(--on-dark); margin-top: 6px; }
.fc .row { display:flex; flex-wrap: wrap; gap: 0 10px; }
.fc .pain { color: #FFD27A; background: rgba(255,210,122,.1); }
.st.future { background: transparent; border: 2px dashed rgba(242,251,247,.22); }
.st.future h3, .st.future p { color: var(--on-dark-2); }
.st.future .n b { background: transparent; color: var(--neon); border: 1.5px solid rgba(0,245,169,.5); }
.st.future .mw b { background: linear-gradient(90deg, rgba(0,245,169,.6), rgba(0,165,122,.6)); }
.st.future .mw.c b { background: linear-gradient(90deg, rgba(159,255,224,.55), rgba(79,227,184,.55)); }
.fc .k { color: var(--neon); }
.fc .n b { background: var(--neon); color: var(--ink); }
.fc .nowt { margin-left: auto; }
.nxt { margin-left: auto; color: var(--neon); border: 1.5px dashed var(--neon); padding: 1px 8px; border-radius: 6px; font-size: 16px; }
.eq { flex-wrap: wrap; row-gap: 8px; margin-top: 12px; }
.eq strong { font-size: 22px; font-weight: 700; color: var(--neon); }
.fc .mw b { background: linear-gradient(90deg, #00F5A9, #00A57A); }
/* the race */
.mk { position:absolute; transform: translateX(-50%%); z-index: 4; }
.mk .in { display:flex; flex-direction:column; align-items:center; }
.mk .chip { white-space: nowrap; font-size: 21px; font-weight: 700; padding: 7px 15px; border-radius: 999px; }
.mk .stm { width: 2px; height: 16px; }
.mk.you { left: %(x3)dpx; top: %(you)dpx; }
.mk.you .chip { background: #F2FBF7; color: var(--ink); } .mk.you .stm { background: #F2FBF7; }
.mk.comp { left: %(x3)dpx; top: %(comp0)dpx; }
.mk.comp .chip { background: #FF8A5B; color: #1A0F0A; box-shadow: 0 0 40px rgba(255,138,91,.5); }
.mk.comp .stm { background: #FF8A5B; height: 0; animation: stm .4s ease 4.6s forwards; }
@keyframes stm { to { height: 16px; } }
.mk.comp .in { animation: race 1.4s cubic-bezier(.65,0,.25,1) 3.3s forwards; }
@keyframes race { to { transform: translate(%(dx)dpx, %(dy)dpx); } }
.gap { position:absolute; left: %(x3)dpx; width: %(dx)dpx; top: %(gapy)dpx; height: 0; border-top: 2.5px dashed #FF8A5B; opacity: 0; z-index: 3; animation: fade .6s ease 4.8s forwards; }
.gap::before, .gap::after { content:""; position:absolute; top: -9px; width: 2.5px; height: 16px; background: #FF8A5B; }
.gap::before { left: 0; } .gap::after { right: 0; }
.gap span { position:absolute; left: 50%%; transform: translateX(-50%%); top: 8px; white-space: nowrap; font-size: 23px; font-weight: 700; color: #FFB08F; }
''' % dict(x3=SX[2], you=SY[2] - 40 - 16 - 40, comp0=SY[2] - 40 - 16 - 40 - 52, dx=SX[3] - SX[2], dy=(SY[3] - 40 - 16 - 40) - (SY[2] - 40 - 16 - 40 - 52), gapy=262),
'''
<h1 class="h1 r" style="--d:.1s">The AI era is here. <span class="g">Don&rsquo;t get left behind.</span></h1>
<p class="lead r" style="--d:.25s">Every era cut <b>manual work</b> and <b>cost</b>. In every era, the companies that waited lost their customers.</p>
<div class="graph">
  <svg class="cv" viewBox="0 0 1664 300" fill="none">
    <defs><linearGradient id="sc" x1="0" x2="1"><stop offset="0" stop-color="#A9C4BA" stop-opacity=".3"/><stop offset=".6" stop-color="#00F5A9" stop-opacity=".8"/><stop offset="1" stop-color="#00F5A9"/></linearGradient>
      <linearGradient id="sf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00F5A9" stop-opacity=".14"/><stop offset="1" stop-color="#00F5A9" stop-opacity="0"/></linearGradient>
      <filter id="glow" x="-20%%" y="-200%%" width="140%%" height="500%%"><feGaussianBlur stdDeviation="4"/></filter></defs>
    <path class="f" style="--d:1.4s" d="%(curve)s L%(xl)d 300 L%(xf)d 300 Z" fill="url(#sf)"/>
    <path class="draw" pathLength="1" style="--d:.3s;--dur:2s" d="%(curve)s" stroke="url(#sc)" stroke-width="4" stroke-linecap="round"/>
    <path class="streak" d="%(curve)s" stroke="#F2FBF7" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>
    <path class="streak" d="%(curve)s" stroke="#00F5A9" stroke-width="3" stroke-linecap="round"/>
  </svg>
  %(graph)s
  <div class="st future r" style="left:%(fx)dpx;--d:2.2s"><div class="n"><b>5.0</b>LATE 2020s</div>
    <h3>Physical AI</h3><p>Robots do the physical work</p>
    <div class="bars"><div class="mw"><span>Manual work</span><i><b style="--w:5%%;--d:2.9s"></b></i></div>
    <div class="mw c"><span>Cost</span><i><b style="--w:15%%;--d:3.05s"></b></i></div></div></div>
  <div class="mk you f" style="--d:2.4s"><div class="in"><span class="chip">Your company?</span><span class="stm"></span></div></div>
  <div class="mk comp f" style="--d:2.7s"><div class="in"><span class="chip">Your competitor</span><span class="stm"></span></div></div>
  <div class="gap"><span>The gap grows every year</span></div>
</div>
''' % dict(curve=STAGE_CURVE, graph=_stage_graph(), xl=SX[4], xf=SX[0], fx=CX[4]),
"\"Think about the industrial revolutions: steam, then electricity, then computers. Each one changed who did the work, and the factories that moved first won. The same thing happens in how a company is run.\n\nBusiness 1.0, until about 1980: handwritten. Orders in a book, stock counted by hand. Slow, and nobody sees the whole picture.\n\nBusiness 2.0, the 1980s and 1990s: spreadsheets. Excel files passed around by email. Faster, but many versions and typing mistakes.\n\nBusiness 3.0, from the 1990s until now: software. SQL Account, and a separate system for each team. Much better, but the systems do not talk, and people still key everything in. This is where most companies in this room are today.\n\nBusiness 4.0 is already here. ChatGPT arrived at the end of 2022 and could only talk. Since 2025, AI agents do the work: they read the WhatsApp order, create the documents, chase the payment, inside an AI-native ERP, and people approve. That is what SuDu does today, and what you will see in the demo.\n\nAnd business 5.0 is next: physical AI. Humanoid robots and self-driving trucks do the physical work, run by the same system. AI-native ERP plus robots: the autonomous enterprise.\n\n(Pause while the competitor marker climbs.) Here is the point. The future is not coming; it is here. Your competitor can already be at 4.0 while you are at 3.0, and in every revolution so far, the ones who moved first took the customers. The gap grows every year.\"\n\nPoint at the two bars on each card: manual work and cost fall with every era, and fall the most at 4.0 and 5.0.\nNote: the years are rounded eras, not exact dates; the manual-work and cost bars are an illustration, not measured figures. Physical AI timing (late 2020s) is an outlook, and it is not on sale today.\nNext: \"Now let's look at how SuDu is built, from the side.\"")

FLAGS_HTML = open(os.path.join(HERE, '_flags.html')).read() if os.path.exists(os.path.join(HERE, '_flags.html')) else ''
JOURNEY = [
    ('2021', 'R&amp;D begins', 'WMS and MES built'),
    ('2022', 'AI R&amp;D', 'Building the AI'),
    ('2023', 'Launch', 'Live in Malaysia'),
    ('2025', 'Regional', 'Singapore and China'),
    ('2026', 'AI goes live', 'ASEAN and Europe'),
]
def _journey():
    out = ''
    for i, (y, t, line) in enumerate(JOURNEY):
        d = 1.6 + i * 0.35
        out += ('<div class="ms' + (' cur' if i == 4 else '') + '" style="left:' + '%.1f' % (i * 25) + '%"><i class="dot pop" style="--d:' + '%.2f' % d + 's"></i>'
                + '<div class="r" style="--d:%.2fs"><b>' % (d + .1) + y + '</b><h4>' + t + '</h4><p>' + line + '</p></div></div>')
    return out
LOGOS = ['petronas', 'bhpetrol', 'ytl', 'twin-arrow', 'toyota.svg', 'mosca.svg']
def _marq():
    one = ''.join('<span class="lgo"><img src="../assets/logos/%s" alt="%s"></span>' % (l if '.' in l else l + '.png', l.split('.')[0]) for l in LOGOS)
    return '<div class="mq"><div class="mqt">' + one * 4 + '</div></div>'

WHO_CSS = '''
.slide { padding-top: 84px; }
.top { display:flex; align-items:flex-start; justify-content:space-between; gap: 40px; }
.h1 { font-size: 80px; max-width: 1180px; line-height: 1.02; }
.h1 .g { color: var(--neon); }
/* flipping name card */
.flip { width: 340px; height: 150px; perspective: 1000px; flex:none; margin-top: 6px; }
.fi { position:relative; width: 100%; height: 100%; transform-style: preserve-3d; animation: flip 6s cubic-bezier(.65,0,.35,1) 1.2s infinite; }
@keyframes flip { 0%, 40% { transform: rotateY(0); } 50%, 90% { transform: rotateY(180deg); } 100% { transform: rotateY(360deg); } }
.fc { position:absolute; inset: 0; backface-visibility: hidden; border-radius: 24px; display:flex; align-items:center; justify-content:center; gap: 22px;
  background: linear-gradient(135deg, rgba(0,245,169,.18), rgba(0,245,169,.04)); border: 1.5px solid rgba(0,245,169,.5); box-shadow: 0 0 60px rgba(0,245,169,.2); }
.fc.bk { transform: rotateY(180deg); }
.fc b { font-size: 70px; font-weight: 750; letter-spacing: -.02em; font-family: var(--sans), 'PingFang SC', 'Hiragino Sans GB', sans-serif; }
.fc span { font-family: var(--mono); font-size: 22px; letter-spacing: .12em; color: var(--neon); line-height: 1.3; }
html.static .fi { animation: none; }
/* stats */
.stats { display:grid; grid-template-columns: 420px 1fr; gap: 22px; margin-top: 34px; }
.stat { padding: 22px 28px; border-radius: 24px; display:flex; flex-direction:column; justify-content:center; }
.stat .n { font-size: 96px; font-weight: 750; letter-spacing: -.045em; line-height: 1; }
.stat .n small { font-size: .5em; vertical-align: .4em; margin-right: 6px; color: var(--neon); }
.stat .t { font-size: 26px; color: var(--on-dark-2); margin-top: 6px; }
.stat .hd2 { display:flex; align-items:baseline; gap: 18px; }
.stat .cty { display:flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }
.stat .cty svg { display:block; border-radius: 3px; flex: none; }
.stat .cty i { font-style: normal; display:flex; align-items:center; gap: 9px; font-size: 22px; font-weight: 600; padding: 6px 14px 6px 8px; border-radius: 999px; background: rgba(242,251,247,.08); color: var(--on-dark);
  opacity: 0; animation: rise .6s var(--ease) forwards; }
''' + ''.join('.stat .cty i:nth-child(%d) { animation-delay: %.2fs; }\n' % (k + 1, 1.0 + k * .12) for k in range(6)) + '''
html.static .stat .cty i { opacity: 1; animation: none; }
/* journey */
.jr { position:relative; height: 190px; margin: 40px 60px 0 20px; }
.jr .rail { position:absolute; left: 0; right: 0; top: 13px; height: 4px; border-radius: 2px; background: rgba(242,251,247,.1); }
.jr .rail i { position:absolute; left: 0; top: 0; bottom: 0; width: 0; border-radius: 2px; background: linear-gradient(90deg, var(--emerald), var(--neon)); animation: rail 2s cubic-bezier(.4,0,.2,1) 1.4s forwards; }
@keyframes rail { to { width: 100%; } }
.jr .comet { position:absolute; top: 3px; left: 0; width: 120px; height: 24px; margin-left: -120px; border-radius: 12px;
  background: radial-gradient(closest-side, #F2FBF7, rgba(0,245,169,.6) 50%, transparent); opacity: 0; animation: comet 3.4s ease-in-out 3.6s infinite; }
@keyframes comet { 0% { left: 0; opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
html.static .jr .comet { display:none; }
.ms { position:absolute; top: 0; width: 280px; margin-left: -15px; }
.ms .dot { display:block; width: 30px; height: 30px; border-radius: 50%; background: var(--night); border: 4px solid var(--emerald); }
.ms.cur .dot { background: var(--neon); border-color: #F2FBF7; box-shadow: 0 0 0 10px rgba(0,245,169,.2), 0 0 40px rgba(0,245,169,.7); }
.ms.cur .dot::after { content:""; position:absolute; inset: -4px; border-radius: 50%; border: 2px solid var(--neon); animation: ring 2s ease-out infinite; }
@keyframes ring { from { transform: scale(1); opacity: .9; } to { transform: scale(2.4); opacity: 0; } }
.ms b { display:block; font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--neon); margin-top: 16px; }
.ms h4 { font-size: 32px; font-weight: 700; letter-spacing: -.02em; margin-top: 2px; }
.ms p { font-size: 23px; color: var(--on-dark-2); margin-top: 2px; }
.ms:last-child { margin-left: -265px; text-align: right; } .ms:last-child .dot { margin-left: auto; }
/* bottom band */
.band { position:absolute; left: 128px; right: 128px; bottom: 112px; display:grid; grid-template-columns: 1fr 740px; gap: 22px; align-items:end; }
.mqw { border-radius: 22px; padding: 12px 0 14px; overflow:hidden; }
.mqw h5 { font-size: 16px !important; }
.mqw h5, .ptn h5 { font-family: var(--mono); font-size: 18px; letter-spacing: .14em; color: var(--on-dark-3); font-weight: 700; padding: 0 24px; }
.mq { margin-top: 10px; overflow:hidden; -webkit-mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); }
.mqt { display:flex; gap: 12px; width: max-content; animation: mq 22s linear infinite; }
@keyframes mq { to { transform: translateX(-50%); } }
.lgo { height: 72px; width: 150px; border-radius: 16px; background: #fff; display:grid; place-items:center; flex:none; }
.lgo img { max-height: 48px; max-width: 118px; object-fit: contain; }
.ptn { position:relative; border-radius: 22px; padding: 16px 0 18px; overflow:hidden; }
.ptn::after { content:""; position:absolute; top: 0; bottom: 0; width: 120px; left: -160px; background: linear-gradient(100deg, transparent, rgba(255,255,255,.22), transparent); transform: skewX(-18deg); animation: shine 4s ease-in-out 2.4s infinite; }
@keyframes shine { 0% { left: -160px; } 40%, 100% { left: 110%; } }
.ptn .row { display:flex; align-items:center; gap: 12px; margin-top: 12px; padding: 0 20px; }
.ptn .sql { height: 100px; padding: 0 16px; flex: 1; border-radius: 16px; background: #fff; display:flex; flex-direction:column; align-items:center; justify-content:center; gap: 6px; }
.ptn .sql img { height: 34px; }
.ptn .sql span { font-size: 18px; font-weight: 800; letter-spacing: .1em; color: var(--ink); background: var(--neon); padding: 3px 10px; border-radius: 6px; }
.ptn .cb { width: 100px; height: 100px; border-radius: 16px; background: #fff; display:grid; place-items:center; flex:none; position:relative; }
.ptn .cb img { max-width: 82px; max-height: 82px; }
.ptn .cb em { position:absolute; bottom: -10px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-style: normal; font-size: 13px; font-weight: 700; background: #FFB547; color: #1A0F0A; padding: 2px 7px; border-radius: 6px; }
/* bright theme overrides */
body { background: #F4FBF8; }
.mesh { position:absolute; inset: -20%; z-index: 0; pointer-events:none; filter: blur(70px); opacity: .9;
  background: radial-gradient(30% 35% at 20% 25%, rgba(0,245,169,.45), transparent 70%), radial-gradient(28% 32% at 80% 20%, rgba(124,92,255,.28), transparent 70%),
  radial-gradient(35% 35% at 70% 85%, rgba(0,165,122,.32), transparent 70%), radial-gradient(25% 30% at 25% 85%, rgba(255,181,71,.25), transparent 70%);
  animation: mesh 18s ease-in-out infinite alternate; }
@keyframes mesh { 50% { transform: translate(4%, -3%) rotate(6deg) scale(1.05); } 100% { transform: translate(-3%, 3%) rotate(-4deg); } }
html.static .mesh { animation: none; }
.h1 { color: var(--ink); }
.h1 .g { background: linear-gradient(90deg, #00A57A, #00C389, #7C5CFF, #00A57A) 0 0 / 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent; animation: grad 6s linear infinite; }
@keyframes grad { to { background-position: -300% 0; } }
.fc { background: linear-gradient(135deg, #fff, #E6F6EE); border-color: rgba(0,165,122,.5); box-shadow: 0 20px 50px -20px rgba(0,165,122,.45); }
.fc b { color: var(--ink); } .fc span { color: var(--green); }
.glass { background: rgba(255,255,255,.72) !important; border: 1px solid rgba(255,255,255,.95) !important; box-shadow: 0 0 0 1px rgba(2,34,31,.06), 0 30px 60px -36px rgba(2,34,31,.4) !important; }
.stat .n { color: var(--ink); } .stat .n small { color: var(--emerald); }
.stat .t { color: var(--ink-2); }
.stat .cty i { background: #fff; color: var(--ink); box-shadow: 0 0 0 1px var(--line); }
.stat .cty svg { box-shadow: 0 0 0 1px rgba(2,34,31,.12); }
.jr .rail { background: rgba(2,34,31,.1); }
.ms .dot { background: #fff; border-color: var(--emerald); }
.ms.cur .dot { background: var(--neon); border-color: var(--ink); box-shadow: 0 0 0 10px rgba(0,245,169,.25), 0 0 40px rgba(0,245,169,.7); }
.ms b { color: var(--green); } .ms h4 { color: var(--ink); } .ms p { color: var(--ink-2); }
.mqw h5, .ptn h5 { color: var(--ink-3); }
.lgo, .ptn .cb, .ptn .sql { box-shadow: 0 0 0 1px var(--line), 0 10px 20px -14px rgba(2,34,31,.35); }
.ptn::after { background: linear-gradient(100deg, transparent, rgba(0,245,169,.35), transparent); }
.kicker { color: var(--green); }
.chrome { color: var(--ink-3) !important; }

'''

WHO_HTML = '''
<div class="mesh"></div>
<div class="top">
  <div><div class="kicker r" style="--d:.05s">Who we are</div><h1 class="h1 r" style="--d:.15s">An AI product from Malaysia.<br>Running in <span class="g"><span data-count="6" data-delay=".9">0</span> countries.</span></h1></div>
  <div class="flip pop" style="--d:.5s"><div class="fi"><div class="fc"><b>速度</b><span>SPEED<br>in Chinese</span></div><div class="fc bk"><b>Sudu</b><span>SPOON<br>in Malay</span></div></div></div>
</div>
<div class="stats">
  <div class="glass stat r" style="--d:.6s"><div class="n"><small>&gt;</small><span data-count="100" data-delay=".9">0</span></div><div class="t">companies run WMS and MES</div></div>
  <div class="glass stat r" style="--d:.75s"><div class="hd2"><div class="n" data-count="6" data-delay="1">0</div><div class="t">countries with users</div></div>''' + FLAGS_HTML.replace('<div class="cty">', '<div class="cty">', 1) + '''</div>
</div>
<div class="jr"><div class="rail"><i></i><span class="comet"></span></div>''' + _journey() + '''</div>
<div class="band">
  <div class="glass mqw r" style="--d:2.6s"><h5>TRUSTED BY</h5>''' + _marq() + '''</div>
  <div class="glass ptn r" style="--d:2.8s"><h5>PARTNER &amp; CERTIFIED</h5><div class="row">
    <div class="sql"><img src="../assets/sql-h.png" alt="SQL Account"><span>OFFICIAL PARTNER</span></div>
    <div class="cb"><img src="../assets/logos/mdec.png" alt="MDEC"></div>
    <div class="cb"><img src="../assets/logos/hrdcorp-provider.png" alt="HRD Corp"></div>
    <div class="cb"><img src="../assets/logos/iso27001.png" alt="ISO 27001"><em>IN PROGRESS</em></div>
  </div></div>
</div>
'''

slide('02-who-we-are', 'Who we are', SEC[0], 'light', 'data-sparks="9,0" style="--gx:85%;--gy:20%;--mx:80%;--my:30%"', WHO_CSS, WHO_HTML,
"\"Hello everyone. A little about SuDu AI before we start.\n\nSuDu means two things. In Chinese, 速度 means speed: fast to set up, fast results. In Malay, sudu means spoon: easy enough to spoon-feed.\n\nWe started in 2021 by building the warehouse and factory systems, and refined them for two years. In 2022 we started building the AI. In 2023 we launched in Malaysia, in 2025 we went to Singapore and China, and this year the AI went live. Today more than 100 companies run their warehouse or factory on SuDu, and we have users in 6 countries.\n\nCompanies like Petronas, BHPetrol, YTL Hotels and Twin Arrow run on SuDu. We are certified by MDEC and HRD Corp, and we are an official SQL Account partner.\"\n\nDo: keep it under two minutes.\nSource: SuDu company profile, pages 1 to 3.\nNext: \"And here is who you will be listening to today.\"")

SPK_CSS = '''
.wrap { flex:1; display:grid; grid-template-columns: 600px 1fr; gap: 90px; align-items:center; }
.ph { position:relative; width: 560px; height: 560px; justify-self:center; }
.ph svg { position:absolute; inset: -40px; width: 640px; height: 640px; }
.ph .ring { transform-origin: 320px 320px; animation: spin 40s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ph img { position:absolute; inset: 30px; width: 500px; height: 500px; border-radius: 50%; object-fit: cover; border: 6px solid var(--neon); box-shadow: 0 0 120px rgba(0,245,169,.35); }
.ph .was { position:absolute; left: 50%; bottom: -78px; transform: translateX(-50%); display:flex; align-items:center; gap: 14px; white-space: nowrap; }
.ph .was span { font-family: var(--mono); font-size: 17px; letter-spacing: .14em; color: var(--on-dark-3); }
.ph .was i { height: 58px; padding: 0 14px; border-radius: 12px; background: #fff; display:grid; place-items:center; }
.ph .was img { position: static; width: auto; height: 34px; border: 0; border-radius: 0; box-shadow: none; }
.nm { font-size: 104px; font-weight: 700; letter-spacing: -.045em; line-height: .95; margin-top: 16px; }
.role { font-size: 34px; font-weight: 600; color: var(--neon); margin-top: 14px; }
.bio { font-size: 30px; line-height: 1.4; color: var(--on-dark-2); margin-top: 16px; max-width: 900px; }
.tiles { display:grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 36px; }
.tiles .glass { padding: 20px 22px; border-radius: 20px; }
.tiles b { display:block; font-size: 50px; font-weight: 700; letter-spacing: -.03em; color: var(--neon); line-height: 1; }
.tiles > div > span { display:block; font-size: 22px; color: var(--on-dark-2); margin-top: 8px; }
.row2 { display:grid; grid-template-columns: 1.35fr 1fr; gap: 16px; margin-top: 16px; }
.row2 .glass { padding: 20px 24px; border-radius: 20px; }
.row2 h4 { font-family: var(--mono); font-size: 17px; letter-spacing: .12em; color: var(--neon); font-weight: 600; }
.chips { display:flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chips i { font-style: normal; font-size: 21px; font-weight: 600; padding: 6px 13px; border-radius: 999px; background: rgba(242,251,247,.1); color: var(--on-dark); }
.trn { display:flex; align-items:center; gap: 18px; background: var(--neon) !important; color: var(--ink); border: 0 !important; }
.trn img { width: 70px; height: 70px; border-radius: 50%; background: #fff; }
.trn b { display:block; font-size: 44px; font-weight: 700; letter-spacing: -.03em; line-height: 1; }
.trn div > span { font-size: 22px; font-weight: 600; }
'''

SPK_HTML = '''
<div class="wrap">
  <div class="ph pop" style="--d:.2s">
    <svg viewBox="0 0 640 640" fill="none"><g class="ring"><circle cx="320" cy="320" r="306" stroke="rgba(0,245,169,.35)" stroke-dasharray="3 10"/><circle cx="320" cy="14" r="8" fill="#00F5A9"/></g></svg>
    <img src="../assets/speaker-landis.jpg" alt="Landis Soam">
    <div class="was f" style="--d:1.4s"><span>PREVIOUSLY AT</span><i><img src="../assets/logos/gdex.png" alt="GDEX"></i><i><img src="../assets/logos/topglove.png" alt="Top Glove"></i></div>
  </div>
  <div>
    <div class="kicker r" style="--d:.1s">Your speaker today</div>
    <div class="nm r" style="--d:.25s">Landis Soam</div>
    <div class="role r" style="--d:.4s">CEO and Founder, SuDu AI</div>
    <p class="bio r" style="--d:.55s">IT background. Led Industry 4.0 projects at GDEX, Top Glove and other global firms.<br>Founded SuDu AI 5 years ago.</p>
    <div class="tiles">
      <div class="glass r" style="--d:.75s"><b><span data-count="8" data-delay=".9">0</span>+</b><span>years in IT</span></div>
      <div class="glass r" style="--d:.85s"><b><span data-count="6" data-delay="1">0</span>+</b><span>years in supply chain</span></div>
      <div class="glass r" style="--d:.95s"><b data-count="3" data-delay="1.1">0</b><span>years implementing SAP</span></div>
      <div class="glass r" style="--d:1.05s"><b><span data-count="5" data-delay="1.2">0</span>+</b><span>years with SQL and AutoCount</span></div>
    </div>
    <div class="row2">
      <div class="glass r" style="--d:1.2s"><h4>INDUSTRY 4.0 PROJECTS</h4><div class="chips"><i>Warehouse RFID</i><i>Manufacturing system</i><i>SAP ERP</i><i>Advance shipment notice</i></div></div>
      <div class="glass trn r" style="--d:1.3s"><img src="../assets/logos/hrdcorp-provider.png" alt="HRD Corp"><div><b><span data-count="50" data-delay="1.5">0</span>+</b><span>companies trained, HRDC certified trainer</span></div></div>
    </div>
  </div>
</div>
'''

slide('02-speaker', 'Your speaker', SEC[0], 'dark', 'data-sparks="9,1 1,5" style="--gx:22%;--gy:50%;--mx:25%;--my:50%"', SPK_CSS, SPK_HTML,
"\"I'm Landis, CEO and founder of SuDu AI. My background is IT and supply chain. Before SuDu, I led Industry 4.0 projects at GDEX, Top Glove and other global companies: warehouse RFID, manufacturing systems, SAP. I have spent more than five years working with SQL Account and AutoCount companies like yours, and as an HRDC certified trainer I have trained more than fifty companies.\n\nSo I know what your office looks like on a Monday morning. \"\n\nDo: under one minute.\nIf someone else presents, swap the photo and facts (Owen Ng, CRO: 7+ years supply chain, 2 years SAP projects, 5 years building SuDu AI).\nSource: SuDu company profile, page 4.\nNext: \"And my co-founder, Owen.\"")


OWEN_HTML = '''
<div class="wrap">
  <div class="ph pop" style="--d:.2s">
    <svg viewBox="0 0 640 640" fill="none"><g class="ring"><circle cx="320" cy="320" r="306" stroke="rgba(0,245,169,.35)" stroke-dasharray="3 10"/><circle cx="320" cy="14" r="8" fill="#00F5A9"/></g></svg>
    <img src="../assets/speaker-owen.jpg" alt="Owen Ng">
  </div>
  <div>
    <div class="kicker r" style="--d:.1s">Your speaker today</div>
    <div class="nm r" style="--d:.25s">Owen Ng</div>
    <div class="role r" style="--d:.4s">CRO and Founder, SuDu AI</div>
    <p class="bio r" style="--d:.55s">From supply chain and SAP to SuDu AI: bringing sales, purchasing, warehouse and factory work together in 1 system.</p>
    <div class="tiles" style="grid-template-columns: repeat(3, 1fr)">
      <div class="glass r" style="--d:.75s"><b><span data-count="7" data-delay=".9">0</span>+</b><span>years in supply chain</span></div>
      <div class="glass r" style="--d:.85s"><b data-count="2" data-delay="1">0</b><span>years of SAP projects</span></div>
      <div class="glass r" style="--d:.95s"><b data-count="5" data-delay="1.1">0</b><span>years building SuDu AI</span></div>
    </div>
    <div class="row2" style="grid-template-columns: 1fr">
      <div class="glass r" style="--d:1.2s"><h4>WHAT HE BUILDS</h4><div class="chips"><i>WMS: warehouse</i><i>MES: production</i><i>AI assistant</i></div></div>
    </div>
  </div>
</div>
'''

slide('02-speaker-owen', 'Speaker: Owen', SEC[0], 'dark', 'data-sparks="9,1 1,5" style="--gx:22%;--gy:50%;--mx:25%;--my:50%"', SPK_CSS, OWEN_HTML,
"\"And I'm Owen, CRO and co-founder of SuDu AI. I started in supply chain, spent two years on SAP projects, and for the last five years I have been building SuDu: the warehouse system, the factory system and the AI assistant, bringing sales, purchasing, warehouse and factory work together in one system.\"\n\nDo: under one minute.\nSource: SuDu company profile, page 5.\nNext: \"Before we start, here is what we cover today.\"")

slide('03-tell-us', 'Tell us your problem', SEC[0], 'light', 'data-sparks="2,1 8,4" style="--gx:22%;--gy:50%;--mx:25%"', '''
.wrap { display:grid; grid-template-columns: 460px 1fr; gap: 130px; align-items:center; height:100%; }
ol { list-style:none; margin-top: 56px; display:grid; gap: 34px; counter-reset: q; }
li { display:grid; grid-template-columns: 76px 1fr; align-items:baseline; font-size: 40px; line-height: 1.25; font-weight: 500; letter-spacing: -.01em; counter-increment: q; }
li::before { content: counter(q); font-family: var(--mono); font-size: 28px; color: var(--green); }
.small { margin-top: 52px; padding-left: 76px; font-size: 28px; }
.qrimg { position:absolute; inset: 62px; width: calc(100% - 124px); height: calc(100% - 124px); image-rendering: pixelated; }
''', '''
<div class="wrap">
  <div class="qr glass pop" style="--d:.2s"><img class="qrimg" src="../assets/qr-survey.png" alt="Problem poll QR code"><div class="frame"></div><div class="scan"></div></div>
  <div>
    <h1 class="h1 r" style="--d:.1s">Scan and answer 3 questions</h1>
    <ol>
      <li class="r" style="--d:.5s">Which job eats the most time in your office?</li>
      <li class="r" style="--d:.65s">How many people key in data or chase payments?</li>
      <li class="r" style="--d:.8s">How much do you trust your stock and finance figures?</li>
    </ol>
  </div>
</div>
''', "\"Take out your phone and scan this. Three questions, one minute. Your answers will be on this screen in a few minutes. By the end of today each of you will leave with three things written on the worksheet in front of you: your number, your readiness score, and your first AI job.\"\n\nDo: coaches help anyone who cannot scan. The demo driver watches the answers come in.\nForm: name, company, mobile; Q1 keying in orders / chasing payments / checking stock / typing up paper forms / making reports; Q2 1 person / 2 to 3 / 4 or more; Q3 (stock and finance figures) fully / mostly / not much; consent line.\nNext: \"While the answers come in, here are the five problems we hear most.\"")

# ============================================================ 2 · THE PROBLEM
TOP5 = [
    ('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>', 'Orders typed in by hand',
     'Every WhatsApp and email order keyed in again. It takes a team.', 'MANPOWER'),
    ('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2M9 2h6"/>', 'Routine work done by people',
     'Chasing overdue payments, sending statements, daily checks.', 'EVERY DAY'),
    ('<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>', 'Problems found too late',
     'Sales drop, customers leave, stock runs out before anyone sees it.', 'TOO LATE'),
    ('<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/>', 'Stock that is never right',
     'The system says 40 cartons. The shelf has 12.', 'NO TRUST'),
    ('<path d="M6 3h12v18l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21z"/><path d="M9 8h6M9 11.5h6M9 15h4"/>', 'Cash comes in late',
     'Invoices go out days after delivery. Bank slips get lost in the chat.', 'CASH FLOW'),
]
def _top5():
    out = ''
    for i, (icon, t, line, tag) in enumerate(TOP5):
        out += ('<div class="iss r" style="--d:' + '%.2f' % (0.35 + i * 0.22) + 's"><span class="no">' + str(i + 1) + '</span>'
                '<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + icon + '</svg></span>'
                '<div class="tx"><h3>' + t + '</h3><p>' + line + '</p></div><span class="tg">' + tag + '</span></div>')
    return out

slide('03-top-5-issues', 'Top 5 issues', SEC[1], 'light', 'data-sparks="9,0" style="--gx:85%;--gy:15%;--mx:85%;--my:20%"', '''
.slide { padding-top: 90px; }
.h1 { font-size: 72px; }
.list { flex:1; display:grid; grid-template-rows: repeat(5, 1fr); gap: 14px; margin-top: 34px; }
.iss { display:grid; grid-template-columns: 90px 84px 1fr auto; align-items:center; gap: 26px; padding: 0 34px 0 22px; border-radius: 24px; background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 24px 40px -30px rgba(2,34,31,.35); }
.iss .no { font-size: 72px; font-weight: 700; letter-spacing: -.04em; color: var(--green); text-align:center; line-height: 1; }
.iss .ic { width: 72px; height: 72px; border-radius: 20px; background: var(--ink); color: var(--neon); display:grid; place-items:center; }
.iss .ic svg { width: 40px; height: 40px; }
.iss h3 { font-size: 36px; font-weight: 700; letter-spacing: -.02em; }
.iss p { font-size: 26px; color: var(--ink-2); margin-top: 4px; }
.iss .tg { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .1em; color: #B4451F; background: rgba(255,138,91,.14); padding: 8px 14px; border-radius: 10px; }
.iss:first-child { background: var(--ink); }
.iss:first-child .no { color: var(--neon); }
.iss:first-child .ic { background: var(--neon); color: var(--ink); }
.iss:first-child h3 { color: var(--on-dark); }
.iss:first-child p { color: var(--on-dark-2); }
.iss:first-child .tg { color: #FFB08F; background: rgba(255,138,91,.16); }
h1 .sig:lang(en) { margin-left: .26em; }
''', '''
<h1 class="h1 r" style="--d:.1s">The 5 problems we hear in<span class="sig" style="--sd:1.4s">every business</span></h1>
<div class="list">''' + _top5() + '''</div>
''',
"\"While your answers come in, here are the five problems we hear in almost every company we visit.\n\nOne: orders typed in by hand. Every WhatsApp and email order is keyed in again, and it takes a team of people to do it.\n\nTwo: routine work done by people. Chasing overdue payments, sending statements, checking the same reports every morning.\n\nThree: problems found too late. Sales drop, a good customer stops ordering, stock runs out, and nobody notices until it hurts.\n\nFour: stock that is never right. The system says forty cartons, the shelf has twelve.\n\nAnd five: cash comes in late. The invoice goes out days after the delivery, and the bank slip is lost somewhere in the chat.\n\nPut your hand up if you have at least three of these.\" (Pause.)\n\nDo: let the hands go up; it is the same point the poll will make with data.\nNote: issue 5 is our suggestion; swap it for the room's top answer if the poll shows something else.\nNext: \"Let me show you how problem number one starts.\"")

PROB_NAMES = ['Orders typed in by hand', 'Routine work done by people', 'Problems found too late', 'Stock that is never right', 'Cash comes in late']
def prob(n, d='0s'):
    dots = ''.join('<b class="on"></b>' if k == n else '<b></b>' for k in range(1, 6))
    return '<div class="prob f" style="--d:' + d + '">PROBLEM ' + str(n) + ' OF 5<i>' + dots + '</i><span>' + PROB_NAMES[n - 1] + '</span></div>'

CLOCK = '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="#C0392B" stroke-width="2.2" stroke-linecap="round" style="vertical-align:-6px"><circle cx="12" cy="12" r="9"/><path d="M12 6v6"/></svg>'
MSG = [  # (text, annotation or '', bold)
    ('Jaya Grocer KL', '', True),
    ('', '', False),
    ('China', 'A heading? A brand? Where the goods come from?', False),
    ('Bwg besar', '', False),
    ('10kg x ---', 'Bawang besar. How many 10 kg bags?', False),
    ('', '', False),
    ('Ayam cincang', '', False),
    ('8ekor x ---', 'Minced chicken, 8 birds. How many?', False),
    ('', '', False),
    ('25mm clear 1pc', 'Which item is this? Which code?', False),
    ('', '', False),
    ('Pls arrange delivery be4 12pm - ' + CLOCK, 'Before 12 pm. Which day?', False),
]
def _msg():
    out, k = '', 0
    for t, ann, bold in MSG:
        cls = 'ln b' if bold else ('ln gap' if not t else 'ln')
        a = ''
        if ann:
            a = '<span class="an" style="--i:' + str(k) + '"><i>?</i>' + ann + '</span>'
            k += 1
        out += '<div class="' + cls + '"><span class="tx">' + t + '</span>' + a + '</div>'
    return out

PO_LINES = [('1', '020114', 'MJ', 'Bawang Putih Kopek 1kg', '9550000114012', 'BAG (10)', '4', '50.00', '200.00'),
            ('2', '020115', 'MJ', 'Bawang Putih Kopek 500g', '9550000115019', 'PKT (1)', '30', '2.50', '75.00'),
            ('3', '020131', 'MJ', 'Bawang Besar China 10kg', '9550000131026', 'BAG (1)', '6', '28.00', '168.00')]
def _po():
    rows = ''.join('<tr class="it"><td>%s</td><td>%s</td><td>%s</td><td>%s<br><small>%s</small></td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % l for l in PO_LINES)
    return '''<div class="po"><div class="wm">SAMPLE</div>
  <div class="poh"><div><b class="co">Seri Mewah Hypermarket Sdn Bhd</b><div class="dl"><u>Deliver To:</u><br>Seri Mewah Hypermarket (Kepong Branch)<br>Lot 12, Jalan Kepong Baru 3,<br>52100 Kepong, Kuala Lumpur<br>Tel: 03-6250 0000</div></div>
    <div class="mid">Supplier Code : MJF01<br>Supplier Name : Maju Jaya Foods Sdn Bhd<br>Credit Code : 30 DAYS<br>Department : Grocery</div>
    <div class="rt"><b class="tt">Purchase Order (PO)</b><br>PO No : <b>PO26111504SMK</b><br>PO Date : 15/11/2026<br>Delivery Date : 16/11/2026<br>Cancel Date : 17/11/2026<div class="bc"></div></div></div>
  <table><tr class="hd"><th>No.</th><th>Stock Code</th><th>Brand</th><th>Stock Description</th><th>U/M</th><th class="n">Qty</th><th class="n">Unit Cost</th><th class="n">Nett Cost</th></tr>''' + rows + '''
  <tr class="tot"><td colspan="5">Total:</td><td class="n">40</td><td></td><td class="n">443.00</td></tr></table>
  <div class="pof">1) Quote our PO number on your DO / Invoice. 2) Loading time 9:00am to 12:30pm. 3) Goods must have at least 6 months shelf life.</div></div>'''

PO_CSS = '''
.pow { position:absolute; left: 128px; right: 128px; top: 270px; z-index: 5; opacity: 0; transform: translateY(40px) scale(.97); pointer-events: none;
  transition: opacity .6s ease, transform .8s cubic-bezier(.2,.8,.2,1); display:grid; grid-template-columns: 1fr 470px; gap: 40px; align-items:start; }
body[data-step="2"] .pow { opacity: 1; transform: none; }
body[data-step="2"] .chat, body[data-step="2"] .boss { visibility: hidden; }
.po { position:relative; background: #fff; color: #111; border-radius: 10px; padding: 26px 30px 20px; font-family: Arial, Helvetica, sans-serif; font-size: 17px; line-height: 1.35;
  box-shadow: 0 0 0 1px rgba(0,0,0,.08), 0 50px 90px -30px rgba(0,0,0,.7); transform: rotate(-1deg); overflow:hidden; }
.po .wm { position:absolute; right: 30px; bottom: 90px; font-size: 110px; font-weight: 900; letter-spacing: .1em; color: rgba(200,40,40,.1); transform: rotate(-14deg); pointer-events:none; }
.poh { display:grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 18px; }
.po .co { font-size: 19px; }
.po .dl { margin-top: 10px; border: 1px solid #333; padding: 8px 10px; }
.po .mid { padding-top: 26px; }
.po .rt { text-align:right; }
.po .tt { text-decoration: underline; font-size: 19px; }
.po .bc { height: 46px; margin: 10px 0 0 auto; width: 240px; background: repeating-linear-gradient(90deg, #111 0 2px, #fff 2px 4px, #111 4px 5px, #fff 5px 8px, #111 8px 11px, #fff 11px 12px); }
.po table { width: 100%; border-collapse: collapse; margin-top: 18px; }
.po th, .po td { border: 1px solid #555; padding: 6px 8px; text-align:left; vertical-align: top; }
.po th { font-weight: 600; background: #f3f3f3; }
.po .n { text-align:right; }
.po small { color: #555; }
.po tr.it td { background: rgba(255,138,91,.0); transition: background .5s ease 1s; }
body[data-step="2"] .po tr.it td { background: rgba(255,138,91,.18); }
.po .tot td { font-weight: 700; border: 0; border-top: 2px solid #333; }
.po .pof { margin-top: 18px; font-size: 14px; color: #444; }
.poc h3 { font-size: 46px; font-weight: 700; letter-spacing: -.02em; line-height: 1.1; }
.poc p { font-size: 28px; color: var(--on-dark-2); margin-top: 16px; line-height: 1.4; }
.poc ul { list-style:none; margin-top: 26px; display:grid; gap: 14px; }
.poc li { display:flex; gap: 12px; align-items:center; font-size: 27px; font-weight: 600; }
.poc li i { font-style: normal; flex:none; width: 38px; height: 38px; border-radius: 50%; background: #FF8A5B; color: #1A0F0A; display:grid; place-items:center; font-weight: 800; }
'''
PO_HTML = '''<div class="pow">''' + _po() + '''
  <div class="poc"><h3>Or it arrives as a PDF purchase order.</h3><p>Neater, but still typed in again by hand.</p>
    <ul><li><i>1</i>Match their stock code to yours</li><li><i>2</i>Check the price and unit (BAG of 10?)</li><li><i>3</i>Key every line into SQL Account</li><li><i>4</i>Repeat for the next PO</li></ul></div>
</div>'''

slide('04-guess-the-order', 'Guess the order', SEC[1], 'dark', 'data-sparks="9,1" style="--gx:30%;--gy:60%;--mx:30%;--my:60%"', '''
.h1 { margin-top: 18px; }
.chat { position:relative; margin-top: 110px; width: 1664px; }
.bub { position:absolute; left: 0; top: -22px; bottom: -64px; width: 640px; border-radius: 30px 30px 30px 8px; background: #fff; box-shadow: 0 40px 80px -30px rgba(0,0,0,.6); }
.bub .meta { position:absolute; right: 26px; bottom: 18px; font-family: var(--mono); font-size: 20px; color: var(--ink-3); }
.who { position:absolute; left: 0; top: -70px; display:flex; align-items:center; gap: 12px; font-size: 22px; color: var(--on-dark-2); }
.who b { width: 34px; height: 34px; border-radius: 50%; background: #25D366; display:grid; place-items:center; }
.who svg { width: 20px; height: 20px; color: #fff; }
.ln { position:relative; display:grid; grid-template-columns: 640px 1fr; align-items:center; min-height: 50px; }
.ln.gap { min-height: 22px; }
.ln .tx { padding-left: 40px; font-size: 38px; color: var(--ink); line-height: 1.2; }
.ln.b .tx { font-weight: 700; }
.an { display:flex; align-items:center; gap: 14px; margin-left: 30px; font-size: 30px; font-weight: 600; color: var(--on-dark);
  opacity: 0; transform: translateX(-24px); transition: opacity .45s ease, transform .5s cubic-bezier(.2,.8,.2,1); transition-delay: calc(var(--i) * .35s); }
.an::before { content:""; width: 60px; height: 2px; background: #FF8A5B; margin-left: -30px; }
.an i { font-style: normal; flex:none; width: 40px; height: 40px; border-radius: 50%; background: #FF8A5B; color: #1A0F0A; display:grid; place-items:center; font-weight: 800; }
body[data-step="1"] .an { opacity: 1; transform: none; }
.ans { position:absolute; right: 128px; bottom: 130px; max-width: 760px; text-align:right; font-size: 34px; font-weight: 700; color: #FFB08F; opacity: 0; transition: opacity .6s ease 2s; }
body[data-step="1"] .ans { opacity: 1; }
.boss { position:absolute; right: 128px; top: 110px; width: 230px; height: 230px; transition: opacity .4s; }
body[data-step="1"] .boss { opacity: 0; }
''' + PO_CSS, prob(1) + '''
<h1 class="h1 r" style="--d:.1s">What did this customer order?</h1>
<div class="chat pop" style="--d:.5s">
  <div class="who"><b>''' + ic(CHAT, 20) + '''</b>WhatsApp &nbsp;·&nbsp; today 8:12 am</div>
  <div class="bub"><span class="meta">8:12 am &#10003;&#10003;</span></div>
  ''' + _msg() + '''
</div>
<img class="av boss pop" style="--d:1.4s" src="../assets/av/boss-facepalm.svg" alt="The boss, puzzled">
<div class="ans">Somebody in your office decodes this. Every order. Every day.</div>
''' + PO_HTML + '''
<script>
(function () {
  document.body.dataset.step = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.step = String(e.data.deckStep); });
})();
</script>
''',
"\"This is a real order, from a real customer chat. Read it with your table: what exactly did this customer order? You have twenty seconds.\" (Pause, let two tables answer.)\n\n(Next: the question marks appear.) \"China: is that a heading, a brand, or where the onions come from? Bwg besar, ten kilo, times what? How many bags? Ayam cincang, eight ekor, times how many? Twenty-five mil clear, one piece: which item is that in your system, which code? And deliver before twelve: which day?\n\nNobody outside your office could decode this. But somebody inside your office does it, for every order, every day: opens the chat, guesses, checks the last order, looks up the codes, and types it into SQL Account.\"\n\n(Next: a PDF purchase order slides in.) \"Some customers are neater. They send a PDF purchase order. Better, but somebody still has to match their stock code to yours, check the price and the unit, a bag of ten or one, and key every line into SQL Account. Then the next PO.\" (The PO is a mock-up with made-up names.)\n\nThis slide has 2 extra Next presses: the questions, then the PDF.\nNext: \"And that same order gets typed again, and again.\"")

def chart(q, opts, d):
    rows = ''.join('<div class="opt"><span>%s</span><i></i></div>' % o for o in opts)
    return '<div class="glass card r" style="--d:%s"><div class="q">%s</div>%s</div>' % (d, q, rows)
slide('06-typed-three-times', 'Keyed in by hand', SEC[1], 'light', 'data-sparks="9,1 1,5" style="--gx:50%;--gy:55%;--mx:50%;--my:55%"', '''
.flow { position:relative; margin-top: auto; display:grid; grid-template-columns: repeat(3, 440px); justify-content:space-between; }
.flow svg.line { position:absolute; left: 0; top: 185px; width: 100%; height: 40px; overflow:visible; }
.node { height: 450px; padding: 30px; display:flex; flex-direction:column; position:relative; z-index:1; }
.node .pic { flex:1; border-radius: 18px; background: #fff; box-shadow: 0 0 0 1px var(--line); display:grid; place-items:center; overflow:hidden; position:relative; }
.node .name { font-size: 32px; font-weight: 650; margin-top: 22px; letter-spacing: -.01em; }
.badge { position:absolute; top: -22px; right: -18px; background: var(--ink); color: var(--neon); font-family: var(--mono); font-size: 24px; font-weight: 600; padding: 10px 16px; border-radius: 14px; display:flex; gap: 10px; align-items:center; }
.chat { width: 78%; display:grid; gap: 12px; }
.chat i { display:block; height: 34px; border-radius: 16px 16px 16px 4px; background: var(--mint); }
.chat i:nth-child(2) { width: 70%; justify-self:end; background:#DDF8EC; border-radius: 16px 16px 4px 16px; }
.chat i:nth-child(3) { width: 85%; }
.sheet { width: 80%; display:grid; grid-template-columns: 1.6fr 1fr 1fr; gap: 0; border: 2px solid rgba(2,34,31,.15); border-radius: 6px; overflow:hidden; transform: rotate(-2deg); }
.sheet b { height: 34px; border-right: 1px solid rgba(2,34,31,.12); border-bottom: 1px solid rgba(2,34,31,.12); font: 500 18px var(--mono); color: var(--ink-3); display:flex; align-items:center; padding-left: 8px; }
.sql { width: 62%; }
.frm { width: 84%; display:grid; gap: 14px; justify-items:center; }
.frm .sheet { width: 100%; transform: none; grid-template-columns: 1.3fr .6fr .8fr; }
.sheet b.h { color: var(--ink); font-weight: 700; background: #F1F4F2; }
.sheet b.cur::after { content:""; width: 2px; height: 20px; background: var(--ink); margin-left: 4px; animation: blk 1s steps(1) infinite; }
@keyframes blk { 50% { opacity: 0; } }
.node .name small { display:block; font-size: 23px; font-weight: 500; color: var(--ink-3); margin-top: 4px; }
.xls { width: 84%; transform: rotate(-2deg); grid-template-columns: 1.4fr .8fr .8fr; }
.issues { margin-top: 56px; margin-bottom: auto; display:flex; gap: 22px; }
.issues div b { color: var(--ink); font-weight: 750; }
.issues div { font-size: 30px; padding: 16px 28px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px var(--line); color: var(--ink-2); }
''', '''
''' + prob(1) + '''
<h1 class="h1 r" style="--d:.1s;margin-top:18px">Every order is keyed in <span class="sig" style="--sd:4.4s">by hand</span></h1>
<div class="flow">
  <svg class="line" viewBox="0 0 1664 40" preserveAspectRatio="none">
    <path d="M220 20 H1444" stroke="rgba(2,34,31,.18)" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/>
    <circle r="12" fill="#00F5A9" stroke="#02221F" stroke-width="3"><animateMotion dur="3.6s" begin="0.6s" fill="freeze" path="M220 20 H1444" keyPoints="0;0;0.5;0.5;1" keyTimes="0;0.1;0.45;0.6;1" calcMode="spline" keySplines=".2 .8 .2 1;.2 .8 .2 1;.2 .8 .2 1;.2 .8 .2 1"/></circle>
  </svg>
  <div class="glass node r" style="--d:.3s"><div class="pic"><div class="chat"><i></i><i></i><i></i></div></div><div class="name">Order comes in<small>WhatsApp, PDF, phone call</small></div><div class="badge pop" style="--d:.9s">%s 80 a day</div></div>
  <div class="glass node r" style="--d:.45s"><div class="pic"><div class="frm"><img class="sql" src="../assets/sql-h.png" alt="SQL Account"><div class="sheet"><b class="h">Item code</b><b class="h">Qty</b><b class="h">UOM</b><b>BWG-CN-10</b><b>20</b><b>BAG</b><b>AYM-CC-8</b><b>8</b><b>EKOR</b><b class="cur">TP-25</b><b></b><b></b></div></div></div><div class="name">Keyed into SQL Account<small>Line by line, ~4 min an order</small></div><div class="badge pop" style="--d:2.4s">%s ×1</div></div>
  <div class="glass node r" style="--d:.6s"><div class="pic"><div class="sheet xls"><b class="h">Item</b><b class="h">Qty</b><b class="h">Bin</b><b>Bawang 10kg</b><b>20 bag</b><b>A3-02</b><b>Ayam cincang</b><b>8 ekor</b><b>Chiller</b><b class="cur">Tape 25mm</b><b></b><b></b></div></div><div class="name">Picking list into Excel<small>Again, ~2 min an order</small></div><div class="badge pop" style="--d:4.1s">%s ×2</div></div>
</div>
<div class="issues">
  <div class="r" style="--d:4.8s">80 orders &times; 6 min = <b>8 hours a day</b></div>
  <div class="r" style="--d:5s"><b>1 full-time person</b>, just typing</div>
  <div class="r" style="--d:5.2s">Typed twice: 2 chances for a mistake</div>
</div>
''' % (ic(CHAT, 24), ic(PEN, 24), ic(PEN, 24)),
"\"Follow one order once it is decoded. It comes in by WhatsApp, PDF or a phone call, about 80 a day in a typical distributor. Then a person keys it into SQL Account: new sales order, customer, then line by line, field by field: item code, quantity, unit, price. About 4 minutes an order.\n\nThen the store needs a picking list. The order is already in SQL Account, but in many companies someone types it again into Excel: item, quantity, which rack. Print, pick, pack. Another 2 minutes.\n\nAdd it up: 80 orders times 6 minutes is 8 hours a day. That is 1 full-time person who only types. And because the same order is typed twice, there are 2 chances for a wrong code or 10 pieces read as 10 cartons.\n\nYour books are right; SQL Account does its job. The trouble is all the typing around the books. It is nobody's fault; it is how the work was set up.\"\n\nDo: point at each card as you say it. Note: 80 orders, 4 and 2 minutes are an example; ask the room for theirs.\nNext: \"Problem two: the routine work.\"")

WARN_PATH = '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>'
# ---------------- Problem 2: routine work ----------------
ROUTINE = [('9:00', 'Check who is overdue'), ('9:30', 'WhatsApp 15 payment reminders'), ('11:00', 'Match bank slips to invoices'),
           ('2:00', 'Send statements to customers'), ('4:30', 'Check stock levels'), ('5:30', 'Put together the sales report')]
def _routine():
    out = ''
    for i, (t, job) in enumerate(ROUTINE):
        d = 1.0 + i * 0.5
        out += ('<div class="rw r" style="--d:' + '%.2f' % (0.5 + i * .12) + 's"><span class="cb"><i style="--d:' + '%.2f' % d + 's">' + ic(CHECK, 26, 3) + '</i></span>'
                '<b>' + t + '</b><span class="job">' + job + '</span></div>')
    return out
slide('07-problem-2', 'Problem 2: routine work', SEC[1], 'light', 'data-sparks="9,1" style="--gx:80%;--gy:50%;--mx:80%;--my:50%"', '''
.wrap { flex:1; display:grid; grid-template-columns: 1fr 760px; gap: 80px; align-items:center; }
.h1 { margin-top: 18px; }
.lead { margin-top: 24px; max-width: 760px; }
.loop { margin-top: 40px; display:inline-flex; align-items:center; gap: 14px; font-size: 30px; font-weight: 700; color: #B4451F; }
.loop svg { animation: spin 3s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.todo { padding: 30px 34px; border-radius: 28px; }
.todo h4 { font-family: var(--mono); font-size: 19px; letter-spacing: .12em; color: var(--ink-3); font-weight: 600; margin-bottom: 10px; }
.rw { display:grid; grid-template-columns: 44px 90px 1fr; align-items:center; gap: 14px; padding: 15px 0; border-bottom: 1px solid var(--line); }
.rw:last-child { border: 0; }
.rw b { font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--green); }
.rw .job { font-size: 30px; }
.cb { width: 36px; height: 36px; border-radius: 9px; border: 3px solid var(--ink); display:grid; place-items:center; }
.cb i { opacity: 0; transform: scale(.4); animation: tick .35s var(--spring) forwards; animation-delay: var(--d); color: var(--green); display:grid; }
@keyframes tick { to { opacity: 1; transform: none; } }
''', prob(2) + '''
<div class="wrap">
  <div>
    <h1 class="h1 r" style="--d:.1s">The same jobs, every day, by hand</h1>
    <p class="lead r" style="--d:.3s">Somebody in your office does this list every single day. Tomorrow, it starts again.</p>
    <div class="loop r" style="--d:4.3s">''' + ic('<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>', 34, 2.4) + '''Repeat tomorrow</div>
  </div>
  <div class="glass todo r" style="--d:.3s"><h4>TODAY&rsquo;S ROUTINE</h4>''' + _routine() + '''</div>
</div>
''',
"\"Problem two. Look at this list. Check who is overdue. Send fifteen payment reminders on WhatsApp. Match the bank slips to the invoices. Send statements. Check the stock. Put the sales report together. Somebody in your office does this every day. And tomorrow, the list starts again. None of it needs a decision. All of it needs a person, today.\"\n\nNext: \"Problem three is worse, because you don't see it.\"")

# ---------------- Problem 3: found too late ----------------
WEEKS = [9, 10, 9, 11, 10, 9, 10, 8, 6, 4, 2, 0, 0, 0, 0, 0]
def _late_chart():
    W, H, X0, Y0 = 1100, 380, 60, 330
    pts = [(X0 + i * (W - 2 * X0) / (len(WEEKS) - 1), Y0 - v * 26) for i, v in enumerate(WEEKS)]
    d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
    area = d + ' L%.1f %d L%.1f %d Z' % (pts[-1][0], Y0, pts[0][0], Y0)
    x_stop, x_seen = pts[8][0], pts[15][0]
    return ('<svg class="ch" viewBox="0 0 %d %d" fill="none">' % (W, H + 40) +
            '<path d="M%d %d H%d" stroke="rgba(242,251,247,.15)" stroke-width="2"/>' % (X0, Y0, W - X0) +
            '<rect class="f" style="--d:2.4s" x="%.1f" y="20" width="%.1f" height="%d" fill="rgba(255,138,91,.12)"/>' % (x_stop, x_seen - x_stop, Y0 - 20) +
            '<path class="f" style="--d:1.6s" d="%s" fill="url(#lg)"/>' % area +
            '<defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00F5A9" stop-opacity=".25"/><stop offset="1" stop-color="#00F5A9" stop-opacity="0"/></linearGradient></defs>'
            '<path class="draw" pathLength="1" style="--d:.5s;--dur:2s" d="%s" stroke="#00F5A9" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>' % d +
            '<g class="pop" style="--d:2.2s"><circle cx="%.1f" cy="%.1f" r="10" fill="#FF8A5B"/></g>' % pts[8] +
            '<g class="pop" style="--d:2.8s"><circle cx="%.1f" cy="%.1f" r="12" fill="#F2FBF7"/></g>' % pts[15] +
            '</svg>'), x_stop / W * 100, x_seen / W * 100
CH, XS, XN = _late_chart()
slide('07-problem-3', 'Problem 3: found too late', SEC[1], 'dark', 'data-sparks="9,1" style="--gx:70%;--gy:60%;--mx:70%;--my:60%"', '''
.h1 { margin-top: 18px; }
.box { position:relative; margin-top: 24px; padding: 22px 34px 14px; }
.box h4 { font-family: var(--mono); font-size: 19px; letter-spacing: .12em; color: var(--on-dark-3); font-weight: 600; }
.box h4 b { color: var(--on-dark); }
.ch { width: 100%; height: 470px; display:block; margin-top: 6px; }
.lb { position:absolute; transform: translateX(-50%); white-space: nowrap; font-size: 24px; font-weight: 700; padding: 8px 14px; border-radius: 12px; }
.lb.st { background: #FF8A5B; color: #1A0F0A; }
.lb.sn { background: #F2FBF7; color: var(--ink); }
.gap { position:absolute; transform: translateX(-50%); font-size: 26px; font-weight: 700; color: #FFB08F; white-space: nowrap; }
.also { display:flex; gap: 16px; margin-top: 26px; }
.also div { flex:1; display:flex; align-items:center; gap: 14px; font-size: 26px; padding: 18px 22px; border-radius: 18px; background: rgba(242,251,247,.05); border: 1px solid rgba(242,251,247,.1); color: var(--on-dark-2); }
.also b { color: var(--on-dark); }
.also svg { color: #FFB08F; flex: none; }
''', prob(3) + '''
<h1 class="h1 r" style="--d:.1s">By the time you see it, <span class="sig" style="--sd:2.6s">it&rsquo;s too late</span></h1>
<div class="glass box r" style="--d:.3s"><h4>EXAMPLE &nbsp;·&nbsp; <b>KEDAI AH SENG</b> &nbsp;·&nbsp; CARTONS ORDERED PER WEEK</h4>''' + CH + '''
  <span class="lb st pop" style="left:''' + '%.1f' % XS + '''%;top:170px;--d:2.3s">Stops ordering</span>
  <span class="lb sn pop" style="left:''' + '%.1f' % min(XN, 88) + '''%;top:390px;--d:2.9s">You notice</span>
  <span class="gap f" style="left:''' + '%.1f' % ((XS + XN) / 2) + '''%;top:62px;--d:3.1s">7 weeks of lost sales</span>
</div>
<div class="also">
  <div class="r" style="--d:3.3s">''' + ic('<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/>', 34) + '''<span><b>Stock runs out:</b> found when the customer calls</span></div>
  <div class="r" style="--d:3.45s">''' + ic('<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>', 34) + '''<span><b>Sales drop:</b> found in the month-end report</span></div>
</div>
''',
"\"Problem three: problems you find too late. This is a sample customer. Every week, nine or ten cartons. Then the orders get smaller, and then they stop. Maybe a competitor called him. Nobody in the office notices, because nobody is watching every customer every week. Seven weeks later someone asks, whatever happened to Ah Seng? By then he is gone. Same with stock: you find out it ran out when the customer calls. Same with sales: you see the drop in the month-end report, a month after it started.\"\n\nNote: sample data, say so.\nNext: \"Problem four: your stock figures.\"")

# ---------------- Problem 4: stock never right ----------------
P4_CAUSES = [
    ('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>', 'Manual Picking', 'Pick lists written by hand. Wrong item, wrong quantity, and nobody updates the system.'),
    ('<path d="M3 9.5L12 4l9 5.5V20H3z"/><path d="M8 20v-6h8v6"/>', 'No fixed shelf spot', 'Goods are left wherever there is space. Nobody records which shelf.'),
    ('<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4M8 11h6"/>', 'Stock cannot be found', 'It is in the warehouse, but nobody knows where. Staff spend hours searching.'),
    ('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/>', 'Oldest stock not sent first', 'New cartons go out first. The old ones sit at the back and expire.'),
    ('<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M8 10l8 4M16 10l-8 4"/>', 'UOM mixed up', '10 pieces keyed as 10 cartons. The numbers get more wrong every day.'),
    ('<path d="M4 5h16v11H9l-5 4z"/><path d="M9 9h6"/>', 'Typed in the next day', 'Goods move today, the system knows tomorrow. In between, every figure is wrong.'),
]
P4_COST = [('Promised stock you don&rsquo;t have', 'Angry customers, lost orders'), ('Expired stock thrown out', 'Money lost'),
           ('Hours lost searching', 'Staff walking, not picking'), ('Month-end stock count', 'The warehouse stops for a day')]
def _p4():
    c = ''.join('<div class="cz r" style="--d:%.2fs"><span class="ic">%s</span><div><b>%s</b><p>%s</p></div></div>' % (0.6 + i * .12, ic(p, 34), t, d) for i, (p, t, d) in enumerate(P4_CAUSES))
    k = ''.join('<div class="cs r" style="--d:%.2fs"><b>%s</b><span>%s</span></div>' % (1.5 + i * .1, a, b) for i, (a, b) in enumerate(P4_COST))
    return c, k
P4C, P4K = _p4()

slide('07-problem-4', 'Problem 4: stock never right', SEC[1], 'light', 'data-sparks="9,0" style="--gx:20%;--gy:50%;--mx:20%;--my:50%"', '''
.slide { padding-top: 84px; }
.h1 { margin-top: 14px; font-size: 66px; }
.wrap { flex:1; display:grid; grid-template-columns: 470px 1fr; gap: 34px; margin-top: 26px; }
.vs { display:grid; grid-template-rows: 1fr auto 1fr; gap: 10px; }
.sd { border-radius: 24px; padding: 20px 26px; display:flex; flex-direction:column; justify-content:center; }
.sd h4 { font-family: var(--mono); font-size: 17px; letter-spacing: .12em; font-weight: 700; color: var(--ink-3); }
.sd .n { font-size: 110px; font-weight: 750; letter-spacing: -.05em; line-height: 1; margin-top: 6px; }
.sd .n small { font-size: 34px; color: var(--ink-3); margin-left: 8px; letter-spacing: 0; }
.bk { background: var(--ink); color: var(--on-dark); } .bk h4, .bk .n small { color: var(--on-dark-3); }
.bk img { height: 28px; margin-top: 8px; align-self:flex-start; }
.crates { display:flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.crates i { width: 30px; height: 26px; border-radius: 5px; background: #D9B88C; box-shadow: inset 0 -5px 0 rgba(0,0,0,.12); }
.crates i.gh { background: transparent; box-shadow: inset 0 0 0 2px rgba(180,69,31,.35); }
.gap { display:flex; align-items:center; justify-content:center; gap: 12px; font-size: 40px; font-weight: 800; color: #B4451F; }
.gap span { font-size: 20px; letter-spacing: .1em; }
.rt h3 { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .12em; color: #B4451F; }
.cg { display:grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
.cz { display:grid; grid-template-columns: 60px 1fr; gap: 14px; align-items:start; padding: 16px 18px; border-radius: 18px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 16px 28px -22px rgba(2,34,31,.35); border-left: 5px solid #FF8A5B; }
.cz .ic { width: 60px; height: 60px; border-radius: 16px; background: rgba(255,138,91,.14); color: #B4451F; display:grid; place-items:center; }
.cz b { font-size: 28px; font-weight: 700; letter-spacing: -.01em; }
.cz p { font-size: 22px; color: var(--ink-2); line-height: 1.3; margin-top: 4px; }
.cost { display:grid; grid-template-columns: auto repeat(4, 1fr); gap: 12px; margin-top: 18px; align-items:stretch; }
.cost .lb { display:flex; align-items:center; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .12em; color: var(--ink-3); padding-right: 6px; }
.cs { padding: 14px 18px; border-radius: 16px; background: var(--ink); color: var(--on-dark); }
.cs b { display:block; font-size: 23px; font-weight: 700; line-height: 1.2; }
.cs span { display:block; font-size: 19px; color: #FFB08F; margin-top: 4px; }
''', prob(4) + '''
<h1 class="h1 r" style="--d:.1s">The system says 40. The shelf has 12.</h1>
<div class="wrap">
  <div class="vs">
    <div class="sd bk r" style="--d:.3s"><h4>SQL ACCOUNT SAYS</h4><div class="n"><span data-count="40" data-delay=".5">0</span><small>ctn</small></div><img src="../assets/sql-h-white.png" alt="SQL Account"></div>
    <div class="gap pop" style="--d:1.2s">&minus;28 <span>MISSING</span></div>
    <div class="glass sd r" style="--d:.45s"><h4>THE SHELF HAS</h4><div class="n"><span data-count="12" data-delay=".7">0</span><small>ctn</small></div><div class="crates">''' + '<i></i>' * 12 + '<i class="gh"></i>' * 8 + '''</div></div>
  </div>
  <div class="rt"><h3 class="f" style="--d:.5s">WHY IT HAPPENS</h3><div class="cg">''' + P4C + '''</div></div>
</div>
<div class="cost"><span class="lb f" style="--d:1.4s">WHAT IT COSTS</span>''' + P4K + '''</div>
''',
"\"Problem four: stock. SQL Account says forty cartons. Somebody walks to the shelf: twelve. Where did twenty-eight go? Here is what really happens in most warehouses.\n\nManual picking: picking is done on paper, so the wrong item or quantity goes out and nobody updates the system. There is no fixed shelf spot, so goods are left wherever there is space and nobody records which shelf. So stock cannot be found: it is in the warehouse, but nobody knows where. The oldest stock is not sent first, so the old cartons sit at the back and expire. UOM mixed up: pieces get keyed as cartons. And everything is typed in the next day.\n\nWhat does it cost? You promise stock you don't have. Expired stock is thrown out. Staff spend hours searching. And the warehouse stops for a day at every month-end count.\n\nHands up if your stock count never matches the system.\" (Pause.) \"If you don't trust the number, you can't let a person, or an AI, promise stock to a customer.\"\n\nNext: \"And problem 5, the one that hurts the most: cash.\"")

# ---------------- Problem 5: cash comes in late ----------------
CASH = [('DAY 0', 'Goods delivered', '', 0), ('DAY 3', 'Invoice typed and sent', 'Paperwork piles up', 1), ('DAY 33', 'Payment due', 'Customer forgets', 2), ('DAY 63', 'Money in the bank', 'Slip lost in the chat', 3)]
def _cash():
    out = ''
    for i, (dy, t, why, k) in enumerate(CASH):
        x = 60 + k * 440
        out += ('<div class="cs pop" style="left:' + str(x) + 'px;--d:' + '%.2f' % (0.8 + i * 0.5) + 's"><i' + (' class="end"' if i == 3 else '') + '></i>'
                '<b>' + dy + '</b><h3>' + t + '</h3>' + ('<span>' + why + '</span>' if why else '') + '</div>')
    return out
slide('07-problem-5', 'Problem 5: cash comes in late', SEC[1], 'dark', 'data-sparks="9,1" style="--gx:80%;--gy:40%;--mx:80%;--my:40%"', '''
.h1 { margin-top: 18px; }
.tl { position:relative; height: 360px; margin-top: 70px; }
.tl .rail { position:absolute; left: 60px; right: 284px; top: 20px; height: 6px; border-radius: 3px; background: rgba(242,251,247,.1); overflow:hidden; }
.tl .rail b { position:absolute; inset: 0; width: 0; background: linear-gradient(90deg, #00F5A9, #FFB547 40%, #FF8A5B); animation: rl 2.4s cubic-bezier(.4,0,.2,1) .7s forwards; }
@keyframes rl { to { width: 100%; } }
.cs { position:absolute; top: 0; width: 0; }
.cs i { position:absolute; left: -23px; top: 0; width: 46px; height: 46px; border-radius: 50%; background: var(--night); border: 5px solid #FFB547; }
.cs:first-of-type i { border-color: var(--neon); }
.cs i.end { border-color: #FF8A5B; background: #FF8A5B; box-shadow: 0 0 40px rgba(255,138,91,.6); }
.cs b { position:absolute; left: -23px; top: 70px; font-family: var(--mono); font-size: 26px; font-weight: 700; color: var(--neon); white-space: nowrap; }
.cs h3 { position:absolute; left: -23px; top: 108px; width: 330px; font-size: 38px; font-weight: 700; letter-spacing: -.02em; }
.cs span { position:absolute; left: -23px; top: 200px; white-space: nowrap; font-size: 24px; font-weight: 600; color: #FFB08F; background: rgba(255,138,91,.12); padding: 7px 13px; border-radius: 10px; }
.wait { font-size: 40px; font-weight: 700; margin-top: 10px; }
.wait em { font-style: normal; color: #FFB08F; }
''', prob(5) + '''
<h1 class="h1 r" style="--d:.1s">Delivered today. Paid 2 months later.</h1>
<div class="tl"><div class="rail"><b></b></div>''' + _cash() + '''</div>
<p class="wait r" style="--d:3.2s">Your money waits <em>63 days</em>, and you pay salaries in the meantime.</p>
''',
"\"Problem five: cash. The goods are delivered on day zero. The invoice is typed and sent on day three, because the office is behind. Payment is due a month later, and the customer forgets. Someone chases. The money arrives on day sixty-three, and the bank slip is sitting somewhere in a WhatsApp chat until somebody matches it. For two months, your money is in your customer's bank, and you are paying salaries and suppliers in the meantime.\"\n\nNote: sample timeline; use the room's real payment terms if you know them.\nNext: \"So what do all five problems cost you? Let's count it, with your own numbers.\"")

slide('07-count-your-number', 'Count your own number', SEC[1], 'light', 'data-sparks="9,0" style="--gx:78%;--gy:70%;--mx:70%;--my:70%"', '''
.slide { padding-top: 90px; }
.h1 { font-size: 70px; }
.lead { margin-top: 10px; font-size: 30px; }
.calc { flex:1; display:grid; grid-template-columns: 1.25fr 70px 1fr 70px 1fr 70px 1.35fr; align-items:stretch; margin-top: 40px; }
.op { display:grid; place-items:center; font-size: 64px; font-weight: 700; color: var(--ink-3); }
.st { padding: 26px 26px 24px; border-radius: 26px; display:flex; flex-direction:column; }
.st .k { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .12em; color: var(--green); }
.st h3 { font-size: 32px; font-weight: 700; letter-spacing: -.01em; margin-top: 8px; line-height: 1.15; }
.st .hint { font-size: 22px; color: var(--ink-3); margin-top: 6px; line-height: 1.3; }
.st .v { margin-top: auto; font-size: 62px; font-weight: 700; letter-spacing: -.03em; line-height: 1; }
.st .v small { font-size: 26px; font-weight: 600; color: var(--ink-3); margin-left: 6px; letter-spacing: 0; }
.jobs { margin: 14px 0 16px; display:grid; gap: 8px; }
.jobs div { display:flex; justify-content:space-between; font-size: 24px; padding: 8px 12px; border-radius: 10px; background: var(--mint); }
.jobs b { font-weight: 700; }
.res { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 80px rgba(0,245,169,.25); }
.res .k { color: var(--neon); } .res .hint { color: var(--on-dark-2); }
.res .v { color: var(--neon); font-size: 76px; }
.res .v small { color: var(--on-dark-2); }
.res .v small.yr { display:block; margin: 10px 0 0; font-size: 30px; }
.foot2 { display:flex; align-items:center; gap: 24px; margin-top: 26px; font-size: 26px; color: var(--ink-2); }
''', '''
<h1 class="h1 r" style="--d:.05s">What does manual work cost you a year?</h1>
<p class="lead r" style="--d:.2s">3 steps. Here is an example. Then do yours.</p>
<div class="calc">
  <div class="glass st r" style="--d:.4s"><span class="k">STEP 1</span><h3>Hours of manual work a week</h3><span class="hint">All staff added together</span>
    <div class="jobs"><div><span>Keying in orders</span><b>10 h</b></div><div><span>Chasing payments</span><b>8 h</b></div><div><span>Checking stock</span><b>7 h</b></div></div>
    <div class="v">25<small>hours</small></div></div>
  <span class="op f" style="--d:.8s">&times;</span>
  <div class="glass st r" style="--d:.9s"><span class="k">STEP 2</span><h3>Weeks in a year</h3><span class="hint">Every week, all year</span><div class="v">52<small>weeks</small></div></div>
  <span class="op f" style="--d:1.2s">&times;</span>
  <div class="glass st r" style="--d:1.3s"><span class="k">STEP 3</span><h3>Cost of 1 staff hour</h3><span class="hint">Salary plus EPF and SOCSO</span><div class="v">RM16</div></div>
  <span class="op f" style="--d:1.6s">=</span>
  <div class="st res r" style="--d:1.7s"><span class="k">YOUR NUMBER</span><h3>Money spent on typing and chasing</h3><span class="hint">25 &times; 52 &times; RM16</span>
    <div class="v">RM<span data-count="20800" data-delay="2" data-dur="1.6">0</span><small class="yr">a year</small></div></div>
</div>
<div class="foot2 r" style="--d:2.4s"><div class="ws" style="--d:2.4s">''' + ic(PEN, 30) + '''Work out your rough monthly staff cost and write it in your notes.</div></div>
''',
"\"Let's put a number on all five problems, your own number. Three steps.\n\nStep one: how many hours a week does your team spend on manual work, all staff added together? In my example: keying in orders ten hours, chasing payments eight, checking stock seven. Twenty-five hours a week.\n\nStep two: times fifty-two weeks in a year.\n\nStep three: times sixteen ringgit, roughly what one staff hour costs you with EPF and SOCSO.\n\nTwenty-five times fifty-two times sixteen: twenty thousand eight hundred ringgit a year, spent on typing and chasing. Now work out your rough monthly staff cost and write it in your notes.\"\n\nDo: one minute of silence. Coaches help with the sums.\nNote: RM16 an hour is a staff member at about RM3,400 a month all-in, over 208 working hours. Adjust for your audience.\nNext: \"The usual answer is to hire another clerk. That only puts more people on the same typing. Can an AI Agent fix it? Only if it has 1 thing: tools.\"")

AI_SECTION = '''
<div class="c">
  <div class="kicker r" style="--d:.1s">PART 1</div>
  <h1 class="big r" style="--d:.25s">What is <span class="g">AI</span>?</h1>
  <p class="lead r" style="--d:.5s">In plain words. No jargon.</p>
  <div class="ag">
    <div class="glass r" style="--d:.8s"><b>1</b><span>How AI grew up<em>rules to agents</em></span></div>
    <i class="f" style="--d:1s">ARR</i>
    <div class="glass r" style="--d:1.05s"><b>2</b><span>The brain<em>LLM</em></span></div>
    <i class="f" style="--d:1.25s">ARR</i>
    <div class="glass r" style="--d:1.3s"><b>3</b><span>The agent<em>brain + hands + loop</em></span></div>
  </div>
</div>
'''.replace('ARR', ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 34, 2.4))
# ================= batch A · slides 1-6 of "What is AI?" (minimal redesign) =================
AA_ARR = ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 34, 2.2)

# ---------------- 1 · section opener ----------------
AA_STEPS = [('Types of AI', 'the 5 you already use', '<path d="M3 20h4v-5h4v-5h4V5h6"/>'),
            ('The brain', 'what an LLM is, how it learned', '<path d="M12 5a3 3 0 00-5.9-.7A3 3 0 004 9a3 3 0 00.5 5.5A3 3 0 008 19a3 3 0 004 1V5z"/><path d="M12 5a3 3 0 015.9-.7A3 3 0 0120 9a3 3 0 01-.5 5.5A3 3 0 0116 19a3 3 0 01-4 1"/>'),
            ('The agent', 'a brain that does the work', '<rect x="5" y="8" width="14" height="11" rx="3"/><path d="M12 4v4M9 13h.01M15 13h.01M3 13v3M21 13v3"/>')]
slide('08-section-ai', 'Section: What is AI?', SEC[2], 'dark bare', 'data-sparks="none"', MIN_CSS + '''
.c { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.big { font-size: 220px; font-weight: 750; letter-spacing: -.055em; line-height: .95; margin-top: 26px; }
.big em { font-style: normal; color: var(--neon); }
.c .ml { margin-top: 26px; }
.path { position:relative; display:grid; grid-template-columns: repeat(3, 440px); margin-top: 110px; }
.path .ln { position:absolute; left: 220px; right: 220px; top: 47px; height: 2px; background: rgba(0,245,169,.45); }
.path .run { position:absolute; left: 220px; top: 41px; width: 14px; height: 14px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 18px 4px rgba(0,245,169,.6); animation: run 3.2s cubic-bezier(.6,0,.4,1) 1.8s infinite; opacity: 0; }
@keyframes run { 0% { transform: translateX(0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateX(866px); opacity: 0; } }
html.static .path .run { display: none; }
.path .st { position:relative; display:flex; flex-direction:column; align-items:center; }
.path i { font-style: normal; width: 96px; height: 96px; border-radius: 50%; display:grid; place-items:center; background: #03201C; border: 2px solid var(--neon); color: var(--neon); box-shadow: 0 0 40px rgba(0,245,169,.18); }
.path small { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .16em; color: var(--neon); margin-top: 22px; }
.path b { font-size: 40px; font-weight: 700; letter-spacing: -.015em; margin-top: 6px; }
.path span { font-size: 26px; color: var(--on-dark-2); margin-top: 6px; }
''', '''
<div class="c">
  <div class="mk u" style="--d:.1s">Part 1</div>
  <h1 class="big u" style="--d:.25s">What is <em>AI</em>?</h1>
  <div class="path">
    <div class="ln ug" style="--d:.9s"></div>
    <span class="run"></span>
    ''' + ''.join('<div class="st u" style="--d:%.2fs"><i>%s</i><small>STEP %d</small><b>%s</b><span>%s</span></div>' % (.7 + k * .35, ic(p, 42, 1.8), k + 1, t, s_) for k, (t, s_, p) in enumerate(AA_STEPS)) + '''
  </div>
</div>
''',
"\"So what is AI, really? Forget the headlines. We will go in 3 steps.\n\nOne: the 5 types of AI you already use every day. Two: the brain, the thing people call an LLM, and how much it read. Three: the agent, a brain that can actually do the work.\"\n\nNext: \"First, the 5 types of AI you already use.\"")

# ---------------- section page: Part 2 · the problem ----------------
_sa = next(x for x in S if x['file'] == '08-section-ai')
PB_STEPS = [('Tell us', 'your biggest problem', CHAT), ('Top 5 issues', 'what we hear most', LIST), ('Your number', 'what it costs you', COIN)]
slide('03-section-problem', 'Section: The problem', SEC[1], 'dark bare', 'data-sparks="none"', _sa['css'], '''
<div class="c">
  <div class="mk u" style="--d:.1s">Part 2</div>
  <h1 class="big u" style="--d:.25s">The <em>problem</em></h1>
  <div class="path">
    <div class="ln ug" style="--d:.9s"></div>
    <span class="run"></span>
    ''' + ''.join('<div class="st u" style="--d:%.2fs"><i>%s</i><small>STEP %d</small><b>%s</b><span>%s</span></div>' % (.7 + k * .35, ic(p, 42, 1.8), k + 1, t_, s_) for k, (t_, s_, p) in enumerate(PB_STEPS)) + '''
  </div>
</div>
''',
"\"That is SuDu. Now let's talk about you: the problems businesses like yours face every day. 3 steps.\n\nOne: you tell us your biggest problem, right now, on your phone. Two: the top 5 issues we hear most. Three: you put a number on what it costs you.\"\n\nNext: \"Take out your phone.\"")


# ---------------- section page: Part 4 · workshop ----------------
WK_STEPS = [('Find your group', 'by the number on your tag', '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>'),
            ('Meet your coach', '1 SuDu coach per group', HAND),
            ('Check your company', 'do you need WMS and MES?', CHECK)]
slide('23-section-workshop', 'Section: Workshop', SEC[5], 'dark bare', 'data-sparks="none"', _sa['css'], '''
<div class="c">
  <div class="mk u" style="--d:.1s">Part 4</div>
  <h1 class="big u" style="--d:.25s"><em>Workshop</em></h1>
  <div class="path">
    <div class="ln ug" style="--d:.9s"></div>
    <span class="run"></span>
    ''' + ''.join('<div class="st u" style="--d:%.2fs"><i>%s</i><small>STEP %d</small><b>%s</b><span>%s</span></div>' % (.7 + k * .35, ic(p, 42, 1.8), k + 1, t_, s_) for k, (t_, s_, p) in enumerate(WK_STEPS)) + '''
  </div>
</div>
''',
"\"Now it is your turn. This is the workshop part. 3 steps.\n\nOne: find your group, using the number on your name tag. Two: meet your coach; every group has 1 SuDu coach. Three: check your own company: do you need a WMS and an MES?\"\n\nNext: \"First, find your number.\"")

# ---------------- section page: live demo (7 parts) ----------------
DM_PARTS = ['Setting up', 'Sales', 'Inventory', 'Purchase', 'Collection', 'Up Sales', 'Finance']
slide('19-section-demo', 'Section: Live demo', SEC[3], 'dark bare', 'data-sparks="none"', _sa['css'] + '''
.dm { position:relative; display:grid; grid-template-columns: repeat(7, 220px); margin-top: 110px; }
.dm .ln { position:absolute; left: 110px; right: 110px; top: 35px; height: 2px; background: rgba(0,245,169,.45); }
.dm .st { position:relative; display:flex; flex-direction:column; align-items:center; }
.dm i { font-style: normal; width: 72px; height: 72px; border-radius: 50%; display:grid; place-items:center; background: #03201C; border: 2px solid var(--neon); color: var(--neon); font-family: var(--mono); font-size: 26px; font-weight: 700; box-shadow: 0 0 30px rgba(0,245,169,.18); }
.dm b { font-size: 30px; font-weight: 700; letter-spacing: -.01em; margin-top: 20px; }
.sub { font-size: 34px; color: var(--on-dark-2); margin-top: 26px; } .sub b { color: var(--on-dark); }
''', '''
<div class="c">
  <div class="mk u" style="--d:.1s">Part 3 &middot; SuDu AI</div>
  <h1 class="big u" style="--d:.25s">Live <em>demo</em></h1>
  <p class="sub u" style="--d:.45s"><b>1</b> sample company &middot; <b>6</b> AI Agents &middot; <b>7</b> parts</p>
  <div class="dm">
    <div class="ln ug" style="--d:.9s"></div>
    ''' + ''.join('<div class="st u" style="--d:%.2fs"><i>%d</i><b>%s</b></div>' % (.8 + k * .15, k + 1, n) for k, n in enumerate(DM_PARTS)) + '''
  </div>
</div>
''',
"\"Enough talking. Let me show you. This is a live demo on a sample company, Maju Jaya Foods, with sample data. 6 AI Agents, 7 parts: setting up, then sales, inventory, purchase, collection, up sales and finance. Watch what each agent does, and where it stops and asks a person.\"\n\nNext: \"First, meet the 6 AI Agents.\"")

# ---------------- imagine: the big vision, before SuDu (a Figure AI factory video plays after it) ----------------
IM_STEPS = [  # when, icon, title, line
    ('TODAY', '<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M12 3v4M9 12h.01M15 12h.01M9 16h6"/>', 'AI runs the office',
     'Orders, invoices, stock and payments, done by AI Agents.'),
    ('NEXT', '<path d="M12 3v3M8 6h8l1 5H7z"/><rect x="6" y="11" width="12" height="7" rx="2"/><path d="M9 18v3M15 18v3M4 13H2M22 13h-2"/>', 'AI walks the floor',
     'Physical AI: robots that pick, pack and build, next to your people.'),
    ('ONE DAY', '<path d="M12 2l2.4 5 5.6.8-4 3.9 1 5.5L12 14.6 7 17.2l1-5.5-4-3.9 5.6-.8z"/>', 'The company runs itself',
     'You set the goal. AI does the rest, and still asks you.'),
]
slide('14-imagine', 'Imagine', SEC[3], 'dark bare', 'data-sparks="none"', MIN_CSS + '''
.c { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.im { font-family: var(--mono); font-size: 24px; font-weight: 700; letter-spacing: .3em; text-transform: uppercase; color: var(--neon); }
.big { font-size: 112px; font-weight: 800; letter-spacing: -.045em; line-height: 1.02; margin-top: 26px; max-width: 1560px; text-wrap: balance; }
.big em { font-style: normal; background: linear-gradient(90deg, #00F5A9, #7CFFD6 50%, #00F5A9); -webkit-background-clip: text; background-clip: text; color: transparent;
  background-size: 200% 100%; animation: shine 5s linear 1.5s infinite; white-space: nowrap; }
@keyframes shine { to { background-position: -200% 0; } }
html.static .big em { animation: none; }
.tl { position:relative; display:grid; grid-template-columns: repeat(3, 480px); gap: 40px; margin-top: 90px; }
.tl .ln { position:absolute; left: 240px; right: 240px; top: 48px; height: 2px; background: linear-gradient(90deg, rgba(0,245,169,.6), rgba(0,245,169,.2)); }
.tl .run { position:absolute; left: 240px; top: 42px; width: 14px; height: 14px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 18px 4px rgba(0,245,169,.6); opacity: 0; animation: run 3.4s cubic-bezier(.6,0,.4,1) 3s infinite; }
@keyframes run { 0% { transform: translateX(0); opacity: 0; } 10%, 90% { opacity: 1; } 100% { transform: translateX(1040px); opacity: 0; } }
html.static .tl .run { display:none; }
.tl .st { position:relative; display:flex; flex-direction:column; align-items:center; }
.tl i { font-style: normal; width: 96px; height: 96px; border-radius: 50%; display:grid; place-items:center; background: #03201C; border: 2px solid var(--neon); color: var(--neon); box-shadow: 0 0 40px rgba(0,245,169,.2); }
.tl .st:last-child i { width: 110px; height: 110px; margin-top: -7px; background: var(--neon); color: #03201C; box-shadow: 0 0 70px rgba(0,245,169,.55); }
.tl small { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .18em; color: var(--neon); margin-top: 22px; }
.tl b { font-size: 40px; font-weight: 750; letter-spacing: -.02em; margin-top: 6px; }
.tl span { font-size: 26px; line-height: 1.38; color: var(--on-dark-2); margin-top: 8px; max-width: 420px; }
.end { margin-top: 80px; font-size: 38px; font-weight: 700; color: var(--on-dark); }
/* ---- cinematic layer ---- */
body { background: #010F0D; overflow: hidden; }
#warp { position:absolute; inset: 0; width: 100%; height: 100%; z-index: 0; }
.floor { position:absolute; left: -50%; right: -50%; bottom: 0; height: 46%; z-index: 0; transform: perspective(900px) rotateX(60deg); transform-origin: 50% 100%;
  background-image: linear-gradient(rgba(0,245,169,.28) 2px, transparent 2px), linear-gradient(90deg, rgba(0,245,169,.22) 2px, transparent 2px);
  background-size: 120px 120px; animation: flr 3.2s linear infinite, fin 2s ease .4s both;
  -webkit-mask-image: linear-gradient(to top, #000 0%, transparent 90%); mask-image: linear-gradient(to top, #000 0%, transparent 90%); }
@keyframes flr { to { background-position: 0 120px, 0 0; } }
@keyframes fin { from { opacity: 0; } to { opacity: .9; } }
.horizon { position:absolute; left: 0; right: 0; top: 52%; height: 260px; transform: translateY(-50%); z-index: 0; pointer-events:none;
  background: radial-gradient(50% 50% at 50% 50%, rgba(0,245,169,.22), transparent 70%); animation: fin 2.4s ease .3s both; }
.c { position:relative; z-index: 1; }
.vig { position:absolute; inset: 0; z-index: 0; pointer-events:none; background: radial-gradient(60% 55% at 50% 45%, rgba(1,15,13,.75), rgba(1,15,13,0) 75%); }
.im { animation: imIn 1.6s cubic-bezier(.2,.7,.2,1) .2s both; text-shadow: 0 0 24px rgba(0,245,169,.7); }
@keyframes imIn { from { opacity: 0; letter-spacing: 1.2em; filter: blur(10px); } to { opacity: 1; letter-spacing: .3em; filter: none; } }
.big { animation: focus 1.6s cubic-bezier(.2,.7,.2,1) .7s both; text-shadow: 0 10px 60px rgba(0,0,0,.5); }
@keyframes focus { from { opacity: 0; filter: blur(22px); transform: scale(1.12); } to { opacity: 1; filter: none; transform: none; } }
.big em { filter: drop-shadow(0 0 30px rgba(0,245,169,.35)); }
/* timeline */
.tl .st { opacity: 0; transform: translateY(30px) scale(.9); animation: stIn .9s cubic-bezier(.3,1.5,.5,1) forwards; animation-delay: var(--d); }
@keyframes stIn { to { opacity: 1; transform: none; } }
.tl i { position:relative; }
.tl i::before, .tl i::after { content:""; position:absolute; inset: -2px; border-radius: 50%; border: 2px solid var(--neon); opacity: 0; animation: pulse 2.6s ease-out infinite; animation-delay: calc(var(--d) + .9s); }
.tl i::after { animation-delay: calc(var(--d) + 2.2s); }
@keyframes pulse { 0% { transform: scale(1); opacity: .8; } 100% { transform: scale(1.9); opacity: 0; } }
.tl i svg { animation: bob 3.2s ease-in-out infinite; animation-delay: var(--d); }
@keyframes bob { 50% { transform: translateY(-5px); } }
.tl .st:last-child i { overflow: visible; }
.tl .rays { position:absolute; left: 50%; top: 48px; width: 360px; height: 360px; margin: -180px 0 0 -180px; border-radius: 50%; z-index: -1; pointer-events:none;
  background: repeating-conic-gradient(from 0deg, rgba(0,245,169,.22) 0 6deg, transparent 6deg 24deg);
  -webkit-mask-image: radial-gradient(circle, #000 18%, transparent 68%); mask-image: radial-gradient(circle, #000 18%, transparent 68%);
  opacity: 0; animation: rays 18s linear infinite, fin 1.6s ease forwards; animation-delay: 0s, calc(var(--d) + .6s); }
@keyframes rays { to { transform: rotate(360deg); } }
.tl .ln { transform-origin: left; transform: scaleX(0); animation: grow 2.4s cubic-bezier(.65,0,.25,1) 1.7s forwards; box-shadow: 0 0 12px rgba(0,245,169,.6); }
@keyframes grow { to { transform: none; } }
/* ending sweep */
.end { position:relative; opacity: 0; animation: stIn .9s cubic-bezier(.2,.7,.2,1) 3.4s forwards; }
.end em { position:relative; font-style: normal; background: linear-gradient(100deg, #00F5A9 40%, #FFFFFF 50%, #00F5A9 60%); background-size: 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: sweep 3.5s ease-in-out 4.2s infinite; }
@keyframes sweep { 0% { background-position: 100% 0; } 60%, 100% { background-position: 0 0; } }
html.static .floor, html.static .horizon { animation: none; opacity: .9; }
html.static .im, html.static .big, html.static .tl .st, html.static .end, html.static .tl .ln { animation: none; opacity: 1; filter: none; transform: none; }
html.static .tl .rays { animation: none; opacity: 1; }
html.static .tl i::before, html.static .tl i::after, html.static .tl i svg, html.static .end em { animation: none; }
html.static .end em { background-position: 0 0; }
''', '''
<canvas id="warp" width="1920" height="1080"></canvas>
<div class="horizon"></div>
<div class="floor"></div>
<div class="vig"></div>
<div class="c">
  <div class="im" style="--d:.2s">Imagine</div>
  <h1 class="big" style="--d:.6s">A day when AI <em>runs your whole company</em>.</h1>
  <div class="tl">
    <div class="ln ug" style="--d:1.6s"></div>
    <span class="run"></span>
    ''' + ''.join('<div class="st" style="--d:%.2fs">%s<i>%s</i><small>%s</small><b>%s</b><span>%s</span></div>' % (1.9 + k * .55, '<span class="rays"></span>' if k == 2 else '', ic(p, 46, 1.8), w, h, s_) for k, (w, p, h, s_) in enumerate(IM_STEPS)) + '''
  </div>
  <p class="end">Sounds far away? <em>It has already started.</em></p>
</div>
<script>
(function () {
  var cv = document.getElementById('warp'), x = cv.getContext('2d'), W = 1920, H = 1080, CX = W / 2, CY = H * .42;
  var STATIC = navigator.webdriver || location.hash === '#static' || document.documentElement.classList.contains('static');
  var N = 420, S = [];
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function star(s) { s.a = rnd(0, Math.PI * 2); s.r = rnd(4, 60); s.v = rnd(.6, 1.6); s.g = Math.random() < .25; return s; }
  for (var i = 0; i < N; i++) { var s = star({}); s.r = rnd(4, 1100); S.push(s); }
  var t0 = performance.now();
  function frame(now) {
    var t = (now - t0) / 1000;
    var warp = STATIC ? .04 : (t < .3 ? t / .3 : t < 2.4 ? 1 : Math.max(.03, 1 - (t - 2.4) / 1.4));   /* burst, then a slow cruise */
    x.fillStyle = 'rgba(1,15,13,' + (warp > .5 ? .28 : .6) + ')'; x.fillRect(0, 0, W, H);
    for (var i = 0; i < N; i++) {
      var s = S[i], r0 = s.r;
      s.r += s.v * (2 + s.r * .045) * (warp * 9 + .4);
      if (s.r > 1250) { star(s); r0 = s.r; }
      var c = Math.cos(s.a), sn = Math.sin(s.a);
      var al = Math.min(1, s.r / 500) * (.3 + .7 * Math.min(1, warp * 1.4));
      x.strokeStyle = s.g ? 'rgba(0,245,169,' + al + ')' : 'rgba(230,255,246,' + (al * .8) + ')';
      x.lineWidth = (s.g ? 2.2 : 1.4) * (.6 + .4 * Math.min(1, warp * 2));
      x.beginPath(); x.moveTo(CX + c * r0, CY + sn * r0 * .62); x.lineTo(CX + c * s.r, CY + sn * s.r * .62); x.stroke();
    }
    if (!STATIC) requestAnimationFrame(frame);
  }
  if (STATIC) { for (var k = 0; k < 40; k++) frame(t0 + k * 16); } else requestAnimationFrame(frame);
})();
</script>
''',
"(Slow down. Let the room picture it.)\n\n\"Let me ask you to imagine something. A day when AI runs your whole company.\n\nToday, AI Agents already run the office: they take the orders, make the invoices, watch the stock and chase the payments. You saw what that looks like.\n\nNext, AI walks onto the floor. Physical AI: robots that pick, pack and build, working next to your people.\n\nAnd one day, the company runs itself. You set the goal. AI does the rest, and it still asks you before the big decisions.\n\nSounds far away? It has already started. Watch this.\"\n\nNext: the video, F.03 at BMW.")

# ---------------- video: Figure AI F.03 at BMW (plays after "Imagine") ----------------
slide('14-video-figure', 'Video: F.03 at BMW', SEC[3], 'dark bare', 'data-sparks="none"', '''
body { background: #000; }
.slide { padding: 0 !important; }
.vw { position:absolute; inset: 0; background: #000; }
.vw video { width: 100%; height: 100%; object-fit: contain; display:block; cursor: pointer; }
.src { position:absolute; left: 48px; bottom: 36px; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; color: rgba(242,251,247,.6); text-transform: uppercase; }
body .deck-foot, body .foot { display:none !important; }
''', '''
<div class="vw"><video id="v" src="../assets/video/f03-bmw.mp4" playsinline preload="auto"></video></div>
<div class="src">Video: Figure AI &middot; F.03 at BMW</div>
<script>
(function () {
  var v = document.getElementById('v');
  var STATIC = navigator.webdriver || location.hash === '#static';
  if (STATIC) { v.addEventListener('loadedmetadata', function () { v.currentTime = Math.min(12, v.duration / 3); }); return; }
  function go() { var p = v.play(); if (p && p.catch) p.catch(function () { v.muted = true; v.play(); }); }
  if (v.readyState >= 2) go(); else v.addEventListener('canplay', go, { once: true });
  v.addEventListener('click', function () { if (v.muted) { v.muted = false; return; } v.paused ? v.play() : v.pause(); });
})();
</script>
''',
"(The video plays: about 1 minute, Figure AI's F.03 robot working on the BMW factory floor. Let it run. Do not talk over it.)\n\n\"That is not a movie. That is a real robot, in a real car factory, today.\"\n\nDo: click the video to pause or play. If it starts with no sound, click it once to turn the sound on.\nNext: \"That is where the world is going. And that is exactly what SuDu is building.\"")


# ---------------- section page: frequently asked questions (before FAQ 1 and FAQ 2) ----------------
FQ = [('I already have SQL Account.', 'Why do I still need SuDu AI?'), ('Can I just connect Claude or Codex', 'straight to SQL Account?')]
slide('24-faq', 'Frequently asked questions', SEC[3], 'dark bare', 'data-sparks="none"', _sa['css'] + '''
.fq { display:grid; grid-template-columns: repeat(2, 640px); gap: 60px; margin-top: 100px; }
.fq > div { position:relative; text-align:left; padding: 34px 38px; border-radius: 30px; background: rgba(242,251,247,.05); box-shadow: inset 0 0 0 1px rgba(0,245,169,.3), 0 0 50px rgba(0,245,169,.08); }
.fq small { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .18em; color: var(--neon); }
.fq b { display:block; font-size: 40px; font-weight: 750; letter-spacing: -.015em; line-height: 1.22; margin-top: 12px; color: var(--on-dark); }
.fq .qm { position:absolute; right: 26px; top: 6px; font-size: 120px; font-weight: 800; line-height: 1; color: transparent; -webkit-text-stroke: 1.5px rgba(0,245,169,.3); }
''', '''
<div class="c">
  <div class="mk u" style="--d:.1s">Before the demo</div>
  <h1 class="big u" style="--d:.25s;font-size:150px">Frequently asked <em>questions</em></h1>
  <div class="fq">''' + ''.join('<div class="u" style="--d:%.2fs"><span class="qm">?</span><small>FAQ %d</small><b>&ldquo;%s<br>%s&rdquo;</b></div>' % (.8 + k * .3, k + 1, a, b) for k, (a, b) in enumerate(FQ)) + '''</div>
</div>
''',
"\"Before the demo, let me answer the 2 questions I get asked the most, at every seminar.\n\nOne: I already have SQL Account, why do I still need SuDu? Two: can I just connect Claude or Codex straight to SQL Account?\"\n\nNext: \"Question 1.\"")
# ---------------- 2 · 70 years of AI ----------------
AA_HIST = [('1950s&ndash;80s', 'Rules', 'People wrote every rule by hand.'),
           ('2000s', 'Machine learning', 'It learns patterns from past examples.'),
           ('2012', 'Deep learning', 'It learns to see photos and hear voices.'),
           ('2018&ndash;20', 'LLM', 'It learns to write like a person.'),
           ('2025', 'AI agents', 'It uses tools and gets work done.')]
AA_ERA = [  # year, name, "think of it like", how it works, well-known, in your company, limit
    ('1950s&ndash;80s', 'Rules', 'Like a recipe book. The computer follows every step exactly.',
     'People write every rule by hand: <b>if this, then that</b>.', ['Excel formulas', 'Credit-limit check', 'Expert systems'],
     'Block an order over the credit limit', 'A new situation with no rule? It is stuck.'),
    ('2000s', 'Machine learning', 'Like a clerk who has seen 10,000 invoices and just knows who pays late.',
     'Show it <b>past data</b>. It finds the pattern by itself.', ['Spam filter', 'Credit score', '&ldquo;You may also like&rdquo;'],
     'Predict who will pay late', 'Needs neat tables. 1 model answers 1 question.'),
    ('2012', 'Deep learning', 'Like a child who learns what a cat is by seeing 1,000 cats.',
     'Many <b>layers</b> learn from millions of photos and sounds.', ['Face unlock', 'Siri', 'Google Translate'],
     'Read a handwritten order or a bank slip', 'Each model does only 1 job.'),
    ('2018&ndash;20', 'LLM', 'Like your phone&rsquo;s autocomplete, but it read the whole internet.',
     'It predicts <b>the next word</b>, again and again.', ['ChatGPT', 'Claude', 'Gemini', 'DeepSeek'],
     'Reply to emails, summarise a PDF', 'It only talks. It can&rsquo;t act.'),
    ('2025', 'AI agents', 'Like a new staff member: reads the order, opens the system, does the job, asks you.',
     'An LLM with <b>tools</b>, working in a loop until done.', ['Claude Code', 'OpenAI Codex'],
     'WhatsApp order &rarr; Sales Order', 'A person still approves.'),
]
AA_LOGO = {'ChatGPT': 'openai.svg', 'Claude': 'claude.svg', 'Claude Code': 'claude.svg', 'OpenAI Codex': 'openai.svg'}
AA_TICK = '<path d="M-7 0 l5 5 l10 -10" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
AA_ILL = [
# ---- 1 · rules: an order travels through a hand-written flowchart and gets blocked
'''<svg class="il" viewBox="0 0 640 440">
<g class="a" style="--t:.5s"><rect x="10" y="185" width="150" height="70" rx="14" fill="#fff" stroke="#02221F" stroke-width="3"/><text x="85" y="228" class="t1">New order</text></g>
<path class="dl" style="--t:.8s" pathLength="1" d="M160 220 H232"/>
<g class="a" style="--t:1s"><polygon points="330,120 430,220 330,320 230,220" fill="#E6F6EE" stroke="#02221F" stroke-width="3"/>
<text x="330" y="212" class="t1">Over credit</text><text x="330" y="240" class="t1">limit?</text></g>
<path class="dl" style="--t:1.3s" pathLength="1" d="M430 220 L470 100"/><path class="dl" style="--t:1.3s" pathLength="1" d="M430 220 L470 340"/>
<g class="a" style="--t:1.5s"><rect class="bk" x="470" y="70" width="160" height="60" rx="12" fill="#FFF1DC" stroke="#FFB547" stroke-width="3"/><text x="550" y="108" class="t1">Block order</text>
<rect x="470" y="310" width="160" height="60" rx="12" fill="#E6F6EE" stroke="#00A57A" stroke-width="3"/><text x="550" y="348" class="t1">Approve</text>
<text x="436" y="150" class="t2">Yes</text><text x="436" y="300" class="t2">No</text></g>
<g class="a" style="--t:1.7s"><rect x="40" y="392" width="560" height="40" rx="8" fill="#F1F2F0"/><text x="320" y="419" class="t3m">RULE 12: IF order &gt; credit limit THEN block</text></g>
<g class="tok"><rect x="-58" y="-19" width="116" height="38" rx="19" fill="#02221F"/><text x="0" y="7" class="t4">RM 6,000</text>
<animateMotion begin="indefinite" dur="2.4s" fill="freeze" keyPoints="0;.18;.5;1" keyTimes="0;.25;.55;1" calcMode="spline" keySplines=".4 0 .2 1;.4 0 .2 1;.4 0 .2 1" path="M85 160 L85 160 L330 160 L550 46"/></g>
</svg>''',
# ---- 2 · machine learning: past customers appear, it draws a line, a new customer is predicted
'''<svg class="il" viewBox="0 0 640 440">
<path class="dl" style="--t:.4s" pathLength="1" d="M60 380 H620 M60 380 V40"/>
<text x="620" y="406" class="t3" text-anchor="end">paid late before &rarr;</text>
<g class="a" style="--t:.5s"><circle cx="80" cy="22" r="8" fill="#00A57A"/><text x="96" y="29" class="t3s">paid on time</text><circle cx="250" cy="22" r="8" fill="#FFB547"/><text x="266" y="29" class="t3s">paid late</text></g>
''' + ''.join('<circle class="p" style="--t:%.2fs" cx="%d" cy="%d" r="11" fill="%s"/>' % (.7 + k * .07, x, y, c) for k, (x, y, c) in enumerate([
    (110, 330, '#00A57A'), (160, 290, '#00A57A'), (130, 240, '#00A57A'), (210, 340, '#00A57A'), (240, 270, '#00A57A'), (180, 190, '#00A57A'), (280, 330, '#00A57A'), (110, 150, '#00A57A'), (220, 120, '#00A57A'),
    (430, 140, '#FFB547'), (480, 190, '#FFB547'), (525, 125, '#FFB547'), (570, 150, '#FFB547'), (450, 240, '#FFB547'), (540, 250, '#FFB547'), (590, 210, '#FFB547'), (400, 180, '#FFB547')])) + '''
<path class="dl" style="--t:2s" pathLength="1" d="M300 50 L400 380" stroke-dasharray="1" fill="none"/>
<text class="a t3" style="--t:2.4s" x="250" y="420" text-anchor="start">&uarr; the pattern it found</text>
<g class="drop"><circle cx="520" cy="320" r="17" fill="#02221F"/><circle class="ring" cx="520" cy="320" r="30" fill="none" stroke="#02221F" stroke-width="2.5"/></g>
<g class="a" style="--t:3.4s"><path d="M520 300 L520 92" stroke="#02221F" stroke-width="2" stroke-dasharray="4 5"/>
<rect x="400" y="48" width="230" height="44" rx="22" fill="#02221F"/><text x="515" y="77" class="t4">Kedai Ali: 80% late</text></g>
</svg>''',
# ---- 3 · deep learning: a scan sweeps the photo, the layers light up, it names what it sees
'''<svg class="il" viewBox="0 0 640 440"><defs><linearGradient id="ph3" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#EEF1EC"/><stop offset="1" stop-color="#D5E0D8"/></linearGradient>
<linearGradient id="sc3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00F5A9" stop-opacity="0"/><stop offset=".85" stop-color="#00F5A9" stop-opacity=".55"/><stop offset="1" stop-color="#00F5A9"/></linearGradient>
<clipPath id="cp3"><rect x="20" y="40" width="380" height="340" rx="18"/></clipPath></defs>
<g class="a" style="--t:.4s"><rect x="20" y="40" width="380" height="340" rx="18" fill="url(#ph3)"/><rect x="20" y="320" width="380" height="60" fill="#C5D1C8" clip-path="url(#cp3)"/>
<path d="M110 175 L230 148 L330 175 L210 205 Z" fill="#E7C996" stroke="#8A6A3A" stroke-width="2.5"/>
<path d="M110 175 L210 205 L210 320 L110 288 Z" fill="#D9B27A" stroke="#8A6A3A" stroke-width="2.5"/>
<path d="M210 205 L330 175 L330 288 L210 320 Z" fill="#C99B5E" stroke="#8A6A3A" stroke-width="2.5"/>
<path d="M160 162 L280 188" stroke="#B9874C" stroke-width="12"/><path d="M255 228 l20 16 l-14 12 l22 20" stroke="#5B3E1A" stroke-width="3.5" fill="none"/>
<text x="210" y="368" class="t3">camera photo</text></g>
<g clip-path="url(#cp3)"><rect class="scan" x="20" y="-40" width="380" height="80" fill="url(#sc3)"/></g>
<rect class="dl box" style="--t:2.3s" pathLength="1" x="90" y="130" width="262" height="210" rx="6" fill="none"/>
<g class="a" style="--t:2.6s"><rect x="90" y="88" width="262" height="38" rx="8" fill="#FFB547"/><text x="221" y="114" class="t5">Damaged carton &middot; 94%</text></g>
''' + ''.join('<line x1="%d" y1="%d" x2="%d" y2="%d" class="wl" style="--t:%.2fs"/>' % (x1, y1, x2, y2, t) for x1, x2, t, ys1, ys2 in [(450, 520, 1.1, (100, 170, 240, 310), (100, 170, 240, 310)), (520, 590, 1.5, (100, 170, 240, 310), (170, 240))] for y1 in ys1 for y2 in ys2) + ''.join('<circle class="nn" style="--t:%.2fs" cx="%d" cy="%d" r="15"/>' % (t, x, y) for x, t, ys in [(450, .9, (100, 170, 240, 310)), (520, 1.3, (100, 170, 240, 310))] for y in ys) + '''
<circle class="nn" style="--t:1.7s" cx="590" cy="170" r="15"/><circle class="nn hot" style="--t:1.9s" cx="590" cy="240" r="15"/>
<text x="590" y="146" class="t3s2">OK</text><text x="590" y="280" class="t3s2 h">Damaged</text>
<text x="520" y="368" class="t3">many layers</text>
</svg>''',
# ---- 4 · LLM: it writes the reply 1 word at a time, choosing the most likely next word
'''<svg class="il" viewBox="0 0 640 440">
<g class="a" style="--t:.4s"><rect x="250" y="20" width="370" height="62" rx="22" fill="#02221F"/><text x="435" y="59" class="t6">Can you deliver tomorrow?</text></g>
<g class="a" style="--t:.8s"><rect x="20" y="110" width="520" height="70" rx="22" fill="#fff" stroke="#DDE3DF" stroke-width="2"/></g>
''' + ''.join('<text class="a w" style="--t:%.2fs" x="%d" y="155">%s</text>' % (1.0 + k * .25, x, w) for k, (x, w) in enumerate([(46, 'Yes,'), (110, 'we'), (158, 'can'), (212, 'deliver')])) + '''
<g class="a" style="--t:3.4s"><rect x="300" y="128" width="130" height="36" rx="8" fill="#E6F6EE"/><text class="w g" x="310" y="155">tomorrow</text></g>
<rect class="cur" x="306" y="128" width="3" height="34" fill="#006C48"/>
<text class="a t3m2" style="--t:2s" x="20" y="232">NEXT WORD?</text>
''' + ''.join('<g class="a" style="--t:%.2fs"><text x="20" y="%d" class="t7%s">%s</text><rect class="bar" style="--t:%.2fs" x="200" y="%d" width="%d" height="20" rx="10" fill="%s"/><text x="%d" y="%d" class="t3s">%d%%</text></g>' % (2.1 + k * .15, 280 + k * 50, ' g' if k == 0 else '', w, 2.3 + k * .15, 265 + k * 50, p * 4, '#006C48' if k == 0 else '#C9D4CC', 214 + p * 4, 281 + k * 50, p) for k, (w, p) in enumerate([('tomorrow', 82), ('later', 9), ('soon', 6)])) + '''
<path class="dl" style="--t:3s" pathLength="1" d="M600 262 C 630 220, 610 150, 440 146" stroke="#006C48" stroke-width="2.5" fill="none" stroke-dasharray="1"/>
</svg>''',
# ---- 5 · agents: it goes round the loop, using 1 tool after another, then asks you
'''<svg class="il" viewBox="0 0 640 440">
<circle class="dl" style="--t:.4s" pathLength="1" cx="320" cy="220" r="150" fill="none" stroke="#00A57A" stroke-width="3"/>
<g class="a" style="--t:.6s"><circle cx="320" cy="220" r="72" fill="#02221F"/><text x="320" y="214" class="t8">LLM</text><text x="320" y="244" class="t9">+ tools</text></g>
''' + ''.join('<g class="a" style="--t:%.2fs"><circle cx="%d" cy="%d" r="42" fill="#fff" stroke="#02221F" stroke-width="2.5"/><g transform="translate(%d %d) scale(1.6)" fill="none" stroke="#006C48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</g>'
              '<text x="%d" y="%d" class="t3s2">%s</text><g transform="translate(%d %d)"><g class="ok" style="--t:%.2fs"><circle r="15" fill="#00A57A"/>%s</g></g></g>'
              % (.8 + k * .1, x, y, x - 19, y - 19, p, lx, ly, t, x + 32, y - 30, 1.3 + k * .8, AA_TICK) for k, (x, y, p, t, lx, ly) in enumerate([
                  (320, 70, '<path d="M4 5h16v11H9l-5 4z"/>', '1 Read WhatsApp', 320, 20),
                  (470, 220, '<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/>', '2 Check stock', 560, 290),
                  (320, 370, '<path d="M6 3h8l4 4v14H6z"/><path d="M9 13h6M9 17h4"/>', '3 Draft Sales Order', 320, 434),
                  (170, 220, '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>', '4 You approve', 80, 290)])) + '''
<g class="tok"><circle r="13" fill="#00F5A9" stroke="#02221F" stroke-width="3"/>
<animateMotion begin="indefinite" dur="3.2s" fill="freeze" path="M320 70 A150 150 0 1 1 319.9 70"/></g>
</svg>''',
]
def _aa_cards():
    out = ''
    for k, (yr, nm, like, how, ex, use, lim) in enumerate(AA_ERA):
        chips = ''.join('<span>%s%s</span>' % (('<img src="../assets/logos/%s" alt="">' % AA_LOGO[x]) if x in AA_LOGO else '', x) for x in ex)
        dots = ''.join('<i class="%s"></i>' % ('on' if j == k else '') for j in range(5))
        out += ('<div class="dt" data-k="%d"><div class="fl"><div class="card">'
                '<div class="stage">%s</div>'
                '<div class="tx"><div class="top"><small>%s</small><span class="dots">%s</span></div><h2>%s</h2>'
                '<div class="like"><small>THINK OF IT LIKE</small><p>%s</p></div>'
                '<p class="how">%s</p>'
                '<div class="rw"><small>WELL-KNOWN</small><div class="chips">%s</div></div>'
                '<div class="rw"><small>IN YOUR COMPANY</small><p class="use">%s</p></div>'
                '<p class="lim">%s</p></div></div></div></div>'
                % (k + 1, AA_ILL[k], yr, dots, nm, like, how, chips, use, lim))
    return out
AA_CARD_CSS = '''/* ---- 3D card stage ---- */
.stg { position:absolute; left: 128px; right: 128px; top: 312px; bottom: 104px; perspective: 2200px; perspective-origin: 50% 30%; pointer-events: none; }
.dt { position:absolute; inset: 0; transform-style: preserve-3d; opacity: 0; transform: translate3d(70%, 40px, -700px) rotateY(-62deg);
  transition: transform 1.15s cubic-bezier(.2,.75,.12,1), opacity .7s ease; will-change: transform, opacity; }
.dt.past { transform: translate3d(-70%, 40px, -700px) rotateY(62deg); }
.dt.on { opacity: 1; transform: translate3d(0, 0, 0) rotateX(7deg) rotateY(-5deg); }
.fl { position:absolute; inset: 0; transform-style: preserve-3d; }
.dt.on .fl { animation: flt 7s ease-in-out 1.2s infinite; }
@keyframes flt { 50% { transform: rotateY(3deg) rotateX(-2deg) translateY(-6px); } }
.card { position:absolute; inset: 0; transform-style: preserve-3d; display:grid; grid-template-columns: 720px 1fr; gap: 50px; align-items:center; padding: 30px 50px 30px 34px;
  border-radius: 34px; background: linear-gradient(160deg, #FFFFFF 0%, #F7FBF9 100%); box-shadow: 0 0 0 1px rgba(2,34,31,.08), 0 70px 120px -50px rgba(2,34,31,.55), 0 30px 50px -40px rgba(2,34,31,.4); }
.card::after { content:""; position:absolute; left: 6%; right: 6%; bottom: -46px; height: 40px; border-radius: 50%; background: radial-gradient(rgba(2,34,31,.28), transparent 70%); transform: translateZ(-40px); }
.stage { position:relative; height: 100%; display:grid; place-items:center; border-radius: 24px; background: radial-gradient(120% 90% at 50% 100%, #E6F6EE 0%, rgba(230,246,238,0) 70%); transform: translateZ(28px); }
.tx { transform: translateZ(14px); }
.tx .top { display:flex; align-items:center; justify-content:space-between; }
.tx .top small { font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--green); }
.dots { display:flex; gap: 8px; } .dots i { width: 12px; height: 12px; border-radius: 50%; background: #DCE3DF; } .dots i.on { background: var(--green); width: 34px; border-radius: 6px; }
.tx h2 { font-size: 66px; font-weight: 800; letter-spacing: -.035em; line-height: 1; margin-top: 8px; }
.like { margin-top: 20px; padding: 16px 22px; border-radius: 18px; background: var(--mint); }
.like small, .rw small { display:block; font-family: var(--mono); font-size: 17px; font-weight: 700; letter-spacing: .14em; color: var(--green); }
.like p { font-size: 29px; line-height: 1.32; font-weight: 600; color: var(--ink); margin-top: 4px; }
.how { font-size: 27px; line-height: 1.35; color: var(--ink-2); margin-top: 18px; } .how b { color: var(--ink); }
.rw { margin-top: 16px; } .rw small { color: var(--ink-3); }
.chips { display:flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.chips span { display:flex; align-items:center; gap: 8px; font-size: 22px; font-weight: 650; padding: 6px 14px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px var(--line); }
.chips img { width: 22px; height: 22px; }
.use { font-size: 27px; font-weight: 700; color: var(--green); margin-top: 6px; }
.lim { margin-top: 16px; font-size: 23px; color: #8A3417; padding-left: 14px; border-left: 3px solid #FFB547; }
.tx > * { opacity: 0; transform: translateY(16px); }
.dt.go .tx > * { animation: tin .7s cubic-bezier(.2,.7,.2,1) forwards; }
''' + ''.join('.dt.go .tx > :nth-child(%d) { animation-delay: %.2fs; }\n' % (n, .45 + n * .12) for n in range(1, 8)) + '''
@keyframes tin { to { opacity: 1; transform: none; } }
/* ---- scene parts: play when the card arrives (.go) ---- */
.il { width: 650px; height: 447px; overflow: visible; }
.il text { font-family: var(--sans); text-anchor: middle; }
.il .t1 { font-size: 23px; font-weight: 700; fill: #02221F; } .il .t2 { font-size: 21px; font-weight: 700; fill: #3A4F48; }
.il .t3 { font-size: 19px; font-weight: 600; fill: #4F635C; } .il .t3s { font-size: 19px; font-weight: 600; fill: #4F635C; text-anchor: start; }
.il .t3s2 { font-size: 20px; font-weight: 700; fill: #3A4F48; } .il .t3s2.h { fill: #B4451F; }
.il .t3m, .il .t3m2 { font-family: var(--mono); font-size: 17px; font-weight: 700; fill: #3A4F48; letter-spacing: .04em; } .il .t3m2 { text-anchor: start; fill: #006C48; letter-spacing: .12em; }
.il .t4 { font-size: 20px; font-weight: 700; fill: #00F5A9; } .il .t5 { font-size: 20px; font-weight: 800; fill: #02221F; }
.il .t6 { font-size: 23px; font-weight: 600; fill: #F2FBF7; } .il .w { font-size: 27px; font-weight: 600; fill: #02221F; text-anchor: start; } .il .w.g { fill: #006C48; font-weight: 800; }
.il .t7 { font-size: 24px; font-weight: 600; fill: #02221F; text-anchor: start; } .il .t7.g { fill: #006C48; font-weight: 800; }
.il .t8 { font-size: 32px; font-weight: 800; fill: #00F5A9; } .il .t9 { font-size: 19px; font-weight: 600; fill: #A9C4BA; }
.il .dl { stroke: #02221F; stroke-width: 3; fill: none; stroke-dasharray: 1; stroke-dashoffset: 1; }
.il .box.dl { stroke: #FFB547; stroke-width: 4; }
.dt.go .il .dl { animation: drw 1s ease forwards; animation-delay: var(--t); }
@keyframes drw { to { stroke-dashoffset: 0; } }
.il .a, .il .p, .il .ok, .il .nn, .il .wl { opacity: 0; }
.dt.go .il .a { animation: ain .6s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--t); }
@keyframes ain { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.il .p, .il .ok { transform-box: fill-box; transform-origin: center; }
.dt.go .il .p, .dt.go .il .ok { animation: pin .45s cubic-bezier(.3,1.6,.5,1) forwards; animation-delay: var(--t); }
@keyframes pin { from { opacity: 0; transform: scale(0); } to { opacity: 1; transform: scale(1); } }
.il .tok { opacity: 0; } .dt.go .il .tok { opacity: 1; transition: opacity .3s .5s; }
.dt.go .il .bk { animation: blk .5s ease 3s 2 alternate; }
@keyframes blk { to { fill: #FFB547; } }
.il .drop { opacity: 0; transform: translateY(-260px); } .dt.go .il .drop { animation: drp .8s cubic-bezier(.5,0,.6,1.5) 2.7s forwards; }
@keyframes drp { to { opacity: 1; transform: none; } }
.il .ring { transform-box: fill-box; transform-origin: center; animation: rng 1.6s ease-out infinite; }
@keyframes rng { 0% { transform: scale(.6); opacity: 1; } 100% { transform: scale(1.5); opacity: 0; } }
.il .scan { opacity: 0; } .dt.go .il .scan { animation: scn 1.3s ease-in-out .6s 2 forwards; }
@keyframes scn { 0% { opacity: 1; transform: translateY(0); } 100% { opacity: 1; transform: translateY(380px); } }
.il .nn { fill: #DCE3DF; transition: fill .4s; } .il .wl { stroke: #00A57A; stroke-width: 1.5; }
.dt.go .il .nn { animation: nlit .5s ease forwards; animation-delay: var(--t); }
@keyframes nlit { to { opacity: 1; fill: #00A57A; } }
.dt.go .il .nn.hot { animation-name: nhot; } @keyframes nhot { to { opacity: 1; fill: #FFB547; } }
.dt.go .il .wl { animation: wlit .5s ease forwards; animation-delay: var(--t); } @keyframes wlit { to { opacity: .35; } }
.il .bar { transform-box: fill-box; transform-origin: left; transform: scaleX(0); } .dt.go .il .bar { animation: bgr .9s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--t); }
@keyframes bgr { to { transform: none; } }
.il .cur { opacity: 0; } .dt.go .il .cur { animation: cur .5s steps(1) 2s 3 forwards; } @keyframes cur { 0% { opacity: 1; } 50% { opacity: 0; } }
'''
slide('08-ai-history', '70 years of AI', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.tl { margin-top: 56px; transform-origin: 50% 0; transition: transform 1.1s cubic-bezier(.2,.75,.15,1), opacity .9s ease; }
body:not([data-s="0"]) .tl { transform: translateY(-14px) scale(.94); opacity: .22; }
.row { position:relative; display:grid; grid-template-columns: repeat(5, 1fr); gap: 28px; }
.row .ln { position:absolute; left: 0; right: 120px; top: 13px; height: 2px; background: var(--ink); opacity: .85; }
.row .ln.ug { animation-duration: 2.2s; }
.st i { display:block; width: 28px; height: 28px; border-radius: 50%; background: #FAFAF7; border: 3px solid var(--ink); }
.st small { display:block; font-family: var(--mono); font-size: 22px; font-weight: 700; color: var(--green); margin-top: 26px; }
.st b { display:block; white-space: nowrap; font-size: 37px; font-weight: 750; letter-spacing: -.02em; line-height: 1.1; margin-top: 8px; }
.st p { font-size: 26px; line-height: 1.38; color: var(--ink-2); margin-top: 10px; }
.st.now i { background: var(--green); border-color: var(--green); box-shadow: 0 0 0 8px rgba(0,108,72,.15); }
.st.now b { color: var(--green); }
.st em { display:inline-block; font-style: normal; font-size: 20px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #fff; background: var(--green); padding: 6px 12px; border-radius: 6px; margin-top: 14px; }
.hint { margin-top: 70px; font-size: 24px; color: var(--ink-3); }
''' + AA_CARD_CSS + '''''', '''
<div class="mk u" style="--d:.05s">How AI grew up</div>
<h1 class="mt u" style="--d:.15s">AI did not appear <em>overnight</em></h1>
<p class="ml u" style="--d:.3s">70 years, 5 big steps. Each one stands on the one before.</p>
<div class="tl"><div class="row">
  <div class="ln ug" style="--d:.5s"></div>
  ''' + ''.join('<div class="st u%s" style="--d:%.2fs"><i></i><small>%s</small><b>%s</b><p>%s</p>%s</div>' % (' now' if k == 4 else '', .6 + k * .4, y, t, d_, '<em>You are here</em>' if k == 4 else '') for k, (y, t, d_) in enumerate(AA_HIST)) + '''
</div></div>
<div class="stg">''' + _aa_cards() + '''</div>
<script>
(function () {
  var B = document.body, cards = [].slice.call(document.querySelectorAll('.dt'));
  function set(n) {
    B.dataset.s = String(n);
    cards.forEach(function (c) {
      var k = +c.dataset.k;
      c.classList.toggle('past', k < n); var was = c.classList.contains('on');
      c.classList.toggle('on', k === n);
      if (k === n && !was) {
        c.classList.remove('go'); void c.offsetWidth; c.classList.add('go');
        c.querySelectorAll('animateMotion').forEach(function (a) { try { a.endElement(); } catch (e) {} });
        setTimeout(function () { c.querySelectorAll('animateMotion').forEach(function (a) { try { a.beginElement(); } catch (e) {} }); }, 900);
      }
      if (k !== n) c.classList.remove('go');
    });
  }
  set(0);
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
''',
"\"Before we open up the brain, 1 minute of history, because ChatGPT did not come from nowhere. 70 years, 5 big steps. Let me open them 1 by 1.\"\n\n(Next) Rules, 1950s to 80s: \"Think of a recipe book: the computer follows every step exactly. Watch this order of RM6,000: the rule says over the credit limit, block it. You use rules every day: Excel formulas, the credit-limit check in SQL Account. The problem: a new situation with no rule, and it is stuck.\"\n\n(Next) Machine learning, 2000s: \"Think of a clerk who has seen 10,000 invoices and just knows who pays late. You show the computer past customers, green paid on time, orange paid late. It finds the line between them by itself. Then a new customer comes in: Kedai Ali, 80 percent chance of paying late. That is how spam filters and credit scores work. But it needs neat tables, and 1 model answers only 1 question.\"\n\n(Next) Deep learning, 2012: \"Think of a child who learns what a cat is by seeing 1,000 cats. Many layers look at a photo, layer by layer, and it says: damaged carton, 94 percent sure. Face unlock, Siri, Google Translate all work like this. In your company: reading a handwritten order or a bank slip. But each model does only 1 job, and it cannot talk with you.\"\n\n(Next) LLM, 2018 to 2020: \"Think of your phone's autocomplete, but it read the whole internet. The customer asks: can you deliver tomorrow? It writes: yes, we can deliver... and for the next word it scores every option: tomorrow 82 percent. It picks it. Then the next word, and the next. ChatGPT, Claude, Gemini, DeepSeek. It replies to emails, summarises PDFs. But it only talks; it cannot act in your systems.\"\n\n(Next) AI agents, 2025: \"Think of a new staff member. It reads the WhatsApp order, checks the stock, drafts the Sales Order, and then asks you to approve. Round and round the loop until the job is done. That is where we are today.\"\n\nThis slide has 5 extra Next presses; each card flies in, in 3D, and plays its own short animation.\nNext: \"Now let's open up the brain of today's AI: the LLM.\"")


# ---------------- 2b · types of AI, by what they do (overview + 5 detail cards, like 70 years of AI) ----------------
AT_TYPES = [  # icon, name, technology, does, think of it like, how it works, in real life, in your company, limit
    ('<path d="M3 20h18"/><path d="M5 16l4-5 4 3 6-8"/><path d="M15 6h4v4"/>', 'Predictive AI', 'Machine learning', 'Guesses what comes next',
     'Like a weather forecast, but for your sales and your customers.',
     'It learns from <b>past numbers</b> and guesses the next one.',
     ['Grab arrival time', 'Bank fraud alert', 'Shopee picks for you'],
     'Who will pay late? What will run out?', 'Only as good as your past data. A new product has no history.'),
    ('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>', 'Vision AI', 'Deep learning', 'Sees and reads pictures',
     'Like a car park guard who never blinks and reads every plate.',
     'A camera takes a photo. It finds the <b>plate</b> and reads the letters.',
     ['Car park plate reader', 'Face unlock', 'Google Lens'],
     'Read a handwritten order or a bank slip', 'Dirty plate or bad light? It can misread.'),
    ('<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>', 'Voice AI', 'Deep learning', 'Hears and speaks',
     'Like a secretary who listens to every voice note and types it out.',
     'It turns <b>sound into text</b>, and text back into speech.',
     ['Hey Siri', 'YouTube captions', 'Car voice control'],
     'A WhatsApp voice note becomes an order', 'A noisy shop or heavy slang? It mishears sometimes.'),
    ('<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="M21 16l-5-5L5 21"/>', 'Diffusion AI', 'Diffusion model', 'Makes pictures and videos',
     'Like a sculptor: starts from a block of noise and chips away until a picture appears.',
     'It starts from <b>random noise</b> and cleans it, step by step, into a picture or video.',
     ['AI short dramas', 'Midjourney', 'Sora'],
     'Product photos and promo videos, no studio', 'Hands, faces and words can come out wrong. Check before you post.'),
    ('<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M12 3v4M9 12h.01M15 12h.01M9 16h6"/>', 'AI Agent', 'LLM + tools', 'Does the work',
     'Like a new staff member: reads, checks, does the job, then asks you.',
     'An LLM with <b>tools</b>. It opens your systems and works step by step.',
     ['Claude Code', 'OpenAI Codex'],
     'WhatsApp order &rarr; Sales Order, you approve', 'A person still approves before anything is posted.'),
]
AT_ILL = [
# ---- 1 · predictive: past months rise, the trend line runs on, next month is forecast
'''<svg class="il" viewBox="0 0 640 440">
<path class="dl" style="--t:.3s" pathLength="1" d="M30 360 H610"/>
''' + ''.join('<g class="a" style="--t:%.2fs"><rect x="%d" y="%d" width="52" height="%d" rx="8" fill="#C9D4CC"/><text x="%d" y="392" class="t3">%s</text></g>'
              % (.5 + k * .15, 60 + k * 80, 360 - h, h, 86 + k * 80, m) for k, (m, h) in enumerate([('Jun', 150), ('Jul', 170), ('Aug', 140), ('Sep', 190), ('Oct', 210), ('Nov', 230)])) + '''
<g class="p" style="--t:2.2s"><rect x="540" y="100" width="52" height="260" rx="8" fill="#E6F6EE" stroke="#006C48" stroke-width="3" stroke-dasharray="8 6"/></g>
<text class="a t3" style="--t:2.2s" x="566" y="392">Dec</text>
<path class="dl" style="--t:1.5s;stroke:#006C48" pathLength="1" d="M86 210 L166 190 L246 220 L326 170 L406 150 L486 130 L566 100"/>
<circle class="p" style="--t:2.5s" cx="566" cy="100" r="10" fill="#006C48"/>
<g class="a" style="--t:2.8s"><rect x="210" y="24" width="330" height="50" rx="14" fill="#02221F"/><text x="375" y="56" class="t4">December: 1,240 cartons</text></g>
</svg>''',
# ---- 2 · vision: a car rolls up, the camera reads the plate, the barrier lifts
'''<svg class="il" viewBox="0 0 640 440">
<rect x="0" y="378" width="640" height="10" rx="5" fill="#DCE3DF"/>
<g class="car">
<path d="M90 250 L130 172 Q140 152 165 152 H315 Q340 152 350 172 L390 250 Z" fill="#2F4A43"/>
<path d="M142 240 L166 178 H314 L338 240 Z" fill="#A9C4BA"/>
<rect x="70" y="240" width="340" height="100" rx="26" fill="#3C5C53"/>
<circle cx="115" cy="282" r="17" fill="#FFE8A8"/><circle cx="365" cy="282" r="17" fill="#FFE8A8"/>
<rect x="85" y="334" width="60" height="44" rx="10" fill="#02221F"/><rect x="335" y="334" width="60" height="44" rx="10" fill="#02221F"/>
<rect x="180" y="296" width="120" height="36" rx="6" fill="#fff" stroke="#02221F" stroke-width="2.5"/><text x="240" y="321" class="t5">WXY 1234</text>
</g>
<rect x="452" y="96" width="12" height="286" rx="4" fill="#02221F"/>
<g class="a" style="--t:1s"><rect x="418" y="70" width="80" height="38" rx="10" fill="#02221F"/><circle cx="430" cy="89" r="9" fill="#00F5A9"/>
<circle class="ring" cx="430" cy="89" r="16" fill="none" stroke="#00F5A9" stroke-width="3"/></g>
<path class="dl" style="--t:1.4s;stroke:#00A57A;stroke-width:2" pathLength="1" d="M424 98 L306 292"/>
<rect x="548" y="226" width="56" height="156" rx="10" fill="#02221F"/><rect x="560" y="250" width="32" height="8" rx="4" fill="#00F5A9" opacity=".7"/>
<rect class="dl box" style="--t:1.8s" pathLength="1" x="170" y="288" width="140" height="52" rx="6" fill="none"/>
<g class="a" style="--t:2.3s"><rect x="60" y="34" width="300" height="84" rx="16" fill="#02221F"/><text x="210" y="68" class="t8">WXY 1234</text><text x="210" y="100" class="t9">Season pass &middot; open the gate</text></g>
<g class="arm"><rect x="300" y="226" width="280" height="18" rx="9" fill="#fff" stroke="#02221F" stroke-width="2.5"/>''' + ''.join('<rect x="%d" y="227.5" width="26" height="15" fill="#E5484D"/>' % x for x in (318, 374, 430, 486)) + '''</g>
<circle cx="576" cy="235" r="9" fill="#fff" stroke="#02221F" stroke-width="3"/>
</svg>''',
# ---- 3 · voice: a WhatsApp voice note plays, it is typed out, it becomes an order line
'''<svg class="il" viewBox="0 0 640 440">
<g class="a" style="--t:.4s"><rect x="20" y="30" width="400" height="84" rx="24" fill="#DCF8C6"/><path d="M46 56 l26 16 l-26 16z" fill="#02221F"/>
''' + ''.join('<rect class="vb" style="--t:%.2fs" x="%d" y="%d" width="6" height="%d" rx="3" fill="#00A57A"/>' % (.6 + (k % 5) * .12, 92 + k * 12, 72 - h // 2, h) for k, h in enumerate([14, 26, 40, 22, 34, 48, 30, 18, 38, 52, 28, 16, 36, 24, 44, 20, 12, 30, 22, 14])) + '''
<text x="384" y="104" class="t3">0:06</text></g>
<path class="dl" style="--t:1.2s" pathLength="1" d="M210 124 V174"/>
<text class="a t3m2" style="--t:1.2s" x="230" y="156">SPEECH TO TEXT</text>
<g class="a" style="--t:1.4s"><rect x="20" y="186" width="600" height="80" rx="20" fill="#fff" stroke="#DDE3DF" stroke-width="2"/></g>
''' + ''.join('<text class="a w" style="--t:%.2fs" x="%d" y="236">%s</text>' % (1.6 + k * .22, x, w) for k, (x, w) in enumerate([(46, 'Boss,'), (124, 'esok'), (192, 'hantar'), (284, '10'), (324, 'carton'), (414, 'Milo')])) + '''
<path class="dl" style="--t:3s" pathLength="1" d="M320 274 V306"/>
<g class="p" style="--t:3.3s"><rect x="130" y="312" width="380" height="92" rx="20" fill="#02221F"/><text x="320" y="348" class="t9">New order line</text><text x="320" y="384" class="t4">10 ctn Milo &middot; deliver tomorrow</text></g>
</svg>''',
# ---- 4 · diffusion: an AI short drama frame comes out of noise, step by step
'''<svg class="il" viewBox="0 0 640 440"><defs><linearGradient id="dfsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7C5CFF"/><stop offset=".55" stop-color="#FF8A5B"/><stop offset="1" stop-color="#FFB547"/></linearGradient><clipPath id="dfc0"><rect x="20" y="104" width="150" height="266" rx="16"/></clipPath><clipPath id="dfc1"><rect x="245" y="104" width="150" height="266" rx="16"/></clipPath><clipPath id="dfc2"><rect x="470" y="104" width="150" height="266" rx="16"/></clipPath></defs>
<g class="a" style="--t:.4s"><rect x="40" y="20" width="560" height="62" rx="22" fill="#02221F"/><text x="320" y="59" class="t6">Short drama: the boss finds out his clerk is an AI</text></g>
<g class="a" style="--t:.9s"><g clip-path="url(#dfc0)"><g opacity="1"><rect x="20" y="104" width="15" height="15" fill="#02221F"/><rect x="35" y="104" width="15" height="15" fill="#7C5CFF"/><rect x="50" y="104" width="15" height="15" fill="#F2FBF7"/><rect x="65" y="104" width="15" height="15" fill="#FFB547"/><rect x="80" y="104" width="15" height="15" fill="#FF8A5B"/><rect x="95" y="104" width="15" height="15" fill="#E5484D"/><rect x="110" y="104" width="15" height="15" fill="#FF8A5B"/><rect x="125" y="104" width="15" height="15" fill="#02221F"/><rect x="140" y="104" width="15" height="15" fill="#FFB547"/><rect x="155" y="104" width="15" height="15" fill="#E5484D"/><rect x="20" y="119" width="15" height="15" fill="#4DA3FF"/><rect x="35" y="119" width="15" height="15" fill="#FFB547"/><rect x="50" y="119" width="15" height="15" fill="#FF8A5B"/><rect x="65" y="119" width="15" height="15" fill="#F2FBF7"/><rect x="80" y="119" width="15" height="15" fill="#F2FBF7"/><rect x="95" y="119" width="15" height="15" fill="#FF8A5B"/><rect x="110" y="119" width="15" height="15" fill="#4DA3FF"/><rect x="125" y="119" width="15" height="15" fill="#FF8A5B"/><rect x="140" y="119" width="15" height="15" fill="#E5484D"/><rect x="155" y="119" width="15" height="15" fill="#F2FBF7"/><rect x="20" y="134" width="15" height="15" fill="#FFB547"/><rect x="35" y="134" width="15" height="15" fill="#FF8A5B"/><rect x="50" y="134" width="15" height="15" fill="#4DA3FF"/><rect x="65" y="134" width="15" height="15" fill="#FFB547"/><rect x="80" y="134" width="15" height="15" fill="#F2FBF7"/><rect x="95" y="134" width="15" height="15" fill="#FFB547"/><rect x="110" y="134" width="15" height="15" fill="#4DA3FF"/><rect x="125" y="134" width="15" height="15" fill="#FFB547"/><rect x="140" y="134" width="15" height="15" fill="#E5484D"/><rect x="155" y="134" width="15" height="15" fill="#7C5CFF"/><rect x="20" y="149" width="15" height="15" fill="#00A57A"/><rect x="35" y="149" width="15" height="15" fill="#F2FBF7"/><rect x="50" y="149" width="15" height="15" fill="#7C5CFF"/><rect x="65" y="149" width="15" height="15" fill="#E5484D"/><rect x="80" y="149" width="15" height="15" fill="#FF8A5B"/><rect x="95" y="149" width="15" height="15" fill="#00A57A"/><rect x="110" y="149" width="15" height="15" fill="#E5484D"/><rect x="125" y="149" width="15" height="15" fill="#7C5CFF"/><rect x="140" y="149" width="15" height="15" fill="#FF8A5B"/><rect x="155" y="149" width="15" height="15" fill="#4DA3FF"/><rect x="20" y="164" width="15" height="15" fill="#02221F"/><rect x="35" y="164" width="15" height="15" fill="#FF8A5B"/><rect x="50" y="164" width="15" height="15" fill="#E5484D"/><rect x="65" y="164" width="15" height="15" fill="#FF8A5B"/><rect x="80" y="164" width="15" height="15" fill="#FFB547"/><rect x="95" y="164" width="15" height="15" fill="#4DA3FF"/><rect x="110" y="164" width="15" height="15" fill="#C9D4CC"/><rect x="125" y="164" width="15" height="15" fill="#E5484D"/><rect x="140" y="164" width="15" height="15" fill="#F2FBF7"/><rect x="155" y="164" width="15" height="15" fill="#02221F"/><rect x="20" y="179" width="15" height="15" fill="#C9D4CC"/><rect x="35" y="179" width="15" height="15" fill="#C9D4CC"/><rect x="50" y="179" width="15" height="15" fill="#02221F"/><rect x="65" y="179" width="15" height="15" fill="#00A57A"/><rect x="80" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="95" y="179" width="15" height="15" fill="#7C5CFF"/><rect x="110" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="125" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="140" y="179" width="15" height="15" fill="#00A57A"/><rect x="155" y="179" width="15" height="15" fill="#E5484D"/><rect x="20" y="194" width="15" height="15" fill="#C9D4CC"/><rect x="35" y="194" width="15" height="15" fill="#02221F"/><rect x="50" y="194" width="15" height="15" fill="#C9D4CC"/><rect x="65" y="194" width="15" height="15" fill="#00A57A"/><rect x="80" y="194" width="15" height="15" fill="#FF8A5B"/><rect x="95" y="194" width="15" height="15" fill="#FF8A5B"/><rect x="110" y="194" width="15" height="15" fill="#E5484D"/><rect x="125" y="194" width="15" height="15" fill="#F2FBF7"/><rect x="140" y="194" width="15" height="15" fill="#7C5CFF"/><rect x="155" y="194" width="15" height="15" fill="#02221F"/><rect x="20" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="35" y="209" width="15" height="15" fill="#C9D4CC"/><rect x="50" y="209" width="15" height="15" fill="#F2FBF7"/><rect x="65" y="209" width="15" height="15" fill="#FFB547"/><rect x="80" y="209" width="15" height="15" fill="#FF8A5B"/><rect x="95" y="209" width="15" height="15" fill="#E5484D"/><rect x="110" y="209" width="15" height="15" fill="#02221F"/><rect x="125" y="209" width="15" height="15" fill="#02221F"/><rect x="140" y="209" width="15" height="15" fill="#02221F"/><rect x="155" y="209" width="15" height="15" fill="#C9D4CC"/><rect x="20" y="224" width="15" height="15" fill="#C9D4CC"/><rect x="35" y="224" width="15" height="15" fill="#FF8A5B"/><rect x="50" y="224" width="15" height="15" fill="#FF8A5B"/><rect x="65" y="224" width="15" height="15" fill="#00A57A"/><rect x="80" y="224" width="15" height="15" fill="#C9D4CC"/><rect x="95" y="224" width="15" height="15" fill="#FF8A5B"/><rect x="110" y="224" width="15" height="15" fill="#FFB547"/><rect x="125" y="224" width="15" height="15" fill="#00A57A"/><rect x="140" y="224" width="15" height="15" fill="#C9D4CC"/><rect x="155" y="224" width="15" height="15" fill="#00A57A"/><rect x="20" y="239" width="15" height="15" fill="#F2FBF7"/><rect x="35" y="239" width="15" height="15" fill="#02221F"/><rect x="50" y="239" width="15" height="15" fill="#FFB547"/><rect x="65" y="239" width="15" height="15" fill="#C9D4CC"/><rect x="80" y="239" width="15" height="15" fill="#02221F"/><rect x="95" y="239" width="15" height="15" fill="#7C5CFF"/><rect x="110" y="239" width="15" height="15" fill="#FF8A5B"/><rect x="125" y="239" width="15" height="15" fill="#C9D4CC"/><rect x="140" y="239" width="15" height="15" fill="#FFB547"/><rect x="155" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="20" y="254" width="15" height="15" fill="#00A57A"/><rect x="35" y="254" width="15" height="15" fill="#7C5CFF"/><rect x="50" y="254" width="15" height="15" fill="#4DA3FF"/><rect x="65" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="80" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="95" y="254" width="15" height="15" fill="#C9D4CC"/><rect x="110" y="254" width="15" height="15" fill="#FF8A5B"/><rect x="125" y="254" width="15" height="15" fill="#7C5CFF"/><rect x="140" y="254" width="15" height="15" fill="#C9D4CC"/><rect x="155" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="20" y="269" width="15" height="15" fill="#E5484D"/><rect x="35" y="269" width="15" height="15" fill="#00A57A"/><rect x="50" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="65" y="269" width="15" height="15" fill="#F2FBF7"/><rect x="80" y="269" width="15" height="15" fill="#E5484D"/><rect x="95" y="269" width="15" height="15" fill="#00A57A"/><rect x="110" y="269" width="15" height="15" fill="#F2FBF7"/><rect x="125" y="269" width="15" height="15" fill="#02221F"/><rect x="140" y="269" width="15" height="15" fill="#F2FBF7"/><rect x="155" y="269" width="15" height="15" fill="#4DA3FF"/><rect x="20" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="35" y="284" width="15" height="15" fill="#FF8A5B"/><rect x="50" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="65" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="80" y="284" width="15" height="15" fill="#4DA3FF"/><rect x="95" y="284" width="15" height="15" fill="#4DA3FF"/><rect x="110" y="284" width="15" height="15" fill="#FFB547"/><rect x="125" y="284" width="15" height="15" fill="#C9D4CC"/><rect x="140" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="155" y="284" width="15" height="15" fill="#00A57A"/><rect x="20" y="299" width="15" height="15" fill="#00A57A"/><rect x="35" y="299" width="15" height="15" fill="#FFB547"/><rect x="50" y="299" width="15" height="15" fill="#7C5CFF"/><rect x="65" y="299" width="15" height="15" fill="#F2FBF7"/><rect x="80" y="299" width="15" height="15" fill="#E5484D"/><rect x="95" y="299" width="15" height="15" fill="#02221F"/><rect x="110" y="299" width="15" height="15" fill="#02221F"/><rect x="125" y="299" width="15" height="15" fill="#7C5CFF"/><rect x="140" y="299" width="15" height="15" fill="#E5484D"/><rect x="155" y="299" width="15" height="15" fill="#FFB547"/><rect x="20" y="314" width="15" height="15" fill="#C9D4CC"/><rect x="35" y="314" width="15" height="15" fill="#E5484D"/><rect x="50" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="65" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="80" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="95" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="110" y="314" width="15" height="15" fill="#FF8A5B"/><rect x="125" y="314" width="15" height="15" fill="#C9D4CC"/><rect x="140" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="155" y="314" width="15" height="15" fill="#FFB547"/><rect x="20" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="35" y="329" width="15" height="15" fill="#FF8A5B"/><rect x="50" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="65" y="329" width="15" height="15" fill="#C9D4CC"/><rect x="80" y="329" width="15" height="15" fill="#7C5CFF"/><rect x="95" y="329" width="15" height="15" fill="#FF8A5B"/><rect x="110" y="329" width="15" height="15" fill="#02221F"/><rect x="125" y="329" width="15" height="15" fill="#FFB547"/><rect x="140" y="329" width="15" height="15" fill="#FF8A5B"/><rect x="155" y="329" width="15" height="15" fill="#FFB547"/><rect x="20" y="344" width="15" height="15" fill="#7C5CFF"/><rect x="35" y="344" width="15" height="15" fill="#E5484D"/><rect x="50" y="344" width="15" height="15" fill="#FF8A5B"/><rect x="65" y="344" width="15" height="15" fill="#02221F"/><rect x="80" y="344" width="15" height="15" fill="#FFB547"/><rect x="95" y="344" width="15" height="15" fill="#FF8A5B"/><rect x="110" y="344" width="15" height="15" fill="#4DA3FF"/><rect x="125" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="140" y="344" width="15" height="15" fill="#7C5CFF"/><rect x="155" y="344" width="15" height="15" fill="#00A57A"/><rect x="20" y="359" width="15" height="15" fill="#02221F"/><rect x="35" y="359" width="15" height="15" fill="#02221F"/><rect x="50" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="65" y="359" width="15" height="15" fill="#FF8A5B"/><rect x="80" y="359" width="15" height="15" fill="#FF8A5B"/><rect x="95" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="110" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="125" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="140" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="155" y="359" width="15" height="15" fill="#00A57A"/></g></g><text x="95" y="396" class="t3">Step 1: noise</text></g><path class="dl" style="--t:1.5s" pathLength="1" d="M180 237 H235"/><path class="dl" style="--t:2.3s" pathLength="1" d="M405 237 H460"/><g class="a" style="--t:1.7s"><g clip-path="url(#dfc1)"><rect x="245" y="104" width="150" height="266" fill="url(#dfsky)"/><circle cx="345" cy="194" r="26" fill="#FFE8A8"/><rect x="245" y="260" width="26" height="70" fill="#0E3A33"/><rect x="269" y="220" width="20" height="110" fill="#0E3A33"/><rect x="287" y="246" width="30" height="84" fill="#0E3A33"/><rect x="315" y="200" width="22" height="130" fill="#0E3A33"/><rect x="335" y="234" width="34" height="96" fill="#0E3A33"/><rect x="367" y="212" width="28" height="118" fill="#0E3A33"/><rect x="245" y="330" width="150" height="40" fill="#02221F"/><g fill="#02221F"><circle cx="287" cy="254" r="14"/><rect x="270" y="270" width="34" height="62" rx="14"/><circle cx="353" cy="258" r="13"/><rect x="337" y="273" width="32" height="58" rx="14"/></g><g opacity="0.55"><rect x="245" y="104" width="15" height="15" fill="#FF8A5B"/><rect x="260" y="104" width="15" height="15" fill="#7C5CFF"/><rect x="275" y="104" width="15" height="15" fill="#FF8A5B"/><rect x="290" y="104" width="15" height="15" fill="#02221F"/><rect x="305" y="104" width="15" height="15" fill="#00A57A"/><rect x="320" y="104" width="15" height="15" fill="#C9D4CC"/><rect x="335" y="104" width="15" height="15" fill="#7C5CFF"/><rect x="350" y="104" width="15" height="15" fill="#E5484D"/><rect x="365" y="104" width="15" height="15" fill="#FFB547"/><rect x="380" y="104" width="15" height="15" fill="#4DA3FF"/><rect x="245" y="119" width="15" height="15" fill="#E5484D"/><rect x="260" y="119" width="15" height="15" fill="#02221F"/><rect x="275" y="119" width="15" height="15" fill="#7C5CFF"/><rect x="290" y="119" width="15" height="15" fill="#E5484D"/><rect x="305" y="119" width="15" height="15" fill="#FFB547"/><rect x="320" y="119" width="15" height="15" fill="#E5484D"/><rect x="335" y="119" width="15" height="15" fill="#00A57A"/><rect x="350" y="119" width="15" height="15" fill="#FF8A5B"/><rect x="365" y="119" width="15" height="15" fill="#00A57A"/><rect x="380" y="119" width="15" height="15" fill="#E5484D"/><rect x="245" y="134" width="15" height="15" fill="#02221F"/><rect x="260" y="134" width="15" height="15" fill="#7C5CFF"/><rect x="275" y="134" width="15" height="15" fill="#02221F"/><rect x="290" y="134" width="15" height="15" fill="#4DA3FF"/><rect x="305" y="134" width="15" height="15" fill="#E5484D"/><rect x="320" y="134" width="15" height="15" fill="#E5484D"/><rect x="335" y="134" width="15" height="15" fill="#E5484D"/><rect x="350" y="134" width="15" height="15" fill="#02221F"/><rect x="365" y="134" width="15" height="15" fill="#4DA3FF"/><rect x="380" y="134" width="15" height="15" fill="#4DA3FF"/><rect x="245" y="149" width="15" height="15" fill="#4DA3FF"/><rect x="260" y="149" width="15" height="15" fill="#F2FBF7"/><rect x="275" y="149" width="15" height="15" fill="#4DA3FF"/><rect x="290" y="149" width="15" height="15" fill="#4DA3FF"/><rect x="305" y="149" width="15" height="15" fill="#E5484D"/><rect x="320" y="149" width="15" height="15" fill="#C9D4CC"/><rect x="335" y="149" width="15" height="15" fill="#02221F"/><rect x="350" y="149" width="15" height="15" fill="#FFB547"/><rect x="365" y="149" width="15" height="15" fill="#FFB547"/><rect x="380" y="149" width="15" height="15" fill="#00A57A"/><rect x="245" y="164" width="15" height="15" fill="#C9D4CC"/><rect x="260" y="164" width="15" height="15" fill="#00A57A"/><rect x="275" y="164" width="15" height="15" fill="#4DA3FF"/><rect x="290" y="164" width="15" height="15" fill="#02221F"/><rect x="305" y="164" width="15" height="15" fill="#C9D4CC"/><rect x="320" y="164" width="15" height="15" fill="#02221F"/><rect x="335" y="164" width="15" height="15" fill="#02221F"/><rect x="350" y="164" width="15" height="15" fill="#FF8A5B"/><rect x="365" y="164" width="15" height="15" fill="#4DA3FF"/><rect x="380" y="164" width="15" height="15" fill="#FF8A5B"/><rect x="245" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="260" y="179" width="15" height="15" fill="#C9D4CC"/><rect x="275" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="290" y="179" width="15" height="15" fill="#02221F"/><rect x="305" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="320" y="179" width="15" height="15" fill="#C9D4CC"/><rect x="335" y="179" width="15" height="15" fill="#FFB547"/><rect x="350" y="179" width="15" height="15" fill="#C9D4CC"/><rect x="365" y="179" width="15" height="15" fill="#02221F"/><rect x="380" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="245" y="194" width="15" height="15" fill="#FF8A5B"/><rect x="260" y="194" width="15" height="15" fill="#F2FBF7"/><rect x="275" y="194" width="15" height="15" fill="#4DA3FF"/><rect x="290" y="194" width="15" height="15" fill="#C9D4CC"/><rect x="305" y="194" width="15" height="15" fill="#7C5CFF"/><rect x="320" y="194" width="15" height="15" fill="#F2FBF7"/><rect x="335" y="194" width="15" height="15" fill="#02221F"/><rect x="350" y="194" width="15" height="15" fill="#FF8A5B"/><rect x="365" y="194" width="15" height="15" fill="#F2FBF7"/><rect x="380" y="194" width="15" height="15" fill="#C9D4CC"/><rect x="245" y="209" width="15" height="15" fill="#F2FBF7"/><rect x="260" y="209" width="15" height="15" fill="#FF8A5B"/><rect x="275" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="290" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="305" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="320" y="209" width="15" height="15" fill="#FFB547"/><rect x="335" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="350" y="209" width="15" height="15" fill="#C9D4CC"/><rect x="365" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="380" y="209" width="15" height="15" fill="#C9D4CC"/><rect x="245" y="224" width="15" height="15" fill="#02221F"/><rect x="260" y="224" width="15" height="15" fill="#7C5CFF"/><rect x="275" y="224" width="15" height="15" fill="#E5484D"/><rect x="290" y="224" width="15" height="15" fill="#E5484D"/><rect x="305" y="224" width="15" height="15" fill="#7C5CFF"/><rect x="320" y="224" width="15" height="15" fill="#FFB547"/><rect x="335" y="224" width="15" height="15" fill="#FFB547"/><rect x="350" y="224" width="15" height="15" fill="#FF8A5B"/><rect x="365" y="224" width="15" height="15" fill="#E5484D"/><rect x="380" y="224" width="15" height="15" fill="#7C5CFF"/><rect x="245" y="239" width="15" height="15" fill="#F2FBF7"/><rect x="260" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="275" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="290" y="239" width="15" height="15" fill="#FFB547"/><rect x="305" y="239" width="15" height="15" fill="#00A57A"/><rect x="320" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="335" y="239" width="15" height="15" fill="#00A57A"/><rect x="350" y="239" width="15" height="15" fill="#E5484D"/><rect x="365" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="380" y="239" width="15" height="15" fill="#02221F"/><rect x="245" y="254" width="15" height="15" fill="#00A57A"/><rect x="260" y="254" width="15" height="15" fill="#E5484D"/><rect x="275" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="290" y="254" width="15" height="15" fill="#7C5CFF"/><rect x="305" y="254" width="15" height="15" fill="#FFB547"/><rect x="320" y="254" width="15" height="15" fill="#02221F"/><rect x="335" y="254" width="15" height="15" fill="#C9D4CC"/><rect x="350" y="254" width="15" height="15" fill="#E5484D"/><rect x="365" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="380" y="254" width="15" height="15" fill="#E5484D"/><rect x="245" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="260" y="269" width="15" height="15" fill="#E5484D"/><rect x="275" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="290" y="269" width="15" height="15" fill="#E5484D"/><rect x="305" y="269" width="15" height="15" fill="#E5484D"/><rect x="320" y="269" width="15" height="15" fill="#FFB547"/><rect x="335" y="269" width="15" height="15" fill="#C9D4CC"/><rect x="350" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="365" y="269" width="15" height="15" fill="#FFB547"/><rect x="380" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="245" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="260" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="275" y="284" width="15" height="15" fill="#C9D4CC"/><rect x="290" y="284" width="15" height="15" fill="#FF8A5B"/><rect x="305" y="284" width="15" height="15" fill="#E5484D"/><rect x="320" y="284" width="15" height="15" fill="#FFB547"/><rect x="335" y="284" width="15" height="15" fill="#02221F"/><rect x="350" y="284" width="15" height="15" fill="#E5484D"/><rect x="365" y="284" width="15" height="15" fill="#E5484D"/><rect x="380" y="284" width="15" height="15" fill="#E5484D"/><rect x="245" y="299" width="15" height="15" fill="#C9D4CC"/><rect x="260" y="299" width="15" height="15" fill="#FF8A5B"/><rect x="275" y="299" width="15" height="15" fill="#E5484D"/><rect x="290" y="299" width="15" height="15" fill="#FFB547"/><rect x="305" y="299" width="15" height="15" fill="#4DA3FF"/><rect x="320" y="299" width="15" height="15" fill="#4DA3FF"/><rect x="335" y="299" width="15" height="15" fill="#00A57A"/><rect x="350" y="299" width="15" height="15" fill="#FFB547"/><rect x="365" y="299" width="15" height="15" fill="#FF8A5B"/><rect x="380" y="299" width="15" height="15" fill="#E5484D"/><rect x="245" y="314" width="15" height="15" fill="#C9D4CC"/><rect x="260" y="314" width="15" height="15" fill="#E5484D"/><rect x="275" y="314" width="15" height="15" fill="#FFB547"/><rect x="290" y="314" width="15" height="15" fill="#FF8A5B"/><rect x="305" y="314" width="15" height="15" fill="#C9D4CC"/><rect x="320" y="314" width="15" height="15" fill="#02221F"/><rect x="335" y="314" width="15" height="15" fill="#E5484D"/><rect x="350" y="314" width="15" height="15" fill="#E5484D"/><rect x="365" y="314" width="15" height="15" fill="#4DA3FF"/><rect x="380" y="314" width="15" height="15" fill="#00A57A"/><rect x="245" y="329" width="15" height="15" fill="#C9D4CC"/><rect x="260" y="329" width="15" height="15" fill="#E5484D"/><rect x="275" y="329" width="15" height="15" fill="#E5484D"/><rect x="290" y="329" width="15" height="15" fill="#C9D4CC"/><rect x="305" y="329" width="15" height="15" fill="#E5484D"/><rect x="320" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="335" y="329" width="15" height="15" fill="#E5484D"/><rect x="350" y="329" width="15" height="15" fill="#00A57A"/><rect x="365" y="329" width="15" height="15" fill="#E5484D"/><rect x="380" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="245" y="344" width="15" height="15" fill="#C9D4CC"/><rect x="260" y="344" width="15" height="15" fill="#7C5CFF"/><rect x="275" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="290" y="344" width="15" height="15" fill="#FF8A5B"/><rect x="305" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="320" y="344" width="15" height="15" fill="#C9D4CC"/><rect x="335" y="344" width="15" height="15" fill="#02221F"/><rect x="350" y="344" width="15" height="15" fill="#FF8A5B"/><rect x="365" y="344" width="15" height="15" fill="#4DA3FF"/><rect x="380" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="245" y="359" width="15" height="15" fill="#FF8A5B"/><rect x="260" y="359" width="15" height="15" fill="#4DA3FF"/><rect x="275" y="359" width="15" height="15" fill="#00A57A"/><rect x="290" y="359" width="15" height="15" fill="#FF8A5B"/><rect x="305" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="320" y="359" width="15" height="15" fill="#02221F"/><rect x="335" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="350" y="359" width="15" height="15" fill="#00A57A"/><rect x="365" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="380" y="359" width="15" height="15" fill="#C9D4CC"/></g></g><text x="320" y="396" class="t3">Step 25</text></g><g class="a" style="--t:2.5s"><g clip-path="url(#dfc2)"><rect x="470" y="104" width="150" height="266" fill="url(#dfsky)"/><circle cx="570" cy="194" r="26" fill="#FFE8A8"/><rect x="470" y="260" width="26" height="70" fill="#0E3A33"/><rect x="494" y="220" width="20" height="110" fill="#0E3A33"/><rect x="512" y="246" width="30" height="84" fill="#0E3A33"/><rect x="540" y="200" width="22" height="130" fill="#0E3A33"/><rect x="560" y="234" width="34" height="96" fill="#0E3A33"/><rect x="592" y="212" width="28" height="118" fill="#0E3A33"/><rect x="470" y="330" width="150" height="40" fill="#02221F"/><g fill="#02221F"><circle cx="512" cy="254" r="14"/><rect x="495" y="270" width="34" height="62" rx="14"/><circle cx="578" cy="258" r="13"/><rect x="562" y="273" width="32" height="58" rx="14"/></g><g class="dn"><g opacity="0.55"><rect x="470" y="104" width="15" height="15" fill="#4DA3FF"/><rect x="485" y="104" width="15" height="15" fill="#FF8A5B"/><rect x="500" y="104" width="15" height="15" fill="#F2FBF7"/><rect x="515" y="104" width="15" height="15" fill="#C9D4CC"/><rect x="530" y="104" width="15" height="15" fill="#7C5CFF"/><rect x="545" y="104" width="15" height="15" fill="#4DA3FF"/><rect x="560" y="104" width="15" height="15" fill="#7C5CFF"/><rect x="575" y="104" width="15" height="15" fill="#F2FBF7"/><rect x="590" y="104" width="15" height="15" fill="#E5484D"/><rect x="605" y="104" width="15" height="15" fill="#F2FBF7"/><rect x="470" y="119" width="15" height="15" fill="#02221F"/><rect x="485" y="119" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="119" width="15" height="15" fill="#4DA3FF"/><rect x="515" y="119" width="15" height="15" fill="#02221F"/><rect x="530" y="119" width="15" height="15" fill="#02221F"/><rect x="545" y="119" width="15" height="15" fill="#FF8A5B"/><rect x="560" y="119" width="15" height="15" fill="#02221F"/><rect x="575" y="119" width="15" height="15" fill="#FFB547"/><rect x="590" y="119" width="15" height="15" fill="#02221F"/><rect x="605" y="119" width="15" height="15" fill="#E5484D"/><rect x="470" y="134" width="15" height="15" fill="#C9D4CC"/><rect x="485" y="134" width="15" height="15" fill="#C9D4CC"/><rect x="500" y="134" width="15" height="15" fill="#FFB547"/><rect x="515" y="134" width="15" height="15" fill="#F2FBF7"/><rect x="530" y="134" width="15" height="15" fill="#02221F"/><rect x="545" y="134" width="15" height="15" fill="#E5484D"/><rect x="560" y="134" width="15" height="15" fill="#00A57A"/><rect x="575" y="134" width="15" height="15" fill="#E5484D"/><rect x="590" y="134" width="15" height="15" fill="#FF8A5B"/><rect x="605" y="134" width="15" height="15" fill="#FF8A5B"/><rect x="470" y="149" width="15" height="15" fill="#4DA3FF"/><rect x="485" y="149" width="15" height="15" fill="#FF8A5B"/><rect x="500" y="149" width="15" height="15" fill="#FF8A5B"/><rect x="515" y="149" width="15" height="15" fill="#00A57A"/><rect x="530" y="149" width="15" height="15" fill="#00A57A"/><rect x="545" y="149" width="15" height="15" fill="#FFB547"/><rect x="560" y="149" width="15" height="15" fill="#7C5CFF"/><rect x="575" y="149" width="15" height="15" fill="#00A57A"/><rect x="590" y="149" width="15" height="15" fill="#7C5CFF"/><rect x="605" y="149" width="15" height="15" fill="#F2FBF7"/><rect x="470" y="164" width="15" height="15" fill="#00A57A"/><rect x="485" y="164" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="164" width="15" height="15" fill="#7C5CFF"/><rect x="515" y="164" width="15" height="15" fill="#E5484D"/><rect x="530" y="164" width="15" height="15" fill="#E5484D"/><rect x="545" y="164" width="15" height="15" fill="#C9D4CC"/><rect x="560" y="164" width="15" height="15" fill="#02221F"/><rect x="575" y="164" width="15" height="15" fill="#FF8A5B"/><rect x="590" y="164" width="15" height="15" fill="#00A57A"/><rect x="605" y="164" width="15" height="15" fill="#FFB547"/><rect x="470" y="179" width="15" height="15" fill="#7C5CFF"/><rect x="485" y="179" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="515" y="179" width="15" height="15" fill="#00A57A"/><rect x="530" y="179" width="15" height="15" fill="#FFB547"/><rect x="545" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="560" y="179" width="15" height="15" fill="#00A57A"/><rect x="575" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="590" y="179" width="15" height="15" fill="#4DA3FF"/><rect x="605" y="179" width="15" height="15" fill="#FF8A5B"/><rect x="470" y="194" width="15" height="15" fill="#00A57A"/><rect x="485" y="194" width="15" height="15" fill="#FF8A5B"/><rect x="500" y="194" width="15" height="15" fill="#C9D4CC"/><rect x="515" y="194" width="15" height="15" fill="#FFB547"/><rect x="530" y="194" width="15" height="15" fill="#02221F"/><rect x="545" y="194" width="15" height="15" fill="#E5484D"/><rect x="560" y="194" width="15" height="15" fill="#F2FBF7"/><rect x="575" y="194" width="15" height="15" fill="#00A57A"/><rect x="590" y="194" width="15" height="15" fill="#7C5CFF"/><rect x="605" y="194" width="15" height="15" fill="#FFB547"/><rect x="470" y="209" width="15" height="15" fill="#E5484D"/><rect x="485" y="209" width="15" height="15" fill="#4DA3FF"/><rect x="500" y="209" width="15" height="15" fill="#FF8A5B"/><rect x="515" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="530" y="209" width="15" height="15" fill="#00A57A"/><rect x="545" y="209" width="15" height="15" fill="#FFB547"/><rect x="560" y="209" width="15" height="15" fill="#7C5CFF"/><rect x="575" y="209" width="15" height="15" fill="#4DA3FF"/><rect x="590" y="209" width="15" height="15" fill="#00A57A"/><rect x="605" y="209" width="15" height="15" fill="#00A57A"/><rect x="470" y="224" width="15" height="15" fill="#E5484D"/><rect x="485" y="224" width="15" height="15" fill="#4DA3FF"/><rect x="500" y="224" width="15" height="15" fill="#00A57A"/><rect x="515" y="224" width="15" height="15" fill="#C9D4CC"/><rect x="530" y="224" width="15" height="15" fill="#E5484D"/><rect x="545" y="224" width="15" height="15" fill="#7C5CFF"/><rect x="560" y="224" width="15" height="15" fill="#00A57A"/><rect x="575" y="224" width="15" height="15" fill="#02221F"/><rect x="590" y="224" width="15" height="15" fill="#FFB547"/><rect x="605" y="224" width="15" height="15" fill="#00A57A"/><rect x="470" y="239" width="15" height="15" fill="#FFB547"/><rect x="485" y="239" width="15" height="15" fill="#FFB547"/><rect x="500" y="239" width="15" height="15" fill="#FFB547"/><rect x="515" y="239" width="15" height="15" fill="#E5484D"/><rect x="530" y="239" width="15" height="15" fill="#E5484D"/><rect x="545" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="560" y="239" width="15" height="15" fill="#E5484D"/><rect x="575" y="239" width="15" height="15" fill="#C9D4CC"/><rect x="590" y="239" width="15" height="15" fill="#4DA3FF"/><rect x="605" y="239" width="15" height="15" fill="#C9D4CC"/><rect x="470" y="254" width="15" height="15" fill="#FF8A5B"/><rect x="485" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="254" width="15" height="15" fill="#C9D4CC"/><rect x="515" y="254" width="15" height="15" fill="#E5484D"/><rect x="530" y="254" width="15" height="15" fill="#F2FBF7"/><rect x="545" y="254" width="15" height="15" fill="#E5484D"/><rect x="560" y="254" width="15" height="15" fill="#00A57A"/><rect x="575" y="254" width="15" height="15" fill="#4DA3FF"/><rect x="590" y="254" width="15" height="15" fill="#4DA3FF"/><rect x="605" y="254" width="15" height="15" fill="#02221F"/><rect x="470" y="269" width="15" height="15" fill="#4DA3FF"/><rect x="485" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="500" y="269" width="15" height="15" fill="#F2FBF7"/><rect x="515" y="269" width="15" height="15" fill="#02221F"/><rect x="530" y="269" width="15" height="15" fill="#FFB547"/><rect x="545" y="269" width="15" height="15" fill="#7C5CFF"/><rect x="560" y="269" width="15" height="15" fill="#FFB547"/><rect x="575" y="269" width="15" height="15" fill="#FF8A5B"/><rect x="590" y="269" width="15" height="15" fill="#00A57A"/><rect x="605" y="269" width="15" height="15" fill="#F2FBF7"/><rect x="470" y="284" width="15" height="15" fill="#7C5CFF"/><rect x="485" y="284" width="15" height="15" fill="#FFB547"/><rect x="500" y="284" width="15" height="15" fill="#FF8A5B"/><rect x="515" y="284" width="15" height="15" fill="#F2FBF7"/><rect x="530" y="284" width="15" height="15" fill="#E5484D"/><rect x="545" y="284" width="15" height="15" fill="#00A57A"/><rect x="560" y="284" width="15" height="15" fill="#4DA3FF"/><rect x="575" y="284" width="15" height="15" fill="#00A57A"/><rect x="590" y="284" width="15" height="15" fill="#FFB547"/><rect x="605" y="284" width="15" height="15" fill="#C9D4CC"/><rect x="470" y="299" width="15" height="15" fill="#7C5CFF"/><rect x="485" y="299" width="15" height="15" fill="#7C5CFF"/><rect x="500" y="299" width="15" height="15" fill="#00A57A"/><rect x="515" y="299" width="15" height="15" fill="#C9D4CC"/><rect x="530" y="299" width="15" height="15" fill="#FFB547"/><rect x="545" y="299" width="15" height="15" fill="#00A57A"/><rect x="560" y="299" width="15" height="15" fill="#02221F"/><rect x="575" y="299" width="15" height="15" fill="#02221F"/><rect x="590" y="299" width="15" height="15" fill="#E5484D"/><rect x="605" y="299" width="15" height="15" fill="#02221F"/><rect x="470" y="314" width="15" height="15" fill="#4DA3FF"/><rect x="485" y="314" width="15" height="15" fill="#FFB547"/><rect x="500" y="314" width="15" height="15" fill="#00A57A"/><rect x="515" y="314" width="15" height="15" fill="#4DA3FF"/><rect x="530" y="314" width="15" height="15" fill="#02221F"/><rect x="545" y="314" width="15" height="15" fill="#7C5CFF"/><rect x="560" y="314" width="15" height="15" fill="#FFB547"/><rect x="575" y="314" width="15" height="15" fill="#02221F"/><rect x="590" y="314" width="15" height="15" fill="#F2FBF7"/><rect x="605" y="314" width="15" height="15" fill="#FF8A5B"/><rect x="470" y="329" width="15" height="15" fill="#C9D4CC"/><rect x="485" y="329" width="15" height="15" fill="#00A57A"/><rect x="500" y="329" width="15" height="15" fill="#E5484D"/><rect x="515" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="530" y="329" width="15" height="15" fill="#4DA3FF"/><rect x="545" y="329" width="15" height="15" fill="#E5484D"/><rect x="560" y="329" width="15" height="15" fill="#FFB547"/><rect x="575" y="329" width="15" height="15" fill="#FF8A5B"/><rect x="590" y="329" width="15" height="15" fill="#00A57A"/><rect x="605" y="329" width="15" height="15" fill="#FF8A5B"/><rect x="470" y="344" width="15" height="15" fill="#7C5CFF"/><rect x="485" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="344" width="15" height="15" fill="#FFB547"/><rect x="515" y="344" width="15" height="15" fill="#F2FBF7"/><rect x="530" y="344" width="15" height="15" fill="#FFB547"/><rect x="545" y="344" width="15" height="15" fill="#00A57A"/><rect x="560" y="344" width="15" height="15" fill="#00A57A"/><rect x="575" y="344" width="15" height="15" fill="#4DA3FF"/><rect x="590" y="344" width="15" height="15" fill="#FF8A5B"/><rect x="605" y="344" width="15" height="15" fill="#E5484D"/><rect x="470" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="485" y="359" width="15" height="15" fill="#F2FBF7"/><rect x="500" y="359" width="15" height="15" fill="#02221F"/><rect x="515" y="359" width="15" height="15" fill="#C9D4CC"/><rect x="530" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="545" y="359" width="15" height="15" fill="#00A57A"/><rect x="560" y="359" width="15" height="15" fill="#7C5CFF"/><rect x="575" y="359" width="15" height="15" fill="#FFB547"/><rect x="590" y="359" width="15" height="15" fill="#E5484D"/><rect x="605" y="359" width="15" height="15" fill="#F2FBF7"/></g></g><rect x="478" y="300" width="134" height="26" rx="6" fill="rgba(2,34,31,.72)"/><text x="545" y="318" class="t9" style="fill:#fff;font-size:15px">Boss, I am the AI.</text></g><text x="545" y="396" class="t3">Step 50: done</text></g><g class="p" style="--t:3.6s"><circle cx="545" cy="210" r="30" fill="rgba(255,255,255,.92)"/><path d="M537 196 l24 14 l-24 14z" fill="#02221F"/></g><g class="p" style="--t:3.9s"><rect x="438" y="118" width="96" height="30" rx="8" fill="#E5484D"/><text x="486" y="139" class="t3" style="fill:#fff;font-size:16px;font-weight:800">EP 1</text></g>
</svg>''',
# ---- 5 · agent: 1 WhatsApp order, it works through each system, then waits for you
'''<svg class="il" viewBox="0 0 640 440">
<g class="a" style="--t:.4s"><rect x="20" y="20" width="440" height="62" rx="22" fill="#DCF8C6"/><text x="44" y="59" class="t7">Mega Mart: 20 ctn Milo, Friday</text></g>
''' + ''.join('<g class="a" style="--t:%.2fs"><rect x="20" y="%d" width="600" height="60" rx="16" fill="#fff" stroke="#DDE3DF" stroke-width="2"/>'
              '<circle cx="56" cy="%d" r="16" fill="#DCE3DF"/><text x="90" y="%d" class="t7">%s</text><text x="600" y="%d" class="t3m" style="text-anchor:end">%s</text></g>'
              % (.7 + k * .15, 106 + k * 76, 136 + k * 76, 144 + k * 76, s_, 143 + k * 76, tool)
              for k, (s_, tool) in enumerate([('Read the order', 'WHATSAPP'), ('Check the stock', 'SQL ACCOUNT'), ('Draft the Sales Order', 'SALES ORDER'), ('Ask the boss', 'APPROVAL')])) + ''.join(
    '<g class="ok" style="--t:%.2fs"><g transform="translate(56 %d)"><circle r="16" fill="#006C48"/>%s</g></g>' % (1.5 + k * .6, 136 + k * 76, AA_TICK) for k in range(3)) + '''
<g class="p" style="--t:3.4s"><circle cx="56" cy="364" r="16" fill="#FFB547"/><circle class="ring" cx="56" cy="364" r="16" fill="none" stroke="#FFB547" stroke-width="3"/></g>
<g class="p" style="--t:3.5s"><rect x="300" y="346" width="170" height="36" rx="10" fill="#FFF1D6"/><text x="385" y="371" class="t3s2 h">Waiting for you</text></g>
</svg>''',
]
def _at_cards():
    out = ''
    for k, (_, nm, tg, do, like, how, ex, use, lim) in enumerate(AT_TYPES):
        chips = ''.join('<span>%s%s</span>' % (('<img src="../assets/logos/%s" alt="">' % AA_LOGO[x]) if x in AA_LOGO else '', x) for x in ex)
        dots = ''.join('<i class="%s"></i>' % ('on' if j == k else '') for j in range(5))
        out += ('<div class="dt" data-k="%d"><div class="fl"><div class="card">'
                '<div class="stage">%s</div>'
                '<div class="tx"><div class="top"><small>%s</small><span class="dots">%s</span></div><h2>%s</h2>'
                '<div class="like"><small>THINK OF IT LIKE</small><p>%s</p></div>'
                '<p class="how">%s</p>'
                '<div class="rw"><small>IN REAL LIFE</small><div class="chips">%s</div></div>'
                '<div class="rw"><small>IN YOUR COMPANY</small><p class="use">%s</p></div>'
                '<p class="lim">%s</p></div></div></div></div>'
                % (k + 1, AT_ILL[k], tg, dots, nm, like, how, chips, use, lim))
    return out
slide('08-ai-types', 'Types of AI', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.ty { display:grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 26px; margin-top: 60px; transform-origin: 50% 0;
  transition: transform 1.1s cubic-bezier(.2,.75,.15,1), opacity .9s ease; }
body:not([data-s="0"]) .ty { transform: translateY(-14px) scale(.94); opacity: .22; }
.ty > div { position:relative; padding: 30px 26px 30px; border-radius: 28px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); }
.ty .hd { display:flex; align-items:flex-start; justify-content:space-between; gap: 10px; }
.ty .tg { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; white-space: nowrap; color: var(--green); padding: 7px 11px; border-radius: 8px; background: var(--mint); border: 1px dashed rgba(0,108,72,.35); }
.ty .ic { flex:none; width: 84px; height: 84px; border-radius: 24px; background: var(--mint); color: var(--green); display:grid; place-items:center; }
.ty small { display:block; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; color: var(--ink-3); margin-top: 28px; }
.ty h2 { font-size: 42px; font-weight: 800; letter-spacing: -.025em; line-height: 1.05; margin-top: 8px; }
.ty .do { font-size: 29px; font-weight: 650; color: var(--green); margin-top: 10px; line-height: 1.25; }
.ty > div.now { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--neon), 0 50px 80px -40px rgba(0,108,72,.6); }
.ty .now .ic { background: rgba(0,245,169,.14); color: var(--neon); }
.ty .now small { color: var(--on-dark-3); } .ty .now .do { color: var(--neon); }
.ty .now .tg { color: var(--neon); background: rgba(0,245,169,.1); border-color: rgba(0,245,169,.4); }
.ty .now em { position:absolute; top: -18px; right: 24px; font-style: normal; font-size: 18px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  color: var(--ink); background: var(--neon); padding: 7px 14px; border-radius: 8px; }
''' + AA_CARD_CSS + '''
/* ---- scene parts only this slide uses ---- */
.il .car { opacity: 0; transform: translateY(46px) scale(.9); transform-box: fill-box; transform-origin: 50% 100%; }
.dt.go .il .car { animation: carin 1s cubic-bezier(.2,.7,.2,1) .3s forwards; }
@keyframes carin { to { opacity: 1; transform: none; } }
.il .arm { transform-box: view-box; transform-origin: 576px 235px; }
.dt.go .il .arm { animation: arm 1.1s cubic-bezier(.3,1.25,.5,1) 3s forwards; }
@keyframes arm { to { transform: rotate(86deg); } }
.il .dn { opacity: 1; } .dt.go .il .dn { animation: dnz 1.2s ease 2.9s forwards; } @keyframes dnz { to { opacity: 0; } }
.il .vb { transform-box: fill-box; transform-origin: center; }
.dt.go .il .vb { animation: vb .7s ease-in-out infinite alternate; animation-delay: var(--t); }
@keyframes vb { from { transform: scaleY(.35); } to { transform: scaleY(1); } }
''', '''
<div class="mk u" style="--d:.05s">Types of AI</div>
<h1 class="mt u" style="--d:.15s">5 types of AI, by <em>what they do</em></h1>
<p class="ml u" style="--d:.3s">You already use most of them every day. Today is about the last one.</p>
<div class="ty">''' + ''.join(
    '<div class="u%s" style="--d:%.2fs">%s<div class="hd"><span class="ic">%s</span><span class="tg">%s</span></div><small>TYPE %d</small><h2>%s</h2><p class="do">%s</p></div>'
    % (' now' if k == 4 else '', .55 + k * .18, '<em>Today</em>' if k == 4 else '', ic(p, 42, 1.9), tg, k + 1, nm, do)
    for k, (p, nm, tg, do, *_rest) in enumerate(AT_TYPES)) + '''</div>
<div class="stg">''' + _at_cards() + '''</div>
<script>
(function () {
  var B = document.body, cards = [].slice.call(document.querySelectorAll('.dt'));
  function set(n) {
    B.dataset.s = String(n);
    cards.forEach(function (c) {
      var k = +c.dataset.k;
      c.classList.toggle('past', k < n); var was = c.classList.contains('on');
      c.classList.toggle('on', k === n);
      if (k === n && !was) { c.classList.remove('go'); void c.offsetWidth; c.classList.add('go'); }
      if (k !== n) c.classList.remove('go');
    });
  }
  set(0);
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
''',
"\"Before we open up the brain, 1 quick map. People say AI as if it is 1 thing. It is not. Sort it by what it does and you get 5 types. You already use most of them every day. Let me show you where.\"\n\n(Next) Predictive AI, built on machine learning: \"Think of a weather forecast, but for your sales. When Grab tells you the driver arrives in 4 minutes, or your bank sends a fraud alert, or Shopee picks products for you, that is predictive AI. It learns from past numbers and guesses the next one: here, December, 1,240 cartons. In your company: who will pay late, what will run out. Its limit: a new product has no history.\"\n\n(Next) Vision AI, built on deep learning: \"You see this every day at the car park. The car rolls up, the camera reads WXY 1234, checks the season pass, and the barrier lifts. No ticket, no guard. Face unlock and Google Lens work the same way. In your company: reading a handwritten order or a bank slip. Dirty plate, bad light: it can misread.\"\n\n(Next) Voice AI: \"Hey Siri, YouTube captions, talking to your car. It turns sound into text. Your customer sends a voice note: Boss, esok hantar 10 carton Milo. It types it out, and it becomes an order line. A noisy shop or heavy slang, and it mishears sometimes.\"\n\n(Next) Diffusion AI, built on a diffusion model: \"Have you watched those AI short dramas on TikTok or YouTube? Many of them were never filmed. You type 1 line: the boss finds out his clerk is an AI. It starts from pure noise, like TV static, and cleans it a little at every step. Step 25, you can see a city. Step 50, done: episode 1. Midjourney and Sora work the same way. In your company: product photos and promo videos, without a studio. Hands, faces and words can still come out wrong, so check before you post.\"\n\n(Next) AI Agent, the LLM plus tools: \"This one does the work. 1 WhatsApp order: it reads it, checks the stock in SQL Account, drafts the Sales Order, and then waits for you. An agent uses the other 4 as its eyes, ears and voice. That is what today is about.\"\n\nThis slide has 5 extra Next presses; each card flies in, in 3D, and plays its own short scene.\nNext: \"The brain behind ChatGPT and every AI agent is the LLM. Let's open it up.\"")


# ---------------- 3 · machine learning ----------------
AA_ML_FLOW = [('You give it', 'Past examples', '3 years of invoices'),
              ('It finds', 'The pattern', 'by itself, no rules typed in'),
              ('It predicts', '1 thing', '&ldquo;Kedai Ali: 80% chance<br>of paying late&rdquo;')]
AA_ML_USE = [('Who will pay late?', 'learned from past invoices'),
             ('How much will we sell?', 'learned from past sales'),
             ('What will run out?', 'learned from stock movements')]

# ---------------- 4 · what is an LLM ----------------
slide('08-what-is-llm', 'What is an LLM?', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.ex { flex:1; display:flex; flex-direction:column; justify-content:center; }
.sn { display:flex; align-items:flex-start; gap: 22px; font-size: 76px; font-weight: 700; letter-spacing: -.03em; line-height: 1.1; }
.sn .bl { position:relative; display:inline-block; min-width: 330px; }
.sn .bl > span { color: var(--green); }
.sn .bl::after { content:""; position:absolute; left: 0; right: 0; top: 92px; height: 5px; border-radius: 3px; background: var(--green); }
.op { position:absolute; left: 0; top: 116px; display:grid; gap: 4px; font-size: 32px; font-weight: 600; letter-spacing: 0; }
.op span { color: var(--ink-3); opacity: .55; }
.op span:first-child { color: var(--green); opacity: 1; }
.ft { display:flex; justify-content:space-between; align-items:baseline; gap: 40px; margin-bottom: 8px; }
.ft b { font-size: 34px; font-weight: 700; }
.ft b em { font-style: normal; color: var(--green); }
.ft p { font-size: 22px; color: var(--ink-3); white-space: nowrap; }
.ft p span { font-weight: 650; color: var(--ink-2); }
.stg8 { position:relative; flex:1; }
.stg8 > .ex, .stg8 > .tk8 { position:absolute; inset: 0; transition: opacity .6s ease, transform .8s cubic-bezier(.2,.7,.2,1); }
.tk8 { display:flex; flex-direction:column; justify-content:center; opacity: 0; transform: translateY(26px); pointer-events: none; }
body[data-s="1"] .ex { opacity: 0; transform: translateY(-20px); }
body[data-s="1"] .tk8 { opacity: 1; transform: none; }
.tk8 [style*="--d"] { opacity: 0; transform: translateY(16px); transition: opacity .5s ease, transform .6s cubic-bezier(.3,1.3,.5,1); }
body[data-s="1"] .tk8 [style*="--d"] { opacity: 1; transform: none; transition-delay: var(--d); }
.pipe { display:flex; align-items:center; justify-content:space-between; gap: 18px; margin-top: 44px; }
.lg { display:flex; align-items:center; gap: 22px; padding: 18px 26px; border-radius: 20px; background: var(--mint); }
.lg .bk { display:grid; grid-template-columns: repeat(2, 30px); gap: 5px; flex:none; }
.lg .bk i { display:block; width: 30px; height: 22px; border-radius: 5px; box-shadow: inset 0 -4px 0 rgba(0,0,0,.15); }
.lg p { font-size: 34px; line-height: 1.3; color: var(--ink); } .lg p b { color: var(--green); }
.pipe .st { display:flex; flex-direction:column; align-items:center; gap: 16px; }
.pipe small { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .12em; color: var(--ink-3); text-transform: uppercase; }
.pipe .ar { display:flex; flex-direction:column; align-items:center; gap: 6px; color: var(--emerald); }
.pipe .bub { font-size: 34px; font-weight: 600; padding: 22px 26px; border-radius: 6px 28px 28px 28px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 24px 40px -30px rgba(2,34,31,.5); white-space: nowrap; }
.pipe .ch { display:flex; gap: 6px; }
.pipe .ch span { font-family: var(--mono); font-size: 34px; font-weight: 600; padding: 12px 8px; border-radius: 10px; white-space: pre; }
.pipe .ch span:nth-child(odd) { background: var(--mint); color: var(--green); } .pipe .ch span:nth-child(even) { background: #E8ECE9; color: var(--ink); }
.pipe .ch.nx span { background: var(--green) !important; color: #fff !important; box-shadow: 0 0 0 6px rgba(0,108,72,.15); }
.pipe .br { width: 130px; height: 130px; border-radius: 50%; background: var(--ink); color: var(--neon); display:grid; place-items:center; box-shadow: 0 0 50px rgba(0,165,122,.35); }
.fx { display:flex; justify-content:center; gap: 60px; margin-top: 50px; }
.fx > div { display:flex; align-items:center; gap: 18px; }
.fx .ic { width: 76px; height: 76px; border-radius: 22px; background: var(--mint); color: var(--green); display:grid; place-items:center; }
.fx b { font-size: 38px; font-weight: 750; letter-spacing: -.01em; }
''', '''
<div class="mk u" style="--d:.05s">Step 2 &middot; The brain</div>
<h1 class="mt u" style="--d:.15s">An LLM predicts the next word. <em>Very well.</em></h1>
<p class="ml u" style="--d:.3s"><b>LLM</b> = large language model. It learned which word usually comes next.</p>
<div class="stg8"><div class="ex">
  <div class="sn u" style="--d:.6s"><span>&ldquo;Terima kasih, see you</span><span class="bl"><span data-type="tomorrow&rdquo;" data-delay="1.7" data-cps="12"></span>
    <span class="op uf" style="--d:1.1s"><span>tomorrow</span><span>later</span><span>soon</span></span></span></div>
</div>
<div class="tk8">
  <div class="lg" style="--d:.1s"><span class="bk"><i style="background:#00A57A"></i><i style="background:#FFB547"></i><i style="background:#4DA3FF"></i><i style="background:#00A57A"></i></span><p>Think of <b>LEGO</b>: it breaks your message into small bricks called <b>tokens</b>, then adds <b>1 brick at a time</b>.</p></div>
  <div class="pipe">
    <div class="st" style="--d:.2s"><div class="bub">Terima kasih, see you&hellip;</div><small>Your message</small></div>
    <div class="ar" style="--d:.5s">''' + ic('<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4L8.1 15.9M14.5 14.5L20 20M8.1 8.1L12 12"/>', 44, 2) + '''<small>cut</small></div>
    <div class="st" style="--d:.7s"><div class="ch">''' + ''.join('<span style="--d:%.2fs">%s</span>' % (.8 + k * .08, t) for k, t in enumerate(['Ter', 'ima', ' kas', 'ih', ',', ' see', ' you'])) + '''</div><small>Tokens</small></div>
    <div class="ar" style="--d:1.4s">''' + ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 44, 2.2) + '''</div>
    <div class="st" style="--d:1.6s"><div class="br">''' + ic('<path d="M12 5a3 3 0 00-5.9-.7A3 3 0 004 9a3 3 0 00.5 5.5A3 3 0 008 19a3 3 0 004 1V5z"/><path d="M12 5a3 3 0 015.9-.7A3 3 0 0120 9a3 3 0 01-.5 5.5A3 3 0 0116 19a3 3 0 01-4 1"/>', 70, 1.6) + '''</div><small>LLM</small></div>
    <div class="ar" style="--d:1.9s">''' + ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 44, 2.2) + '''</div>
    <div class="st" style="--d:2.1s"><div class="ch nx"><span style="--d:2.2s"> tomorrow</span></div><small>Next token</small></div>
  </div>
  <div class="fx">
    <div style="--d:2.5s"><span class="ic">''' + ic('<rect x="2" y="8" width="20" height="8" rx="1.5"/><path d="M6 8v3M10 8v4M14 8v3M18 8v4"/>', 38, 2) + '''</span><b>100 words &asymp; 130 tokens</b></div>
    <div style="--d:2.7s"><span class="ic">''' + ic('<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4.5a1.5 1.5 0 010 3H10"/>', 38, 2) + '''</span><b>You pay per token, like a phone bill</b></div>
  </div>
</div></div>
</div></div>
<div class="ft u" style="--d:2.4s"><b>It does not look answers up. <em>It predicts them, 1 word at a time.</em></b>
  <p>You know it as <span>ChatGPT &middot; Claude &middot; Gemini &middot; DeepSeek</span></p></div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"ChatGPT, Claude, Gemini, DeepSeek. You know the names. Inside each one is the same kind of thing: an LLM, a large language model. Large, because it read a huge amount of text. Language, because words go in and words come out.\n\nWhat does it actually do? Only 1 thing. Let's try. Terima kasih, see you...\" (pause, let the room finish) \"...tomorrow. You did it too. It looked at the words so far and picked the most likely next word. Then the next. Then the next. Done well enough, that looks like understanding.\n\nRemember this sentence: it does not look answers up. It predicts them, 1 word at a time. Everything else today follows from that.\"\n\n(Next) \"1 small correction: it does not really see words. Think of LEGO: it breaks your message into small bricks called tokens, then builds the reply 1 brick at a time. A token is a small piece of text: a word, part of a word, or a comma. Terima kasih, see you tomorrow becomes 8 pieces: Ter, ima, kas, ih, comma, see, you, tomorrow. Short English words are 1 token; Malay words often become 2 or 3. Rule of thumb: 1 token is about three quarters of an English word. Why care? Because AI is measured in tokens: you pay per token, and its memory is counted in tokens. So when people say it predicts the next word, it really predicts the next token.\"\n\nThis slide has 1 extra Next press.\nNote: the split is an illustration; each model cuts text a little differently.\nNext: \"To predict that well, it had to read. A lot.\"")

# ---------------- 5 · how much it read (scene kept from the original) ----------------
AA_TOWERS = '''<svg class="tw" viewBox="0 0 160 400" fill="none">
<g fill="#0E3A33" stroke="#00F5A9" stroke-width="2.5" stroke-linejoin="round">
<path d="M14 400V120l8-16v-20l6-10 6 10v20l8 16v280z"/><path d="M28 74V20"/>
<path d="M104 400V120l8-16v-20l6-10 6 10v20l8 16v280z"/><path d="M118 74V20"/>
<path d="M42 210h62v14H42z" fill="#00F5A9" fill-opacity=".25"/></g>
<g stroke="rgba(0,245,169,.35)" stroke-width="1.5">''' + ''.join('<path d="M18 %d h20M108 %d h20"/>' % (y, y) for y in range(140, 395, 18)) + '''</g></svg>'''
AA_FACTS = [('13,000', 'Twin Towers high, if you stacked the books', 4.2),
            ('800', 'football fields, if you laid the books flat', 6.6),
            ('50 trips', 'to the Moon, with the pages end to end', 8.8)]
slide('08-how-much-it-read', 'How much an AI has read', SEC[2], 'dark', 'data-sparks="none"', MIN_CSS + '''
.slide { padding-top: 112px; }
.wrap { flex:1; display:grid; grid-template-columns: 1fr 800px; gap: 50px; }
.lf { display:flex; flex-direction:column; }
.h2 { color: var(--on-dark-2); font-weight: 500; font-size: 36px; margin-top: 18px; }
.hero { font-size: 170px; font-weight: 800; letter-spacing: -.055em; line-height: .9; margin-top: 14px; white-space: nowrap; }
.hero small { display:block; font-size: 64px; font-weight: 700; letter-spacing: -.03em; color: var(--neon); margin-top: 6px; }
.bk { font-size: 34px; color: var(--on-dark-2); margin-top: 26px; }
.bk b { color: var(--on-dark); font-weight: 650; }
.facts { margin-top: auto; margin-bottom: 10px; display:grid; gap: 0; }
.fx { display:grid; grid-template-columns: 210px 1fr; align-items:baseline; gap: 20px; padding: 16px 0; border-top: 1px solid rgba(242,251,247,.16); }
.fx b { font-size: 42px; font-weight: 750; letter-spacing: -.02em; color: var(--neon); white-space: nowrap; }
.fx span { font-size: 26px; line-height: 1.3; color: var(--on-dark-2); }
/* the scene */
.sc { position:relative; height: 860px; margin-top: -60px; border-radius: 30px; overflow:hidden;
  background: linear-gradient(to top, rgba(0,245,169,.06), transparent 40%); }
.ground { position:absolute; left: 0; right: 0; bottom: 70px; height: 2px; background: rgba(242,251,247,.25); }
.zoom { position:absolute; left: 0; right: 0; bottom: 72px; top: 0; transform-origin: 20% 100%; }
@keyframes zoomout { to { transform: scale(.1); } }
.tw { position:absolute; left: 180px; bottom: 0; width: 160px; height: 400px; }
.stack { position:absolute; left: 400px; bottom: 0; width: 150px; height: 0;
  background: repeating-linear-gradient(to top, #FFB547 0 18px, #0E3A33 18px 20px, #00C389 20px 40px, #0E3A33 40px 42px, #7C5CFF 42px 60px, #0E3A33 60px 62px, #F2FBF7 62px 80px, #0E3A33 80px 82px, #FF8A5B 82px 100px, #0E3A33 100px 102px);
  border-radius: 4px; box-shadow: 0 0 40px rgba(0,245,169,.25);
  animation: pile 2.4s cubic-bezier(.3,.1,.3,1) .8s forwards, sky 2.6s cubic-bezier(.6,0,.2,1) 3.6s forwards; }
@keyframes pile { to { height: 400px; } }
@keyframes sky { from { height: 400px; } to { height: 8200px; } }
.cap1 { position:absolute; left: 400px; bottom: 490px; font-size: 26px; font-weight: 700; color: var(--on-dark); opacity: 0; animation: fade .5s ease 2.6s forwards, fadeout .4s ease 3.4s forwards; }
@keyframes fadeout { to { opacity: 0; } }
.cnt { position:absolute; right: 40px; top: 40px; text-align:right; opacity: 0; }
.cnt b { display:block; font-size: 120px; font-weight: 800; letter-spacing: -.04em; color: var(--neon); line-height: 1; }
.cnt > span { font-size: 30px; color: var(--on-dark); font-weight: 600; }
.tiny { position:absolute; left: 30%; bottom: 76px; transform: translateX(-50%); font-size: 22px; color: var(--on-dark-2); opacity: 0; white-space: nowrap; }
.ht { position:absolute; right: 40px; top: 230px; text-align:right; opacity: 0; animation: fade .6s ease 6.3s forwards, fadeout .5s ease 7.9s forwards; }
.ht b { display:block; font-size: 76px; font-weight: 800; letter-spacing: -.03em; color: var(--on-dark); line-height: 1; }
.ht span { font-size: 26px; color: var(--on-dark-2); }
.ht em { font-style: normal; color: var(--neon); font-weight: 700; }
.cnt { animation: fade .6s ease 3.8s forwards, fadeout .5s ease 7.9s forwards; }
.tiny { animation: fade .6s ease 5.6s forwards, fadeout .5s ease 7.9s forwards; }
.ground { animation: fadeout .5s ease 7.9s forwards; }
.zoom { animation: zoomout 2.6s cubic-bezier(.6,0,.2,1) 3.6s forwards, fadeout .5s ease 7.9s forwards; }
.space { position:absolute; inset: 0; opacity: 0; animation: fade .9s ease 8.1s forwards;
  background: radial-gradient(1.5px 1.5px at 12% 22%, #fff8, transparent), radial-gradient(1.5px 1.5px at 72% 12%, #fff8, transparent), radial-gradient(1px 1px at 40% 64%, #fff6, transparent), radial-gradient(1px 1px at 86% 70%, #fff6, transparent), radial-gradient(1.5px 1.5px at 58% 38%, #fff7, transparent), radial-gradient(1px 1px at 24% 84%, #fff6, transparent); }
.space svg { position:absolute; inset: 0; width: 100%; height: 100%; }
.space .tl { font: 600 24px var(--sans, Figtree); fill: var(--on-dark-2); }
.space .tb { font: 800 26px var(--sans, Figtree); fill: var(--on-dark); }
.mc { position:absolute; left: 40px; top: 36px; max-width: 560px; }
.mc b { display:block; font-size: 96px; font-weight: 800; letter-spacing: -.04em; color: var(--neon); line-height: 1; }
.mc > span { font-size: 28px; color: var(--on-dark); font-weight: 600; }
html.static .ht, html.static .cnt, html.static .tiny { display:none; }
html.static .zoom { transform: scale(.1); } html.static .stack { height: 8200px; } html.static .cap1 { display:none; }
/* ---- step 0: what an LLM is ---- */
.intro { flex:1; display:flex; flex-direction:column; }
body:not([data-s="0"]) .intro { display:none; }
.guess { flex:1; display:none; flex-direction:column; }
body[data-s="1"] .guess { display:flex; }
.gq { display:grid; grid-template-columns: repeat(4, 1fr); gap: 28px; margin-top: auto; margin-bottom: 40px; }
.gq > div { position:relative; display:flex; flex-direction:column; padding: 30px 30px 28px; border-radius: 28px; background: rgba(242,251,247,.06); box-shadow: 0 0 0 1px rgba(242,251,247,.14); }
.gq .lt { width: 72px; height: 72px; border-radius: 50%; display:grid; place-items:center; font-size: 38px; font-weight: 800; color: #02221F; background: var(--neon); }
.gq .bks { display:flex; align-items:flex-end; gap: 4px; height: 100px; margin-top: 20px; }
.gq .bks i { flex:1; border-radius: 4px 4px 0 0; background: repeating-linear-gradient(to top, #FFB547 0 14px, #03201C 14px 16px, #00C389 16px 30px, #03201C 30px 32px, #7C5CFF 32px 46px, #03201C 46px 48px);
  transform-origin: bottom; transform: scaleY(0); animation: gbk 1s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: var(--d); }
@keyframes gbk { to { transform: none; } }
html.static .gq .bks i { transform: none; animation: none; }
.gq b { display:block; font-size: 44px; font-weight: 800; letter-spacing: -.03em; line-height: 1.05; margin-top: 16px; }
.gq b small { display:block; font-size: 28px; font-weight: 650; color: var(--on-dark-2); letter-spacing: -.01em; margin-top: 4px; }
.gq .sk { display:flex; align-items:center; gap: 14px; margin-top: 18px; padding: 14px 16px; border-radius: 16px; background: rgba(0,245,169,.08); }
.gq .sk i { flex:none; width: 50px; height: 50px; border-radius: 14px; display:grid; place-items:center; background: rgba(0,245,169,.16); color: var(--neon); }
.gq .sk div { font-size: 22px; line-height: 1.3; color: var(--on-dark-2); }
.gq .sk span { display:block; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .14em; color: var(--on-dark-3); }
.gq .sk em { font-style: normal; font-weight: 800; color: var(--neon); }
.gq p { margin-top: 14px; padding-top: 16px; border-top: 1px solid rgba(242,251,247,.16); font-size: 24px; color: var(--on-dark-2); }
.gq p span { display:block; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .14em; color: var(--on-dark-3); margin-bottom: 4px; }
.gq p em { font-style: normal; font-weight: 700; color: var(--on-dark); }
.hand { display:inline-flex; align-items:center; gap: 14px; margin-top: 30px; font-size: 30px; font-weight: 650; color: var(--neon); }
#p2host { flex:1; display:none; }
body[data-s="2"] #p2host { display:flex; }
.intro .lgs { margin-bottom: 20px; }
#p2host > .wrap { flex:1; }
.intro .mt { max-width: 1500px; }
.lgs { display:flex; gap: 14px; margin-top: 34px; }
.lgs span { display:flex; align-items:center; gap: 10px; font-size: 26px; font-weight: 650; padding: 10px 20px; border-radius: 999px; background: rgba(242,251,247,.08); box-shadow: 0 0 0 1px rgba(242,251,247,.14); }
.lgs img { width: 26px; height: 26px; filter: brightness(0) invert(1); }
.intro .m3 { margin-bottom: 30px; }
.intro .m3 b em { font-style: normal; color: var(--neon); }
.tkn { font-size: 26px; color: var(--on-dark-2); margin-bottom: 40px; } .tkn b { color: var(--on-dark); }
''', '''
<div class="intro">
  <div class="mk u" style="--d:.05s">The brain</div>
  <h1 class="mt u" style="--d:.15s">An LLM is a brain that learned <em>language</em></h1>
  <p class="ml u" style="--d:.3s"><b>LLM</b> = Large Language Model. It learned how people write by reading a <b>huge amount of text</b>.</p>
  <div class="lgs u" style="--d:.45s"><span><img src="../assets/logos/openai.svg" alt="">ChatGPT</span><span><img src="../assets/logos/claude.svg" alt="">Claude</span><span>Gemini</span><span>DeepSeek</span></div>
  <div class="m3">
    <div class="u" style="--d:.7s"><b><em>Large</em></b><p>Trained on a huge amount of data: websites, books and news, in 100+ languages.</p></div>
    <div class="u" style="--d:.85s"><b><em>Language</em></b><p>Words go in, words come out. It reads and writes like a person.</p></div>
    <div class="u" style="--d:1s"><b><em>Model</em></b><p>It learned the patterns, so it can guess the next word, 1 at a time.</p></div>
  </div>
  <p class="tkn u" style="--d:1.2s">It reads text in small pieces called <b>tokens</b>. 1 token &asymp; &frac34; of a word.</p>
</div>
<div class="guess">
  <div class="mk u" style="--d:.05s">Quick guess</div>
  <h1 class="mt u" style="--d:.15s">How much did an LLM read to <em>learn language</em>?</h1>
  <div class="hand u" style="--d:.35s">''' + ic(HAND, 40, 2) + '''Raise your hand: A, B, C or D?</div>
  <div class="gq"><div class="u" style="--d:0.60s"><span class="lt">A</span><div class="bks"><i style="--d:0.90s;height:8%"></i></div><b>10,000<small>books</small></b><div class="sk"><i><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21V7l4-4 4 4v14"/><path d="M6 21h12M10 10h4M10 14h4M10 18h4"/></svg></i><div><span>STACKED UP</span><em>250 m</em> a 70-storey tower</div></div><p><span>READING 1 BOOK A DAY</span><em>27 years</em></p></div><div class="u" style="--d:0.80s"><span class="lt">B</span><div class="bks"><i style="--d:1.10s;height:14%"></i><i style="--d:1.14s;height:21%"></i><i style="--d:1.18s;height:28%"></i></div><b>1 million<small>books</small></b><div class="sk"><i><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20l7-12 4 6 3-4 6 10z"/><path d="M8.2 10.5l1.8 1.5 1.5-1.3"/></svg></i><div><span>STACKED UP</span><em>25 km</em> 6 Mount Kinabalus</div></div><p><span>READING 1 BOOK A DAY</span><em>2,700 years</em></p></div><div class="u" style="--d:1.00s"><span class="lt">C</span><div class="bks"><i style="--d:1.30s;height:20%"></i><i style="--d:1.34s;height:27%"></i><i style="--d:1.38s;height:34%"></i><i style="--d:1.42s;height:41%"></i><i style="--d:1.46s;height:48%"></i><i style="--d:1.50s;height:55%"></i><i style="--d:1.54s;height:62%"></i></div><b>20 million<small>books</small></b><div class="sk"><i><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M3 4l4 4M17 16l4 4M7 4L4 7M20 17l-3 3M12 9V5M12 19v-4"/></svg></i><div><span>STACKED UP</span><em>500 km</em> past the space station</div></div><p><span>READING 1 BOOK A DAY</span><em>55,000 years</em></p></div><div class="u" style="--d:1.20s"><span class="lt">D</span><div class="bks"><i style="--d:1.50s;height:26%"></i><i style="--d:1.54s;height:33%"></i><i style="--d:1.58s;height:40%"></i><i style="--d:1.62s;height:47%"></i><i style="--d:1.66s;height:54%"></i><i style="--d:1.70s;height:61%"></i><i style="--d:1.74s;height:68%"></i><i style="--d:1.78s;height:75%"></i><i style="--d:1.82s;height:82%"></i><i style="--d:1.86s;height:89%"></i><i style="--d:1.90s;height:96%"></i><i style="--d:1.94s;height:100%"></i><i style="--d:1.98s;height:100%"></i><i style="--d:2.02s;height:100%"></i></div><b>100 million<small>books</small></b><div class="sk"><i><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg></i><div><span>STACKED UP</span><em>2,500 km</em> 6x the space station</div></div><p><span>READING 1 BOOK A DAY</span><em>274,000 years</em></p></div></div>
</div>
<template id="p2"><div class="wrap">
  <div class="lf">
    <div class="mk u" style="--d:.05s">How much it read</div>
    <h2 class="h2 u" style="--d:.15s">Even more than D. DeepSeek V4 (2026) read about</h2>
    <div class="hero u" style="--d:.3s"><span data-count="240" data-zh="2.4" data-zhdec="1" data-delay=".5" data-dur="1.6">0</span> million<small>books of 400 pages</small></div>
    <p class="bk u" style="--d:.7s">&asymp; <b>32 trillion tokens</b> of text</p>
    <div class="facts">''' + ''.join('<div class="fx u" style="--d:%.1fs"><b>%s</b><span>%s</span></div>' % (d_, n, t) for n, t, d_ in AA_FACTS) + '''</div>
  </div>
  <div class="sc">
    <div class="zoom">''' + AA_TOWERS + '''<div class="stack"></div></div>
    <div class="cap1">= 1 Twin Tower</div>
    <div class="ground"></div>
    <div class="tiny">the Twin Towers, 452 m</div>
    <div class="ht"><b>&asymp; 6,000 km</b><span>tall: <em>15x higher</em> than the space station</span></div>
    <div class="space"><svg viewBox="0 0 800 860">
      <defs><radialGradient id="ea" cx=".35" cy=".35"><stop offset="0" stop-color="#4DA3FF"/><stop offset=".6" stop-color="#0B6E5A"/><stop offset="1" stop-color="#05362D"/></radialGradient>
      <radialGradient id="mo" cx=".35" cy=".35"><stop offset="0" stop-color="#F2F4F3"/><stop offset="1" stop-color="#8A9A95"/></radialGradient></defs>
      <path id="tr" d="M190 660 C 330 420, 470 330, 640 250" fill="none" stroke="rgba(0,245,169,.35)" stroke-width="3" stroke-dasharray="6 10"/>
      <circle cx="150" cy="700" r="100" fill="url(#ea)"/><circle cx="150" cy="700" r="100" fill="none" stroke="rgba(77,163,255,.5)" stroke-width="10" stroke-opacity=".25"/>
      <circle cx="660" cy="240" r="44" fill="url(#mo)"/>
      <circle r="9" fill="#00F5A9"><animateMotion dur="1.4s" begin="8.6s" repeatCount="indefinite" keyPoints="0;1;0" keyTimes="0;.5;1" calcMode="linear"><mpath href="#tr"/></animateMotion></circle>
      <text class="tb" x="150" y="840" text-anchor="middle">Earth</text><text class="tb" x="660" y="320" text-anchor="middle">Moon</text>
      <text class="tl" x="440" y="520" text-anchor="middle" transform="rotate(-33 440 470)">384,400 km</text>
    </svg>
    <div class="mc"><b>&times;<span data-count="50" data-delay="8.6" data-dur="2.2">0</span></b><span>trips to the Moon, with the pages<br>laid end to end</span></div></div>
    <div class="cnt"><b>&times;<span data-count="13000" data-delay="3.8" data-dur="2.4">0</span></b><span>Twin Towers of books</span></div>
  </div>
</div>
</template>
<div id="p2host"></div>
<script>
(function () {
  var B = document.body, host = document.getElementById('p2host'), tpl = document.getElementById('p2');
  var STATIC = document.documentElement.classList.contains('static');
  var fmt = function (n) { return n.toLocaleString('en-US'); };
  function counters(root) {
    root.querySelectorAll('[data-count]').forEach(function (el) {
      var ZH = /^zh/.test(document.documentElement.lang) && el.dataset.zh;
      var to = parseFloat(ZH ? el.dataset.zh : el.dataset.count), dec = ZH ? parseInt(el.dataset.zhdec || '0', 10) : 0;
      var dur = (parseFloat(el.dataset.dur) || 1.4) * 1000, delay = (parseFloat(el.dataset.delay) || 0) * 1000;
      var show = function (v) { el.textContent = dec ? v.toFixed(dec) : fmt(Math.round(v)); };
      if (STATIC) { show(to); return; }
      show(0);
      setTimeout(function () {
        var t0 = performance.now();
        (function tick(t) { var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 4); show(to * e); if (p < 1) requestAnimationFrame(tick); })(t0);
      }, delay);
    });
  }
  function set(n) {
    B.dataset.s = String(n);
    host.innerHTML = '';
    if (n >= 2) { host.appendChild(tpl.content.cloneNode(true)); counters(host); }
  }
  set(0);
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
''',
"\"ChatGPT, Claude, Gemini, DeepSeek. You know the names. Inside each one is the same thing: an LLM, a large language model. Large, because it was trained on a huge amount of data: websites, books, news, in more than 100 languages. Language, because words go in and words come out. Model, because it learned the patterns of how people write, so it can guess the next word, 1 at a time. It reads text in small pieces called tokens; 1 token is about three quarters of a word.\"\n\n(Next) \"Quick guess. To learn language, how much did it read? A, 10,000 books. B, 1 million. C, 20 million. D, 100 million. Stacked up, A is a 70-storey tower. B is 6 Mount Kinabalus. C goes past the space station. D is 6 times higher than the space station. If you read 1 book a day, A takes you 27 years. D takes you 274,000 years. Raise your hand: A? B? C? D?\" (count the hands, then Next)\n\n(Next) \"Who said D? Still not enough. Take DeepSeek V4, from 2026: about 240 million books of 400 pages, more than 2 times D. In tokens, those small pieces of text, that is more than 32 trillion. 2 years earlier, Llama 3 read 15 trillion, about 110 million books, so it doubled in 2 years.\n\nWatch: if you stacked the books...\" (the pile reaches the top of the Twin Towers) \"...that is 1 Twin Tower. Keep going.\" (the view pulls back) \"13,000 Twin Towers. The pile is about 6,000 km tall, 15 times higher than the space station. Laid flat, the books would cover 800 football fields.\" (the view changes to Earth and Moon) \"And if you tore out every page and laid them end to end, they would reach the Moon 50 times over.\"\n\nNote: rough figures from the published token counts (DeepSeek-V4 paper: 32T+ tokens; Meta: Llama 3, 15T+). Working: 1 token = 0.75 word; a 400-page book = 100,000 words, 2.5 cm thick, 12 x 20 cm pages; a football field = 7,140 m2. Say \"about\". The stack itself does not reach the Moon; the pages laid end to end do.\nThis slide has 2 extra Next presses: the LLM intro, the guess (A to D; the real answer is even bigger than D), then the 32 trillion scene.\nNext: \"So it is a very clever brain. But can it do your work? Not on its own.\"")

# ---------------- 6 · what it read, and never saw ----------------
AA_GLOBE = '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>'
AA_BOOK = '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/>'
AA_NEWS = '<path d="M4 6h13v13H6a2 2 0 01-2-2z"/><path d="M17 9h3v8a2 2 0 01-2 2M8 10h5M8 14h5"/>'
AA_LANG = '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>'
AA_READ = [(AA_GLOBE, 'Public websites'), (AA_BOOK, 'Books'), (AA_NEWS, 'News and Wikipedia'),
           (AA_LANG, 'English, Malay, &#20013;&#25991;, &#2980;&#2990;&#3007;&#2996;&#3021; + 100 more')]
AA_NEVER = ['Your customers and their prices', 'Your stock and your accounts', 'Your WhatsApp chats', 'Your SOP: who approves what']
# ---------------- How an LLM works, in 5 steps (merges: what it read, tokens, meaning map, how it learned, next word, makes things up) ----------------
LH_STEPS = [('Learn', 'It read the world'), ('Cut', 'Text into tokens'), ('Map', 'Meaning as a map'), ('Write', '1 word at a time'), ('Watch out', 'Sure, even when wrong')]
LH_TOKS = ['Pls', ' arrange', ' delivery', ' be', '4', ' 12', 'pm', ',', ' b', 'wg', ' bes', 'ar', ' 10', 'kg', ' x', ' 20']
def _lh_panels():
    chips = ''.join('<span style="--d:%.2fs">%s</span>' % (.3 + k * .06, t) for k, t in enumerate(LH_TOKS))
    loop = ''.join('<span style="--d:%.2fs"><i>%d</i>%s</span>' % (.3 + k * .2, k + 1, t) for k, t in enumerate(['Guess the next word', 'Check', 'Adjust', 'Repeat']))
    bars = ''.join('<div class="br" style="--d:%.2fs"><span>%s</span><i><b style="--w:%d%%"></b></i><em>%d%%</em></div>' % (.4 + k * .15, w, p, p) for k, (w, p) in enumerate([('breakfast', 82), ('lunch', 9), ('dinner', 6)]))
    mp = ('<div class="mp"><div class="cl on" style="--d:.3s"><small>ONIONS</small><span>bawang</span><span>onion</span><span>&#27915;&#33905;</span><span class="sf">bwg</span></div>'
          '<div class="cl" style="--d:.5s"><small>DRINKS</small><span>Milo</span><span>Horlicks</span><span>teh tarik</span></div>'
          '<div class="cl" style="--d:.7s"><small>MONEY</small><span>invoice</span><span>bil</span><span>bayar</span></div></div>')
    P = [
        ('<div class="lp">' + loop + '<em style="--d:1.1s">trillions of times</em></div>'
         '<div class="two"><div style="--d:1.2s"><small>IT READ</small><p>Websites, books, news, in 100+ languages</p></div>'
         '<div class="no" style="--d:1.35s"><small>IT NEVER SAW</small><p>Your prices, stock, chats or SOP</p></div></div>',
         'It read the internet and played 1 game: <b>guess the next word</b>, trillions of times.', 'So it knows the world, <b>not your company</b>.'),
        ('<div class="tk"><div class="msg" style="--d:.2s">Pls arrange delivery be4 12pm, bwg besar 10kg x 20</div><div class="ch">' + chips + '</div>'
         '<p class="ct" style="--d:1.4s"><b>16 tokens</b> for 9 words</p></div>',
         'It cuts text into small pieces called <b>tokens</b>. 1 token &asymp; &frac34; of a word.', 'You <b>pay per token</b>, and it can hold about 1 million at once.'),
        (mp, 'Words used the same way <b>sit close together</b>.', 'So it understands <b>BM, English, Chinese</b> and short forms like &ldquo;bwg&rdquo;.'),
        ('<div class="nx"><p class="q" style="--d:.2s">&ldquo;Nasi lemak is usually eaten for <u>breakfast</u>&rdquo;</p>' + bars + '</div>',
         'It scores every possible next word and <b>picks the most likely</b>.', 'Then the next word, and the next. That is how it writes.'),
        ('<div class="cs"><div class="c1" style="--d:.2s"><small>NO FACTS</small><p class="b">Kedai Ali&rsquo;s credit limit is <b class="am">RM10,000</b>.</p><em class="am">Made up</em></div>'
         '<div class="c2" style="--d:.5s"><small>LOOKED UP IN YOUR RECORDS</small><p class="b"><b>RM5,000.</b> Only RM180 left.</p><em>Correct</em></div></div>',
         'With no facts, it <b>guesses</b>, and still sounds sure. This is called <b>hallucination</b>.', 'Fix: let it <b>look up your records</b>, and a person checks.'),
    ]
    out = ''
    for k, (vis, a, b) in enumerate(P):
        out += '<div class="pn" data-s="%d"><div class="vis">%s</div><div class="tx"><p class="a">%s</p><p class="b2">%s</p></div></div>' % (k + 1, vis, a, b)
    return out



# ---------------- slide: 70 years of AI ----------------
HIST = [('1950s&ndash;80s', 'Rules', 'People wrote every if-then rule by hand.', '&ldquo;If over the limit, block it.&rdquo;'),
        ('2000s', 'Machine learning', 'It learns patterns from past examples.', 'Spam filters, credit scores'),
        ('2012', 'Deep learning', 'Many-layer neural networks. AlexNet beats everyone at recognising photos.', 'Photo recognition'),
        ('2010s', 'Speech, vision, recommendations', 'Deep learning goes into everyday apps.', 'Siri, face unlock, &ldquo;you may also like&rdquo;'),
        ('2017', 'Transformer', 'A new design that reads a whole sentence at once.', 'The &ldquo;T&rdquo; in ChatGPT'),
        ('2018&ndash;20', 'LLM', 'Transformers trained on the internet start to write like people.', 'GPT-3 (2020)'),
        ('2023', 'Multimodal', 'It reads photos, PDFs and voice, not only text.', 'Snap a delivery order'),
        ('2025', 'Agentic AI', 'It uses tools and works in a loop until the job is done.', 'You are here')]
def _hist():
    out = ''
    for k, (y, t, d_, eg) in enumerate(HIST):
        out += ('<div class="st%s" style="--k:%d;--d:%.2fs"><div class="cd"><small>%s</small><b>%s</b><p>%s</p><em>%s</em></div></div>'
                % (' now' if k == len(HIST) - 1 else '', k, .5 + k * .16, y, t, d_, eg))
    return out

# ---------------- slide: machine learning ----------------
ML = [('<path d="M12 3v6M12 9l-5 5M12 9l5 5M7 14v4M17 14v4"/><circle cx="12" cy="3" r="1.5"/>', 'Random forest', 'Hundreds of small decision trees each give an answer, then they vote.', 'Will this customer pay late?'),
      ('<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>', 'XGBoost', 'Trees built 1 after another. Each new tree fixes the last one&rsquo;s mistakes.', 'How much will we sell next month?'),
      ('<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>', 'LightGBM', 'The same idea, built for speed on very big tables.', 'Which items will run out this week?'),
      ('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>', 'CNN', 'A neural network that looks at a picture in small squares.', 'Read a handwritten order, spot a damaged carton')]

LLM_LETTERS = [('L', 'Large', 'It read trillions of words, and holds what it learned in hundreds of billions of numbers.'),
               ('L', 'Language', 'Words in, words out. Today also photos, voice notes and PDFs.'),
               ('M', 'Model', 'Not a library of facts. A pattern of how language works, squeezed into those numbers.')]
LLMS = [('ChatGPT', 'OpenAI', 'openai.svg'), ('Claude', 'Anthropic', 'claude.svg'), ('Gemini', 'Google', ''), ('DeepSeek', 'DeepSeek', '')]


# ---------------- slide: how much an AI has read (book stack vs Twin Towers) ----------------
TOWERS = '''<svg class="tw" viewBox="0 0 160 400" fill="none">
<g fill="#0E3A33" stroke="#00F5A9" stroke-width="2.5" stroke-linejoin="round">
<path d="M14 400V120l8-16v-20l6-10 6 10v20l8 16v280z"/><path d="M28 74V20"/>
<path d="M104 400V120l8-16v-20l6-10 6 10v20l8 16v280z"/><path d="M118 74V20"/>
<path d="M42 210h62v14H42z" fill="#00F5A9" fill-opacity=".25"/></g>
<g stroke="rgba(0,245,169,.35)" stroke-width="1.5">''' + ''.join('<path d="M18 %d h20M108 %d h20"/>' % (y, y) for y in range(140, 395, 18)) + '''</g></svg>'''


# ---------------- slide: what it read, and what it never saw ----------------
READ_SRC = [('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>', 'Web pages', 'Billions of public sites'),
            ('<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/>', 'Books', 'Novels to accounting'),
            ('<path d="M4 4h16v16H4z"/><path d="M8 8h8M8 12h8M8 16h5"/>', 'Wikipedia', 'In 300+ languages'),
            ('<path d="M4 6h13v13H6a2 2 0 01-2-2z"/><path d="M17 9h3v8a2 2 0 01-2 2M8 10h5M8 14h5"/>', 'News', 'Years of articles'),
            ('<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>', 'Code', 'How software is written'),
            ('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>', 'Forums', 'People asking, people answering')]
NEVER = ['Your customers and their special prices', 'Your stock and your accounts in SQL Account', 'Your WhatsApp chats with customers',
         'Your SOP: who approves, who always pays late', 'Anything after its training cut-off date']

# ---------------- slide: tokens and the context window ----------------
TOKS = ['Pls', ' arrange', ' delivery', ' be', '4', ' 12', 'pm', ',', ' b', 'wg', ' bes', 'ar', ' 10', 'kg', ' x', ' 20']
TOK_CARDS = [('1 token &asymp; &frac34; of a word', '100 English words is about 130 tokens. Malay, Chinese and short forms like &ldquo;be4&rdquo; use more.'),
             ('You pay per token', 'Every question and every answer is counted, like a phone bill. A long PDF costs more than a short chat.'),
             ('Its desk has a size', 'The <b>context window</b>: how much it can hold at once. Today about 100,000 to 1,000,000 tokens, a 300-page book or more. In a very long chat, early details start to slip.')]
# ---- batch B: slides 7-13 of "What is an AI Agent?" (minimal redesign) ----

# ---------------- 7 · tokens ----------------
AB_TOKS = ['Pls', ' arrange', ' delivery', ' be', '4', ' 12', 'pm', ',', ' b', 'wg', ' bes', 'ar', ' 10', 'kg', ' x', ' 20']
AB_IDS = [3427, 31408, 9578, 387, 19, 220, 4013, 11, 293, 70, 9435, 277, 220, 7501, 865, 508]
AB_LANG = [('English', ['Please', ' deliver', ' tomorrow'], 'cheapest'),
           ('Malay', ['Tol', 'ong', ' hant', 'ar', ' es', 'ok'], ''),
           ('Chinese', ['请', '明天', '送', '货'], ''),
           ('Short forms', ['pl', 's', ' del', ' tmr', ' be', '4', ' 12'], 'costs more')]
AB_WHY = [('<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4.5a1.5 1.5 0 010 3H10"/>', 'You pay per token', 'In and out, like a phone bill.',
           [('1 WhatsApp order', '&asymp; 30'), ('A 10-page PDF', '&asymp; 6,500')]),
          ('<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18"/>', 'It can only hold so much', 'Its desk has a size: the context window.',
           [('Big models today', '&asymp; 1 million'), ('That is about', '7 books')]),
          ('<path d="M5 12h14M13 6l6 6-6 6"/>', 'It writes 1 token at a time', 'Speed = tokens per second.',
           [('A fast model', '&asymp; 100 a second'), ('A long answer', 'a few seconds')])]
def AB_tok_chips(toks, d0, step=.08, cls=''):
    return ''.join('<span class="%s" style="--d:%.2fs">%s</span>' % (cls, d0 + k * step, t) for k, t in enumerate(toks))

# ---------------- 8 · meaning map ----------------
AB_MAP = [  # label, centre, words (dx, dy), highlighted?
    ('Onions', (240, 205), [('bawang', -95, -20), ('bwg', -75, 40), ('onion', 30, -60), ('&#27915;&#33905;', 45, 30)], True),
    ('Drinks', (730, 175), [('Milo', -70, -20), ('Horlicks', 20, -55), ('teh tarik', 30, 25), ('Nescafe', -85, 55)], False),
    ('Money', (250, 485), [('invoice', -95, -25), ('bil', 50, -45), ('bayar', -50, 50), ('payment', 40, 25)], False),
    ('When', (740, 475), [('esok', -80, -25), ('tomorrow', 15, -50), ('pagi', -70, 50), ('be4 12pm', 20, 30)], False),
]
def AB_map_svg():
    out = ''
    for g, (lab, (cx, cy), words, hi) in enumerate(AB_MAP):
        d0 = (.7 if hi else 1.5 + (g - 1) * .3)
        out += '<g class="uf %s" style="--d:%.2fs"><circle class="zone" cx="%d" cy="%d" r="122"/><text class="gl" x="%d" y="%d">%s</text>' % (
            'hi' if hi else 'lo', d0, cx, cy, cx, cy - 138, lab.upper())
        for k, (w, dx, dy) in enumerate(words):
            out += ('<g class="uf" style="--d:%.2fs"><circle class="dot" cx="%d" cy="%d" r="8"/><text class="wd" x="%d" y="%d">%s</text></g>'
                    % (d0 + .15 + k * .12, cx + dx, cy + dy, cx + dx + 16, cy + dy + 10, w))
        out += '</g>'
    return out

# ---------------- 9 · how it learned ----------------
AB_LOOP = [('Guess', 'the next word'), ('Check', 'the real word'), ('Adjust', 'turn the dials a little'), ('Repeat', 'with the next sentence')]
def AB_loop_svg():
    xs = [190, 610, 1030, 1450]
    out = ('<path class="dr" pathLength="1" style="--d:1.8s" d="M1450 70 C1450 -4, 190 -4, 190 70"/>'
           '<path class="dr" pathLength="1" style="--d:2.4s" d="M178 58 L190 72 L202 58"/>'
           '<g class="uf" style="--d:2.2s"><rect x="680" y="0" width="300" height="40" rx="20" class="pill"/>'
           '<text class="arc" x="830" y="28">trillions of times</text></g>')
    for k, (h, s) in enumerate(AB_LOOP):
        x, d = xs[k], .6 + k * .3
        out += ('<g class="uf" style="--d:%.2fs"><circle class="nd%s" cx="%d" cy="130" r="54"/><text class="num%s" x="%d" y="143">%d</text>'
                '<text class="lb" x="%d" y="240">%s</text><text class="sb" x="%d" y="280">%s</text></g>'
                % (d, ' last' if k == 3 else '', x, ' last' if k == 3 else '', x, k + 1, x, h, x, s))
        if k < 3:
            out += ('<path class="dr" pathLength="1" style="--d:%.2fs" d="M%d 130 H%d M%d 120 L%d 130 L%d 140"/>'
                    % (d + .2, x + 72, x + 348, x + 338, x + 348, x + 338))
    return out

# ---------------- 10 · next word ----------------
AB_PROBS = [('breakfast', 82), ('lunch', 9), ('dinner', 6), ('supper', 3)]

# ---------------- 11 · compare LLMs ----------------
AB_SPECS = [('How smart', 'Test it on your own real work.'),
            ('How much it reads at once', '1 million tokens is about 7 books.'),
            ('Cost', 'You pay per token, in and out.'),
            ('Speed', 'How fast the words come out.'),
            ('Thinks step by step', 'Slower, but better on hard jobs.'),
            ('Size', 'How many dials inside: billions to trillions.'),
            ('How it is built', 'Everyone works, or only experts: next slide.')]

# ---------------- 12 · dense vs mixture of experts ----------------
AB_PERSON = '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="7.5" r="4.2"/><path d="M3.5 22c0-4.8 3.8-8.4 8.5-8.4s8.5 3.6 8.5 8.4z"/></svg>'
AB_MAIL = ic('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>', 64, 1.8)
AB_ARROW = ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 40, 2.2)
def AB_staff(lit, d0, step):
    out = ''
    for k in range(16):
        on = (k in lit) if lit is not None else True
        d = (d0 + k * step) if lit is None else d0
        out += '<span class="p%s" style="--d:%.2fs">%s</span>' % (' on' if on else '', d, AB_PERSON)
    return '<div class="staff">%s</div>' % out

# ---------------- 13 · why it makes things up ----------------


# ---------------- slide: how it learned ----------------
# ---------------- slide: meaning map ----------------
MAP_GROUPS = [  # label, colour, centre, words (dx, dy)
    ('Onions', '#00F5A9', (230, 170), [('bawang', -60, -30), ('onion', 40, -50), ('&#27915;&#33905;', 70, 20), ('bwg', -20, 40)]),
    ('Drinks', '#FFB547', (690, 150), [('Milo', -50, -20), ('Horlicks', 40, -50), ('teh tarik', 60, 30), ('Nescafe', -70, 45)]),
    ('Money', '#9B85FF', (250, 450), [('invoice', -60, -30), ('bil', 50, -40), ('bayar', -40, 45), ('payment', 70, 25)]),
    ('When', '#4DA3FF', (700, 440), [('esok', -60, -25), ('tomorrow', 50, -45), ('be4 12pm', 55, 40), ('pagi', -55, 45)]),
]
def _map_svg():
    out, k = '', 0
    for g, (lab, col, (cx, cy), words) in enumerate(MAP_GROUPS):
        out += '<g class="grp" style="--d:%.2fs"><circle cx="%d" cy="%d" r="125" fill="%s" fill-opacity=".07" stroke="%s" stroke-opacity=".35" stroke-dasharray="4 8"/>' % (.6 + g * .5, cx, cy, col, col)
        out += '<text class="gl" x="%d" y="%d" fill="%s">%s</text></g>' % (cx, cy - 140, col, lab.upper())
        for w, dx, dy in words:
            out += ('<g class="wd" style="--d:%.2fs"><circle cx="%d" cy="%d" r="8" fill="%s"/><text x="%d" y="%d">%s</text></g>'
                    % (.8 + g * .5 + k % 4 * .1, cx + dx, cy + dy, col, cx + dx + 14, cy + dy + 8, w))
            k += 1
    return out
MAP_PTS = [('Same meaning, any language', '<b>bawang</b>, <b>onion</b> and <b>&#27915;&#33905;</b> land in the same spot. So it reads BM, English and Chinese alike.'),
           ('Typos still land nearby', '<b>bwg</b> is used like <b>bawang</b>, so it lands next to it. That is how rojak and short forms work.'),
           ('The real map is huge', 'Not 2 directions but thousands. Close on the map = similar in meaning.')]

# ---------------- slide: how it learned ----------------
TRAIN = [('Read and guess', 'Pre-training',
          ['Take a sentence, hide the next word', 'Guess it, then check the real word', 'Turn the dials a tiny bit toward the right answer', 'Repeat, trillions of times'],
          [('Months', 'of training'), ('10,000s', 'of computer chips'), ('USD 100m+', 'for the biggest')]),
         ('Coached by people', 'Fine-tuning',
          ['People wrote thousands of example answers', 'Then rated its answers: better or worse', 'It learned to follow instructions', 'And to be helpful, polite and safe'],
          [('Like', 'a graduate on probation')]),
         ('Locked, then released', 'Ready to use',
          ['The dials are locked', 'Its knowledge stops at a cut-off date', 'It does not learn from your chat as you talk', 'Ask it anything: it predicts the answer'],
          [('Cut-off', 'it knows nothing after it')])]

PROBS = [('breakfast', 82), ('lunch', 9), ('dinner', 6), ('supper', 3)]

# ---------------- slide: 7 things to compare between LLMs ----------------
SPECS = [('Capability', 'How good it is at your kind of work: writing, maths, reading documents, coding.', 'Test it on 10 of your own real orders, not only on rankings.'),
         ('Context window', 'How much it can read at once, in tokens.', 'DeepSeek V4: 1 million tokens, about 7 books of 400 pages.'),
         ('Cost', 'Price per 1 million tokens. Reading in and writing out are priced separately.', 'Long PDFs and long chats cost more.'),
         ('Output speed', 'How many tokens a second it writes.', 'Fast for chat; slower is fine for a report overnight.'),
         ('Reasoning', 'Whether it can think step by step before it answers.', 'Slower and costs more, but better on hard, many-step jobs.'),
         ('Parameters', 'The number of dials inside the brain.', 'Llama 3: 8B or 70B. DeepSeek V4 Pro: 1.6T (1,600B).'),
         ('Architecture', 'Dense, or Mixture of Experts (MoE).', 'Next slide.')]

# ---------------- slide: dense vs MoE ----------------
def _experts():
    lit = {2, 9}
    return ''.join('<i class="%s"></i>' % ('on' if k in lit else '') for k in range(16))

# ---------------- slide: why it makes things up ----------------
TIPS = [('Give it facts', 'Let it look up your records. Don&rsquo;t trust what it &ldquo;remembers&rdquo;.'),
        ('Ask for the source', '&ldquo;Where did this number come from?&rdquo; A good answer can show you.'),
        ('A person checks', 'Anything that moves money or stock waits for a human yes.')]

# ---------------- slide: why the AI agent was invented ----------------
GAPS = [('It can only talk. It cannot click, send or save.', 'Tools', 'Hands to act in real systems'),
        ('Its knowledge stops at a cut-off date.', 'Look-up', 'Fetch fresh facts every time'),
        ('It forgets after every chat. Its desk has a size.', 'Memory', 'Notes kept outside the brain'),
        ('It answers in 1 shot and never checks itself.', 'The loop', 'Act, check, try again until done'),
        ('It doesn&rsquo;t know how your company works.', 'Rules &amp; skills', 'Your SOP, written down'),
        ('Nothing stops it doing the wrong thing.', 'Permission', 'Limits, plus a person who approves')]
ERAS = [('2022', 'Chat', 'It talks'), ('2023', 'Tools', 'It can call a system'), ('2025', 'Agents', 'It works in a loop until done')]
# ==================== batch C · slides 14-19 of "What is an AI Agent?" (minimal redesign) ====================
AC_WRENCH = '<path d="M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>'
AC_LOOK = '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>'
AC_CAB = '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 6h4M10 12h4M10 18h4"/>'
AC_LOOPI = '<path d="M20 12a8 8 0 11-2.3-5.7"/><path d="M20 4v4h-4"/>'
AC_BOOK = '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>'
AC_SHIELD = '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>'
AC_ARROW = '<path d="M4 12h16M14 6l6 6-6 6"/>'
AC_X = '<path d="M6 6l12 12M18 6L6 18"/>'
AC_CHAT = '<path d="M4 5h16v11H9l-5 4z"/>'

# ---------------- 14 · why agents ----------------
AC_SIX = [(AC_WRENCH, 'Tools', 'to click, send and save'),
          (AC_LOOK, 'Look-up', 'fresh facts, every time'),
          (AC_CAB, 'Memory', 'notes kept outside the brain'),
          (AC_LOOPI, 'A loop', 'try, check, try again'),
          (AC_BOOK, 'Rules', 'your SOP, written down'),
          (AC_SHIELD, 'Permission', 'a person approves')]


# ---------------- 15 · what is an AI agent (robot + 6 in-slide steps) ----------------
AC_PARTS = [  # (name, short label on robot, tag, 1 plain sentence, 1 example)
    ('Brain', 'thinks', '', 'It understands the message and plans the next step.',
     '&ldquo;bwg besar 10kg x ---&rdquo; &rarr; big onions, 10 kg bags. Quantity missing, so it asks.'),
    ('Tools', 'does the work', 'NO TOOLS, NO WORK', 'Each tool is 1 action in a real system. The brain cannot click; tools can.',
     'Check stock &rarr; 42 bags. Create order &rarr; draft ready.'),
    ('Memory', 'knows your data', '', 'The brain forgets after every chat, so it looks up your records.',
     'Jaya Grocer&rsquo;s last price for big onions: RM28 a bag.'),
    ('Rules &amp; skills', 'your SOP', '', 'Your way of working, written down: what never to do, and the steps.',
     'Over the credit limit? Stop and ask the boss.'),
    ('Permission', 'what it may touch', 'KEEPS IT SAFE', 'What it may see and do. Anything important waits for a person.',
     'It can draft an order. It cannot delete an invoice.'),
]
AC_ON1 = [('Brain', 'reads the WhatsApp order'), ('Memory', 'finds the customer and the stock'),
          ('Tools', 'drafts the order in your ERP'), ('Rules', 'asks when an item is unclear'),
          ('Permission', 'you approve before it saves')]

AC_S = 'rgba(0,245,169,.38)'
def AC_lbl(k, x, y, lx, ly, ex, ey, anchor='start'):
    name, short = AC_PARTS[k - 1][0], AC_PARTS[k - 1][1]
    return ('<g class="lb"><path class="ld" d="M%d %dL%d %d" pathLength="1"/><circle class="dot" cx="%d" cy="%d" r="6"/>'
            '<circle class="nb" cx="%d" cy="%d" r="17"/><text class="nn" x="%d" y="%d">%d</text>'
            '<text class="ln" x="%d" y="%d" text-anchor="%s">%s</text><text class="ls" x="%d" y="%d" text-anchor="%s">%s</text></g>'
            % (x, y, ex, ey, x, y, ex, ey, ex, ey + 6, k, lx, ly, anchor, name, lx, ly + 30, anchor, short))

AC_ROBOT = '''<svg class="rbt" viewBox="0 0 820 780" aria-label="An AI agent drawn as a robot, with its 5 parts labelled">
<defs>
 <linearGradient id="rb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22483F"/><stop offset="1" stop-color="#0B2420"/></linearGradient>
 <linearGradient id="rh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2B5A50"/><stop offset="1" stop-color="#0D2A25"/></linearGradient>
 <radialGradient id="rg"><stop offset="0" stop-color="#00F5A9" stop-opacity=".55"/><stop offset="1" stop-color="#00F5A9" stop-opacity="0"/></radialGradient>
</defs>
<ellipse cx="380" cy="706" rx="200" ry="28" fill="url(#rg)" opacity=".7"/>
<g class="bob">
 <ellipse class="flame" cx="380" cy="596" rx="30" ry="40" fill="url(#rg)"/>
 <path d="M334 540h92l-14 34h-64z" fill="#0B2420" stroke="''' + AC_S + '''" stroke-width="2"/>
 <ellipse cx="380" cy="576" rx="22" ry="5" fill="#00F5A9" opacity=".85"/>
 <path d="M268 340C212 360 192 408 212 466" fill="none" stroke="''' + AC_S + '''" stroke-width="36" stroke-linecap="round"/>
 <path d="M268 340C212 360 192 408 212 466" fill="none" stroke="#1A3E37" stroke-width="31" stroke-linecap="round"/>
 <path d="M492 340C556 324 590 286 598 232" fill="none" stroke="''' + AC_S + '''" stroke-width="36" stroke-linecap="round"/>
 <path d="M492 340C556 324 590 286 598 232" fill="none" stroke="#1A3E37" stroke-width="31" stroke-linecap="round"/>
 <rect x="262" y="300" width="236" height="246" rx="58" fill="url(#rb)" stroke="''' + AC_S + '''" stroke-width="2"/>
 <path d="M290 320h180" stroke="rgba(242,251,247,.12)" stroke-width="2" stroke-linecap="round"/>
 <rect x="352" y="280" width="56" height="26" rx="8" fill="#0B2420" stroke="''' + AC_S + '''" stroke-width="2"/>
 <line x1="380" y1="86" x2="380" y2="50" stroke="''' + AC_S + '''" stroke-width="5" stroke-linecap="round"/>
 <circle class="ant" cx="380" cy="42" r="11" fill="#00F5A9"/>
 <rect x="248" y="84" width="264" height="204" rx="76" fill="url(#rh)" stroke="''' + AC_S + '''" stroke-width="2"/>
 <circle cx="246" cy="208" r="19" fill="#0B2420" stroke="''' + AC_S + '''" stroke-width="2"/><circle cx="246" cy="208" r="7" fill="#00F5A9" opacity=".6"/>
 <circle cx="514" cy="208" r="19" fill="#0B2420" stroke="''' + AC_S + '''" stroke-width="2"/><circle cx="514" cy="208" r="7" fill="#00F5A9" opacity=".6"/>
 <rect x="284" y="202" width="192" height="60" rx="30" fill="#021A17" stroke="rgba(0,245,169,.5)" stroke-width="2"/>
 <g class="eyes"><rect x="318" y="222" width="34" height="18" rx="9" fill="#00F5A9"/><rect x="408" y="222" width="34" height="18" rx="9" fill="#00F5A9"/></g>

 <g class="pt p1">
  <circle class="ring" cx="380" cy="142" r="84"/>
  <ellipse cx="380" cy="142" rx="76" ry="48" fill="rgba(0,245,169,.07)" stroke="rgba(0,245,169,.45)" stroke-width="2"/>
  <g class="brain" fill="rgba(0,245,169,.16)" stroke="#00F5A9" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">
   <path d="M377 106C351 98 327 110 327 131C313 141 317 165 335 169C343 179 364 179 377 172Z"/>
   <path d="M383 106C409 98 433 110 433 131C447 141 443 165 425 169C417 179 396 179 383 172Z"/>
   <path d="M347 125c10 0 16 6 16 14M341 151c10-4 20 0 24 8M413 125c-10 0-16 6-16 14M419 151c-10-4-20 0-24 8" fill="none"/>
  </g>
 </g>
 <g class="pt p2">
  <circle class="ring" cx="606" cy="190" r="70"/>
  <circle cx="598" cy="232" r="22" fill="#0B2420" stroke="#00F5A9" stroke-width="3"/>
  <path transform="translate(588 148) scale(3)" d="M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z" fill="#0B2420" stroke="#00F5A9" stroke-width="1.1" stroke-linejoin="round"/>
  <g class="spk" stroke="#00F5A9" stroke-width="3" stroke-linecap="round"><path d="M664 186l16 4M662 206h16M654 224l10 10"/></g>
 </g>
 <g class="pt p3">
  <circle class="ring" cx="380" cy="458" r="80"/>
  <rect x="316" y="404" width="128" height="110" rx="14" fill="#06201C" stroke="#00F5A9" stroke-width="2.5"/>
  <path d="M316 441h128M316 478h128" stroke="#00F5A9" stroke-width="2" opacity=".7"/>
  <g fill="#00F5A9"><rect x="366" y="419" width="28" height="7" rx="3.5"/><rect x="366" y="456" width="28" height="7" rx="3.5"/><rect x="366" y="493" width="28" height="7" rx="3.5"/></g>
 </g>
 <g class="pt p4">
  <circle class="ring" cx="184" cy="478" r="70"/>
  <g transform="rotate(-10 182 478)">
   <rect x="148" y="434" width="70" height="90" rx="8" fill="#0B2420" stroke="#00F5A9" stroke-width="3"/>
   <path d="M160 434v90" stroke="#00F5A9" stroke-width="3"/>
   <path d="M172 462l7 7 14-14M172 492h32M172 506h22" fill="none" stroke="#00F5A9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <circle cx="214" cy="468" r="20" fill="#1A3E37" stroke="''' + AC_S + '''" stroke-width="2"/>
 </g>
 <g class="pt p5">
  <circle class="ring" cx="380" cy="356" r="56"/>
  <path d="M380 324l32 12v20c0 20-14 32-32 40c-18-8-32-20-32-40v-20z" fill="rgba(255,181,71,.16)" stroke="#FFB547" stroke-width="3" stroke-linejoin="round"/>
  <rect x="369" y="352" width="22" height="17" rx="3" fill="#FFB547"/>
  <path d="M373 352v-5a7 7 0 0114 0v5" fill="none" stroke="#FFB547" stroke-width="3"/>
 </g>
</g>
<g class="lbs">
 <g class="pt p1">''' + AC_lbl(1, 304, 128, 176, 120, 200, 128, 'end') + '''</g>
 <g class="pt p2">''' + AC_lbl(2, 628, 162, 656, 100, 628, 106) + '''</g>
 <g class="pt p5">''' + AC_lbl(5, 414, 356, 626, 350, 604, 364) + '''</g>
 <g class="pt p3">''' + AC_lbl(3, 446, 470, 626, 490, 604, 504) + '''</g>
 <g class="pt p4">''' + AC_lbl(4, 160, 528, 30, 660, 112, 604) + '''</g>
</g>
</svg>'''

def AC_detail():
    out = ''
    for i, (name, _, tag, what, eg) in enumerate(AC_PARTS):
        out += ('<div class="dt" data-s="%d"><small class="pn">PART %d OF 5%s</small><h2>%s</h2><p class="what">%s</p>'
                '<div class="eg"><small>EXAMPLE</small><p>%s</p></div></div>'
                % (i + 1, i + 1, (' <span class="tg">' + tag + '</span>') if tag else '', name, what, eg))
    return out

slide('20-what-is-agent', 'What is an AI agent?', SEC[2], 'dark', 'data-sparks="none"', MIN_CSS + '''
.mt { font-size: 66px; }
.wrap { flex:1; display:grid; grid-template-columns: 700px 1fr; gap: 70px; margin-top: 10px; min-height: 0; }
.rbt { width: 700px; height: auto; display:block; overflow: visible; animation: lift .9s cubic-bezier(.2,.8,.2,1) .3s both; }
@keyframes lift { from { opacity: 0; transform: translateY(26px); } to { opacity: 1; transform: none; } }
.bob { animation: bob 4.6s ease-in-out 1.4s infinite; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
.flame { transform-box: fill-box; transform-origin: 50% 0; animation: flk 1.2s ease-in-out infinite alternate; }
@keyframes flk { from { transform: scaleY(.85); opacity: .75; } to { transform: scaleY(1.1); opacity: 1; } }
.eyes rect { transform-box: fill-box; transform-origin: center; animation: blink 6s 2s infinite; }
@keyframes blink { 0%,95%,100% { transform: scaleY(1); } 97.5% { transform: scaleY(.12); } }
.pt { transition: opacity .5s ease; }
.ring { fill: none; stroke: #00F5A9; stroke-width: 3; opacity: 0; transform-box: fill-box; transform-origin: center; }
.p5 .ring { stroke: #FFB547; }
.lb .ld { fill:none; stroke: rgba(242,251,247,.45); stroke-width: 2; stroke-dasharray: 1; stroke-dashoffset: 1; animation: ld .6s ease forwards; }
.lb .dot { fill: #00F5A9; } .p5 .lb .dot { fill: #FFB547; }
.lb .nb { fill: #021A17; stroke: #00F5A9; stroke-width: 2.5; } .p5 .lb .nb { stroke: #FFB547; }
.lb .nn { font: 700 19px var(--sans); fill: #00F5A9; text-anchor: middle; } .p5 .lb .nn { fill: #FFB547; }
.lb .ln { font: 750 34px var(--sans); fill: var(--on-dark); letter-spacing: -.01em; transition: fill .4s ease; }
.lb .ls { font: 500 23px var(--sans); fill: var(--on-dark-2); }
.lbs .pt { opacity: 0; animation: lin .5s ease forwards; }
''' + ''.join('.lbs .p%d, .lbs .p%d .ld { animation-delay: %.2fs; }\n' % (k, k, .9 + (k - 1) * .2) for k in range(1, 6)) + '''
@keyframes lin { to { opacity: 1; } }
@keyframes ld { to { stroke-dashoffset: 0; } }
''' + ''.join('body[data-s="%d"] .bob .pt:not(.p%d), body[data-s="%d"] .lbs .pt:not(.p%d) > * { opacity: .18; }\n'
              'body[data-s="%d"] .p%d .ring { animation: rng 2.4s ease-out infinite; }\n'
              'body[data-s="%d"] .lbs .p%d .ln { fill: %s; }\n' % (k, k, k, k, k, k, k, k, '#FFB547' if k == 5 else '#00F5A9') for k in range(1, 6)) + '''
@keyframes rng { 0% { opacity: .9; transform: scale(.7); } 100% { opacity: 0; transform: scale(1.25); } }
.stage { position:relative; }
.intro, .dt, .lp { position:absolute; inset: 0; display:flex; flex-direction:column; justify-content:center; transition: opacity .5s ease, transform .6s cubic-bezier(.2,.8,.2,1); }
.dt, .lp { opacity: 0; transform: translateX(24px); pointer-events: none; }
body:not([data-s="0"]) .intro { opacity: 0; transform: translateX(-24px); }
''' + ''.join('body[data-s="%d"] .dt[data-s="%d"] { opacity: 1; transform: none; }\n' % (k, k) for k in range(1, 6)) + '''
body[data-s="6"] .lp { opacity: 1; transform: none; }
.ag2 { flex:1; display:flex; flex-direction:column; min-height: 0; transition: opacity .7s ease, transform .9s cubic-bezier(.2,.75,.15,1); }
body[data-w="1"] .ag2 { opacity: 0; transform: translateY(40px); }
body[data-w="1"] .ag2 * { animation-play-state: paused; }
.why { position:absolute; left: 128px; right: 128px; top: 92px; bottom: 120px; display:flex; flex-direction:column; transition: opacity .6s ease, transform .8s cubic-bezier(.2,.75,.15,1); }
body:not([data-w="1"]) .why { opacity: 0; transform: translateY(-30px); pointer-events: none; }
.why .mt { font-size: 64px; white-space: nowrap; }
.why .q { margin-top: 30px; display:inline-flex; align-self:flex-start; align-items:center; gap: 14px; font-size: 36px; padding: 16px 26px; border-radius: 6px 26px 26px 26px; background: #fff; color: var(--ink); font-weight: 600; }
.why .q i { font-style: normal; display:grid; place-items:center; width: 40px; height: 40px; border-radius: 50%; background: #25D366; color: #fff; }
.why .cmp { flex:1; min-height: 0; display:grid; grid-template-columns: 1fr 1fr; gap: 44px; margin-top: 34px; margin-bottom: 30px; }
.why .cmp > div { display:flex; flex-direction:column; overflow:hidden; padding: 0 !important; }
.why .pic { position:relative; flex:1; min-height: 0; overflow:hidden; background: rgba(242,251,247,.05); }
.why .ag .pic { background: radial-gradient(120% 100% at 30% 0%, rgba(0,245,169,.22), rgba(0,245,169,.04) 70%); }
.why .pic .av { position:absolute; left: 26px; bottom: -14px; height: 92%; }
.why .pic .cb { position:absolute; left: 47%; right: 30px; top: 30px; padding: 20px 24px; border-radius: 6px 24px 24px 24px; background: #fff; color: var(--ink); font-size: 26px; line-height: 1.35; font-style: italic; box-shadow: 0 24px 40px -24px rgba(0,0,0,.6); }
.why .pic .cb span { display:block; font-style: normal; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .14em; color: var(--ink-3); margin-bottom: 6px; }
.why .pic .shot { position:absolute; left: 30px; right: 150px; top: 24px; transform: rotate(-2deg); border-radius: 18px; overflow:hidden; box-shadow: 0 30px 60px -20px rgba(0,0,0,.65); }
.why .pic .shot img { display:block; width: 100%; }
.why .pic .av2 { position:absolute; right: 6px; bottom: -10px; height: 74%; }
.why .pic .tg { position:absolute; right: 22px; top: 26px; display:flex; align-items:center; gap: 8px; font-size: 21px; font-weight: 700; color: #02221F; background: var(--neon); padding: 8px 14px; border-radius: 999px; box-shadow: 0 10px 24px -8px rgba(0,245,169,.6); }
.why .cap { display:grid; grid-template-columns: auto 1fr; align-items:baseline; column-gap: 22px; padding: 18px 30px 22px; }
.why .cap small { grid-column: 1 / -1; }
.why .cap .res { justify-self: end; }
.why .cmp > div { padding: 34px 38px; border-radius: 26px; border: 1px solid rgba(242,251,247,.16); background: rgba(242,251,247,.04); }
.why .cmp .ag { border-color: rgba(0,245,169,.55); background: rgba(0,245,169,.07); }
.why .cmp small { font-family: var(--mono); font-size: 21px; font-weight: 700; letter-spacing: .14em; color: var(--on-dark-3); }
.why .cmp .ag small { color: var(--neon); }
.why .cmp h3 { font-size: 40px; font-weight: 800; letter-spacing: -.02em; margin-top: 6px; }
.why .cmp .say { font-size: 32px; line-height: 1.38; color: var(--on-dark-2); margin-top: 14px; font-style: italic; }
.why .cmp ul { list-style:none; display:grid; gap: 14px; margin-top: 20px; }
.why .cmp li { display:flex; align-items:center; gap: 14px; font-size: 33px; color: var(--on-dark); }
.why .cmp li svg { color: var(--neon); flex:none; }
.why .cmp .res { margin-top: 0; font-size: 28px; font-weight: 750; }
.why .cmp .bad .res { color: #FFB547; } .why .cmp .ag .res { color: var(--neon); }
.why .bt { margin-top: auto; font-size: 36px; color: var(--on-dark-2); }
.why .bt b { color: var(--on-dark); }
.why [style*="--d"] { opacity: 0; transform: translateY(16px); transition: opacity .5s ease, transform .6s cubic-bezier(.2,.7,.2,1); }
body[data-w="1"] .why [style*="--d"] { opacity: 1; transform: none; transition-delay: var(--d); }
.intro > p { font-size: 40px; line-height: 1.35; color: var(--on-dark); max-width: 820px; }
.intro > p b { color: var(--neon); font-weight: 700; }
.vs { margin-top: 44px; display:grid; gap: 0; max-width: 820px; }
.vs div { display:grid; grid-template-columns: 300px 1fr; align-items:baseline; padding: 20px 0; border-top: 1px solid rgba(242,251,247,.18); }
.vs b { font-size: 32px; font-weight: 750; }
.vs span { font-size: 30px; color: var(--on-dark-2); }
.vs .yes b { color: var(--neon); } .vs .yes span { color: var(--on-dark); }
.pn { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .14em; color: var(--neon); display:flex; align-items:center; gap: 16px; }
.dt[data-s="5"] .pn { color: #FFB547; }
.tg { padding: 6px 12px; border-radius: 8px; border: 1.5px solid currentColor; letter-spacing: .1em; font-size: 18px; }
.dt h2 { font-size: 76px; font-weight: 750; letter-spacing: -.035em; line-height: 1; margin-top: 18px; }
.dt .what { font-size: 38px; line-height: 1.34; color: var(--on-dark); margin-top: 24px; max-width: 820px; text-wrap: balance; }
.dt .eg { margin-top: 40px; padding-left: 26px; border-left: 3px solid var(--neon); max-width: 820px; }
.dt[data-s="5"] .eg { border-color: #FFB547; }
.dt .eg small { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; color: var(--on-dark-3); }
.dt .eg p { font-size: 31px; line-height: 1.38; color: var(--on-dark-2); margin-top: 8px; }
.lp h4 { font-family: var(--mono); font-size: 20px; letter-spacing: .14em; color: var(--neon); font-weight: 700; }
.lp ol { list-style:none; margin-top: 18px; max-width: 840px; }
.lp li { display:grid; grid-template-columns: 56px 220px 1fr; align-items:baseline; padding: 18px 0; border-top: 1px solid rgba(242,251,247,.16); }
.lp li i { font-style: normal; font-family: var(--mono); font-size: 22px; font-weight: 700; color: var(--on-dark-3); }
.lp li b { font-size: 32px; font-weight: 750; color: var(--neon); }
.lp li:last-child b { color: #FFB547; }
.lp li span { font-size: 30px; color: var(--on-dark); }
''', '''
<div class="why">
  <div class="mk" style="--d:.05s;opacity:1;transform:none">Why we need an AI Agent</div>
  <h1 class="mt" style="--d:.15s">A chatbot <em>talks</em>. Your business needs work <em>done</em>.</h1>
  <div class="q" style="--d:.35s"><i>''' + ic('<path d="M4 5h16v11H9l-5 4z"/>', 22, 2.2) + '''</i>Ali bin Osman: 2 grade C egg, 2 grade B egg</div>
  <div class="cmp">
    <div class="bad" style="--d:.6s">
      <div class="pic"><img class="av" src="../assets/av/meiling-typing.svg" alt="Mei Ling typing">
        <div class="cb"><span>CHATBOT REPLIES</span>Open SQL Account, create a Sales Order, check the stock, then reply&hellip;</div></div>
      <div class="cap"><small>CHATBOT</small><h3>Tells you what to do</h3><p class="res">You still do all the typing.</p></div>
    </div>
    <div class="ag" style="--d:.85s">
      <div class="pic"><div class="shot"><img src="../assets/shot-approve.png" alt="SuDu approval card: Sales Order for Ali, waiting for you"></div>
        <img class="av2" src="../assets/av/agent-thumbs.svg" alt="The SuDu agent"><span class="tg">''' + ic(CHECK, 22, 3) + '''Sales Order drafted</span></div>
      <div class="cap"><small>AI AGENT</small><h3>Does it for you</h3><p class="res">You just approve.</p></div>
    </div>
  </div>
  <p class="bt" style="--d:1.2s">It can&rsquo;t click, it forgets, it doesn&rsquo;t know your rules, nothing stops it. <b>So we give the brain 4 things.</b></p>
</div>
<div class="ag2">
<div class="mk u" style="--d:.05s">The agent</div>
<h1 class="mt u" style="--d:.2s">An AI agent is a brain with hands, and <em>limits</em></h1>
<div class="wrap">
  ''' + AC_ROBOT + '''
  <div class="stage">
    <div class="intro">
      <p class="u" style="--d:1.7s">A brain alone only talks. Give it <b>tools</b>, <b>memory</b>, <b>rules</b> and <b>permission</b>, and it does a real job.</p>
      <div class="vs"><div class="u" style="--d:1.95s"><b>Brain only</b><span>tells you what to do</span></div>
        <div class="yes u" style="--d:2.15s"><b>Brain + 4 parts</b><span>does the work for you</span></div></div>
    </div>
    ''' + AC_detail() + '''
    <div class="lp"><h4>THE 5 PARTS ON 1 WHATSAPP ORDER</h4><ol>''' + ''.join('<li><i>%d</i><b>%s</b><span>%s</span></li>' % (k + 1, p, t) for k, (p, t) in enumerate(AC_ON1)) + '''</ol></div>
  </div>
</div>
</div>
<script>
(function () {
  var B = document.body;
  function set(n) { B.dataset.w = n === 0 ? '1' : '0'; B.dataset.s = String(Math.max(0, n - 1)); }
  set(0);
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
''',
"\"Why do we need an AI Agent at all? Look at a normal WhatsApp order: Ali wants 2 grade C eggs and 2 grade B eggs. On the left is Mei Ling with a chatbot. It tells her what to do: open SQL Account, create a Sales Order, check the stock, reply to the customer. Helpful, but she still does all the typing. On the right is an AI Agent. It does the job: this is the real Sales Order it drafted in SuDu, customer, items and prices filled in, waiting for 1 click. You just approve. Why can't the chatbot do that? It cannot click, it forgets, it does not know your rules, and nothing stops it. So we give the brain 4 things.\"\n\n(Next: the robot appears) \"A brain alone only talks. So, step by step, people gave it more: tools in 2023, and from 2025 agents that work on their own. If the LLM is the brain, an AI agent is the brain with hands, and with limits. Here it is as a robot with 5 parts. A brain alone only talks; it tells you what to do. Give it the other 4 parts and it does the work for you. Let me take them 1 at a time.\"\n\n(Next) Brain: \"The head is the language model. It understands the message and plans the next step. It understands meaning, not keywords: bwg, bawang and onion are the same thing. Here it reads big onions, 10 kg bags, and sees the quantity is missing, so it asks. But on its own it has never seen your company. Like a smart graduate on day 1.\"\n\n(Next) Tools: \"The hands, and the part people forget. Each tool is 1 action in a real system. Some tools only look: check stock, read an invoice. Some tools act: create an order, send a message. The brain cannot click a button. Without tools, it can only tell you what to do. No tools, no work.\"\n\n(Next) Memory: \"The filing cabinet in its chest. Most people do not know this: the brain forgets everything after each chat. So it looks things up in your records: customers, prices, stock, fresh every time. Jaya Grocer's last price for big onions: RM28 a bag. Which also means: messy records in, wrong answers out.\"\n\n(Next) Rules and skills: \"The rulebook in its hand. Your way of working, written down. Rules say what must never happen: over the credit limit, stop and ask the boss. Skills are the steps for 1 job: read the order, match the items, check stock, draft, send for approval. Plain words, so your manager can read and change them.\"\n\n(Next) Permission: \"The badge on its chest, and what makes it safe. What can it see? Only the data its job needs. What can it do? Only what you allow: draft yes, delete no, move money never. And anything important waits for a person, and every action is logged. This is the difference between a helper and a risk.\"\n\n(Next) \"Put the 5 together on 1 WhatsApp order: the brain reads it, memory finds the customer and the stock, the tools draft the order in your ERP, the rules make it ask when an item is unclear, and permission means you approve before anything is saved.\"\n\nThis slide has 7 extra Next presses: the robot, then the 5 parts, then 1 order.\nNext: \"So how does it actually work? It goes round a loop.\"")

# ---------------- 16 · the agent loop ----------------
AC_NODES = [('Think', -90), ('Act', 30), ('Check', 150)]
AC_ROUNDS = [('1', 'Find the item', 'Big onions, 10 kg. 42 bags in stock.', ''),
             ('2', 'Check credit limit &amp; term', 'Order is RM560. Only RM180 left.', ''),
             ('3', 'Over credit limit &amp; term', 'Rule: the boss decides. It asks, then waits.', 'warn')]
def AC_loop_svg():
    import math
    cx, cy, r = 280, 270, 200
    o = ('<svg class="lps" viewBox="0 0 560 540"><defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
         '<path d="M0 0L10 5L0 10z" fill="#00A57A"/></marker></defs>'
         '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="rgba(2,34,31,.08)" stroke-width="2"/>' % (cx, cy, r))
    for k, (_, a) in enumerate(AC_NODES):
        a0, a1 = math.radians(a + 26), math.radians(a + 120 - 26)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        o += ('<path class="arc" style="--d:%.2fs" d="M%.1f %.1fA%d %d 0 0 1 %.1f %.1f" pathLength="1" fill="none" stroke="#00A57A" stroke-width="4" stroke-linecap="round" marker-end="url(#ah)"/>'
              % (1.0 + k * .35, x0, y0, r, r, x1, y1))
    o += ('<circle class="run" r="9" fill="#00A57A"><animateMotion dur="7s" begin="2.4s" repeatCount="indefinite" path="M%d %d A%d %d 0 1 1 %.1f %d A%d %d 0 1 1 %d %d"/></circle>'
          % (cx, cy - r, r, r, cx, cy + r, r, r, cx, cy - r))
    o += ('<text class="mid" x="%d" y="%d" text-anchor="middle">repeat</text><text class="mid2" x="%d" y="%d" text-anchor="middle">until done</text>'
          % (cx, cy - 4, cx, cy + 34))
    for k, (n, a) in enumerate(AC_NODES):
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        o += ('<g class="nd" style="--d:%.2fs"><circle cx="%.1f" cy="%.1f" r="66" fill="#fff" stroke="#02221F" stroke-width="3"/>'
              '<text class="nn" x="%.1f" y="%.1f" text-anchor="middle">%s</text></g>' % (.6 + k * .35, x, y, x, y + 11, n))
    return o + '</svg>'

# ---------------- why we need an AI agent (split out of "what is an AI agent": it was step 0) ----------------
_wa = S[-1]
assert _wa['file'] == '20-what-is-agent', _wa['file']
_wh = _wa['html']
_why_html = _wh[_wh.index('<div class="why">'):_wh.index('<div class="ag2">')]
_wn = _wa['notes']
_cut = _wn.index('\n\n(Next: the robot appears) ')
slide('20-why-agent', 'Why we need an AI agent', SEC[2], 'dark', 'data-sparks="none" data-w="1"', _wa['css'], _why_html, _wn[:_cut] + '\n\nNext: "So let\'s meet the AI Agent."')
_wa['notes'] = _wn[_cut + len('\n\n(Next: the robot appears) '):]
_wa['notes'] = _wa['notes'].replace('This slide has 7 extra Next presses: the robot, then the 5 parts, then 1 order.', 'This slide has 6 extra Next presses: the 5 parts, then 1 order.').replace('Next: "So how does it actually work? It goes round a loop."', 'Next: "But not every agent is a good agent. Meet 2 of them."')
assert 'Meet 2 of them' in _wa['notes']
_wa['html'] = _wh.replace("function set(n) { B.dataset.w = n === 0 ? '1' : '0'; B.dataset.s = String(Math.max(0, n - 1)); }",
                          "function set(n) { B.dataset.w = '0'; B.dataset.s = String(n); }")
assert _wa['html'] != _wh

# ---------------- quiz: chatbot or AI agent? (1 step: reveal) ----------------
QZ = [  # icon, job, answer is agent?, why
    ('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>', 'Write a polite reply to a customer who paid late', False, 'Just words. Any chatbot can write it.'),
    ('<path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/>', 'Check if we still have 20 bags of onions', True, 'It must open your stock in SQL Account.'),
    ('<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 015 .5c0 1.5-2.5 2-2.5 3.5M12 17h.01"/>', 'Explain what an e&#8209;Invoice is', False, 'General knowledge. No system needed.'),
    ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 13h6M9 17h4"/>', 'Create the Sales Order and send the DO', True, 'It must click inside your system.'),
]
slide('20-agent-quiz', 'Quiz: chatbot or AI agent?', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.qz { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 26px; margin-top: auto; margin-bottom: 50px; }
.qz > div { position:relative; display:flex; flex-direction:column; min-height: 550px; padding: 30px 28px 28px; border-radius: 28px; background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); transition: box-shadow .5s ease, transform .6s cubic-bezier(.3,1.4,.5,1); }
.qz .n { font-family: var(--mono); font-size: 20px; font-weight: 700; color: var(--ink-3); }
.qz .ic { width: 96px; height: 96px; border-radius: 28px; display:grid; place-items:center; background: var(--mint); color: var(--green); margin-top: 16px; }
.qz h2 { font-size: 36px; font-weight: 750; letter-spacing: -.02em; line-height: 1.2; margin-top: 24px; }
.qz .ask { margin-top: auto; display:flex; gap: 10px; }
.qz .ask span { flex:1; text-align:center; font-size: 22px; font-weight: 700; padding: 12px 0; border-radius: 14px; border: 2px dashed var(--line); color: var(--ink-3); }
.qz .ans { position:absolute; left: 28px; right: 28px; bottom: 28px; padding: 18px 20px; border-radius: 18px; opacity: 0; transform: translateY(20px) scale(.96);
  transition: opacity .45s ease, transform .6s cubic-bezier(.3,1.5,.5,1); }
.qz .ans b { display:flex; align-items:center; gap: 10px; font-size: 28px; font-weight: 800; }
.qz .ans p { font-size: 22px; line-height: 1.35; margin-top: 6px; }
.qz .bot .ans { background: #EEF1EC; color: var(--ink); } .qz .bot .ans p { color: var(--ink-2); }
.qz .agt .ans { background: var(--ink); color: var(--on-dark); } .qz .agt .ans b { color: var(--neon); } .qz .agt .ans p { color: var(--on-dark-2); }
body[data-s="1"] .qz .ans { opacity: 1; transform: none; }
''' + ''.join('body[data-s="1"] .qz > div:nth-child(%d) .ans { transition-delay: %.2fs; }\n' % (k + 1, k * .25) for k in range(4)) + '''
body[data-s="1"] .qz .agt { box-shadow: 0 0 0 3px var(--green), 0 40px 70px -40px rgba(0,108,72,.55); transform: translateY(-10px); }
.shout { display:inline-flex; align-items:center; gap: 14px; margin-top: 26px; font-size: 30px; font-weight: 650; color: var(--green); }
''', '''
<div class="mk u" style="--d:.05s">Quick quiz</div>
<h1 class="mt u" style="--d:.15s">Chatbot or <em>AI Agent</em>?</h1>
<div class="shout u" style="--d:.3s">''' + ic(HAND, 40, 2) + '''Who can do this job? Shout it out.</div>
<div class="qz">''' + ''.join(
    '<div class="u %s" style="--d:%.2fs"><span class="n">JOB %d</span><span class="ic">%s</span><h2>%s</h2>'
    '<div class="ask"><span>Chatbot</span><span>AI Agent</span></div>'
    '<div class="ans"><b>%s%s</b><p>%s</p></div></div>'
    % ('agt' if ag else 'bot', .5 + k * .15, k + 1, ic(p, 48, 1.9), job, ic(CHECK, 28, 3), 'Needs an AI Agent' if ag else 'A chatbot can', why)
    for k, (p, job, ag, why) in enumerate(QZ)) + '''</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Quick quiz before we open it up. 4 jobs. For each one, shout: chatbot, or AI Agent?\n\nJob 1: write a polite reply to a customer who paid late.\" (let them shout) \"Job 2: check if we still have 20 bags of onions. Job 3: explain what an e-Invoice is. Job 4: create the Sales Order and send the DO.\"\n\n(Next) \"Job 1 and job 3: a chatbot can do them. They are just words. Job 2 and job 4 need an AI Agent, because it has to open your system and click. Here is the rule: if the job is only words, a chatbot can help. If the job touches your system, you need an agent.\"\n\nThis slide has 1 extra Next press: the answers.\nNext: \"So let's meet the AI Agent.\"")

# ---------------- meet your AI agent (intro before the robot) ----------------
MI_FACTS = [('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 'Works 24/7', 'No leave, no MC, no overtime'),
            ('<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 21h8M12 18v3"/>', 'Uses your systems', 'WhatsApp, SQL Account, Excel'),
            ('<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>', 'Asks before it acts', 'Nothing is posted without you')]
slide('20-agent-intro', 'Meet your AI agent', SEC[2], 'dark', 'data-sparks="none"', MIN_CSS + '''
.wrap { flex:1; display:grid; grid-template-columns: 720px 1fr; gap: 60px; align-items:center; }
.hero { position:relative; width: 720px; height: 720px; display:grid; place-items:center; }
.hero svg.orbit { position:absolute; inset: 0; }
.hero .rg { transform-origin: 360px 360px; animation: spin 50s linear infinite; } .hero .rg.b { animation-duration: 80s; animation-direction: reverse; }
@keyframes spin { to { transform: rotate(360deg); } }
.hero img { width: 470px; height: 470px; position:relative; }
.mi .mt { font-size: 84px; }
.fc { display:grid; gap: 22px; margin-top: 50px; }
.fc > div { display:grid; grid-template-columns: 84px 1fr; gap: 24px; align-items:center; }
.fc i { width: 84px; height: 84px; border-radius: 24px; display:grid; place-items:center; background: rgba(0,245,169,.12); color: var(--neon); }
.fc b { display:block; font-size: 38px; font-weight: 750; letter-spacing: -.02em; }
.fc span { display:block; font-size: 27px; color: var(--on-dark-2); margin-top: 2px; }
''', '''
<div class="wrap">
  <div class="hero">
    <svg class="orbit" viewBox="0 0 720 720" fill="none">
      <g class="rg"><circle cx="360" cy="360" r="330" stroke="rgba(242,251,247,.14)" stroke-dasharray="2 10"/><circle cx="360" cy="30" r="7" fill="#00F5A9"/></g>
      <g class="rg b"><circle cx="360" cy="360" r="280" stroke="rgba(0,245,169,.22)"/><circle cx="640" cy="360" r="5" fill="#00F5A9" opacity=".7"/></g>
    </svg>
    <img class="u" style="--d:.3s" src="../assets/av/agent-hi.svg" alt="The SuDu agent waving">
  </div>
  <div class="mi">
    <div class="mk u" style="--d:.1s">Meet your AI Agent</div>
    <h1 class="mt u" style="--d:.2s">Not a chatbot.<br><em>A new staff member.</em></h1>
    <p class="ml u" style="--d:.4s">It reads your messages, opens your systems, does the job, and <b>asks you</b> before anything is posted.</p>
    <div class="fc">''' + ''.join('<div class="u" style="--d:%.2fs"><i>%s</i><div><b>%s</b><span>%s</span></div></div>' % (.7 + k * .18, ic(p, 40, 1.9), b, s_) for k, (p, b, s_) in enumerate(MI_FACTS)) + '''</div>
  </div>
</div>
''',
"\"So, meet your AI Agent. It is not a chatbot that only talks. Think of it as a new staff member. It reads your WhatsApp messages, opens your systems like SQL Account and Excel, does the job, and asks you before anything is posted.\n\n3 things to remember. It works 24/7: no leave, no MC, no overtime. It uses the systems you already have. And it asks before it acts: nothing goes into your books without you.\"\n\nNext: \"So what is inside it? Let's open it up, as a robot with 5 parts.\"")

# ---------------- good agent vs bad agent (replaces the agent loop) ----------------
GB_ROWS = [  # time, what happens, bad agent, good agent
    ('9:00 am', '3 WhatsApp orders come in', 'Zzz&hellip; does nothing until you type &ldquo;create the orders&rdquo;.',
     'Drafts 3 Sales Orders. &ldquo;Boss, approve?&rdquo;'),
    ('11:30 am', 'Milo stock is down to 2 days', 'Says nothing. You find out when a customer shouts.',
     '&ldquo;Milo runs out Friday. PO to the supplier is drafted.&rdquo;'),
    ('4:00 pm', 'Kedai Ali is 45 days late', 'Nobody asked, so it never reminds.',
     'Sends a polite reminder. &ldquo;RM3,200 promised by Friday.&rdquo;'),
]
slide('21-good-vs-bad-agent', 'Good agent vs bad agent', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.mt { font-size: 70px; }
.gb { display:grid; grid-template-columns: 330px 1fr 1fr; column-gap: 26px; margin-top: 36px; flex:1; min-height: 0; grid-template-rows: auto repeat(3, 1fr) auto; row-gap: 14px; }
.gb .who { display:flex; align-items:center; gap: 20px; padding: 14px 24px; border-radius: 24px; }
.gb .who img { width: 104px; height: 104px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px var(--line); flex:none; }
.gb .who b { display:block; font-size: 38px; font-weight: 800; letter-spacing: -.02em; }
.gb .who span { display:block; font-size: 23px; font-weight: 600; margin-top: 2px; }
.gb .bad.who { background: #FFF1D6; } .gb .bad.who span { color: #8A3417; }
.gb .good.who { background: var(--ink); color: var(--on-dark); } .gb .good.who span { color: var(--neon); }
.gb .ev { display:flex; flex-direction:column; justify-content:center; padding-left: 6px; border-left: 4px solid var(--ink); padding: 0 0 0 20px; }
.gb .ev small { font-family: var(--mono); font-size: 20px; font-weight: 700; color: var(--green); }
.gb .ev b { font-size: 30px; font-weight: 750; letter-spacing: -.01em; line-height: 1.2; margin-top: 4px; }
.gb .c { display:flex; align-items:center; gap: 18px; padding: 18px 24px; border-radius: 22px; font-size: 27px; line-height: 1.32; }
.gb .c i { flex:none; width: 54px; height: 54px; border-radius: 50%; display:grid; place-items:center; font-style: normal; }
.gb .c.bad { background: #FBF7EF; color: #5B4A33; box-shadow: inset 0 0 0 2px #F1E2C2; } .gb .c.bad i { background: #FFE2A8; color: #8A3417; }
.gb .c.good { background: #EAF7F1; color: var(--ink); box-shadow: inset 0 0 0 2px rgba(0,108,72,.25); font-weight: 600; } .gb .c.good i { background: var(--green); color: #fff; }
.gb .zz { font-weight: 800; color: #C77800; }
.gb .sc { display:flex; align-items:center; justify-content:space-between; padding: 18px 26px; border-radius: 22px; }
.gb .sc b { font-size: 54px; font-weight: 800; letter-spacing: -.03em; } .gb .sc span { font-size: 25px; font-weight: 600; text-align:right; }
.gb .sc.bad { background: #FFF1D6; } .gb .sc.bad b { color: #C77800; } .gb .sc.bad span { color: #8A3417; }
.gb .sc.good { background: var(--green); color: #fff; } .gb .sc.good span { color: #E6F6EE; }
.gb .sl { display:flex; align-items:center; font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .14em; color: var(--ink-3); }
.st { opacity: 0; transform: translateY(18px); transition: opacity .5s ease, transform .6s cubic-bezier(.3,1.3,.5,1); }
.st.good { transition-delay: .35s; }
''' + ''.join('body[data-s="%d"] .s%d' % (n, k) + (', ' if False else '') + ' { opacity: 1; transform: none; }\n' for n in range(1, 5) for k in range(1, n + 1)) + '''
html.static .st { opacity: 1; transform: none; }
.zzz { display:inline-block; animation: zzz 1.6s ease-in-out infinite; } @keyframes zzz { 50% { transform: translateY(-5px) rotate(-6deg); } }
''', '''
<div class="mk u" style="--d:.05s">Good agent vs bad agent</div>
<h1 class="mt u" style="--d:.15s">Same AI. Very <em>different</em> staff.</h1>
<p class="ml u" style="--d:.3s">A bad agent waits for your prompt. A good agent <b>sees the work and starts it</b>.</p>
<div class="gb">
  <div></div>
  <div class="who bad u" style="--d:.5s"><img src="../assets/av/malas-tudung.svg" alt="Ah Malas with a coffee"><div><b>Ah Malas</b><span>Only does what you type</span></div></div>
  <div class="who good u" style="--d:.7s"><img src="../assets/av/agent-salute.svg" alt="Ah Rajin saluting"><div><b>Ah Rajin</b><span>Does the work before you ask</span></div></div>
''' + ''.join(
    '<div class="ev st s%d"><small>%s</small><b>%s</b></div>'
    '<div class="c bad st s%d"><i>%s</i><span>%s</span></div>'
    '<div class="c good st s%d"><i>%s</i><span>%s</span></div>'
    % (k + 1, tm, ev, k + 1, '<span class="zz zzz">z</span>' if k == 0 else ic('<path d="M12 8v5M12 16h.01"/><circle cx="12" cy="12" r="9"/>', 28, 2.4), bad,
       k + 1, ic(CHECK, 28, 3), good) for k, (tm, ev, bad, good) in enumerate(GB_ROWS)) + '''
  <div class="sl st s4">BY 5 PM</div>
  <div class="sc bad st s4"><b>1 job</b><span>the 1 you typed</span></div>
  <div class="sc good st s4"><b>5 jobs</b><span>done before you asked,<br>all waiting for your OK</span></div>
</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Now, not every agent is a good agent. Meet 2 of them. Ah Malas, with his coffee: he only does what you type. And Ah Rajin: he sees the work and starts it before you ask. Same AI inside. Very different staff. Let's follow them through 1 day.\"\n\n(Next) 9 am: \"3 WhatsApp orders come in. Ah Malas? Zzz. Nothing happens until you sit down and type: create the orders. Ah Rajin has already drafted 3 Sales Orders: Boss, approve?\"\n\n(Next) 11:30: \"Milo stock is down to 2 days. Ah Malas says nothing; you find out when a customer shouts at you. Ah Rajin: Milo runs out on Friday, and the PO to the supplier is already drafted.\"\n\n(Next) 4 pm: \"Kedai Ali is 45 days late. Nobody asked Ah Malas, so he never reminds. Ah Rajin sends a polite reminder and comes back with: RM3,200 promised by Friday.\"\n\n(Next) \"By 5 pm, Ah Malas did 1 job: the 1 you typed. Ah Rajin did 5, all waiting for your OK. And here is the important part: Ah Rajin is still not allowed to post anything on his own. Proactive does not mean out of control. It means he does the preparing, and you do the deciding.\n\nSo what makes a good agent? It knows the goal, it watches your data, it acts first, and it still asks you. That is how we set up every SuDu agent.\"\n\nThis slide has 4 extra Next presses: 3 moments of the day, then the score.\nNext: \"How do you turn the brain into a good staff member? The same way you set up a new hire.\"")


slide('21-agent-loop', 'The agent loop', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.wrap { flex:1; display:grid; grid-template-columns: 560px 1fr; gap: 110px; margin-top: 30px; min-height: 0; align-items:center; }
.lps { width: 560px; height: 540px; overflow: visible; display:block; }
.lps .nn { font: 750 32px var(--sans); fill: var(--ink); }
.lps .mid { font: 750 34px var(--sans); fill: var(--green); }
.lps .mid2 { font: 500 26px var(--sans); fill: var(--ink-2); }
.nd { opacity: 0; animation: mFade .7s ease forwards; animation-delay: var(--d); }
.arc { stroke-dasharray: 1; stroke-dashoffset: 1; animation: acd .7s ease forwards; animation-delay: var(--d); }
@keyframes acd { to { stroke-dashoffset: 0; } }
html.static .nd { opacity: 1; animation: none; } html.static .arc { stroke-dashoffset: 0; animation: none; }
html.static .run { display: none; }
.rt { align-self: center; }
.rd { display:grid; grid-template-columns: 80px 1fr; align-items:baseline; padding: 24px 0; border-top: 1px solid var(--line); }
.mk + .rd { border-top: 3px solid var(--ink); }
.rd i { font-style: normal; font-size: 46px; font-weight: 800; color: var(--green); letter-spacing: -.03em; }
.rd b { display:block; font-size: 36px; font-weight: 750; letter-spacing: -.02em; }
.rd p { font-size: 28px; line-height: 1.35; color: var(--ink-2); margin-top: 6px; }
.rd.warn i { color: #C77800; }
.rd.warn b::after { content:""; display:inline-block; width: 12px; height: 12px; border-radius: 50%; background: #FFB547; margin-left: 14px; vertical-align: middle; }
''', '''
<div class="mk u" style="--d:.05s">How an agent works</div>
<h1 class="mt u" style="--d:.2s">It works <em>on repeat</em>, until the job is done</h1>
<p class="ml u" style="--d:.4s">Think, act, check, repeat. It stops when the job is done, or when it needs you.</p>
<div class="wrap">
  ''' + AC_loop_svg() + '''
  <div class="rt"><div class="mk u" style="--d:1.6s;margin-bottom:18px">1 WhatsApp order, 3 rounds</div>''' + ''.join(
      '<div class="rd %s u" style="--d:%.2fs"><i>%s</i><div><b>%s</b><p>%s</p></div></div>' % (c, 1.8 + k * .3, n, t, p) for k, (n, t, p, c) in enumerate(AC_ROUNDS)) + '''</div>
</div>
''',
"\"So how does an agent actually work? It does not answer in 1 shot like a chatbot. It works on repeat until the job is done. [Point at the circle] Think: plan the next step. Act: use 1 tool. Check: did it work? Am I done? Is this safe? If not done, round again.\n\nWatch it on 1 WhatsApp order from Jaya Grocer. Round 1: find the item. It searches and finds big onions, 10 kg bags, 42 bags in stock. Round 2: check the credit limit and term. The order is RM560, and only RM180 is left on the credit limit. Round 3: over the credit limit and term. The rule says the boss decides. So it sends the request for approval and waits.\n\nThat is the whole idea. It loops until the job is done, then reports to you. Or, when it is unsure or the step is risky, it stops and asks a person.\"\n\nNext: \"Think of it like hiring a new graduate.\"")

# ---------------- 17 · brain to staff ----------------
AC_HIRE = [  # icon, clerk gets, agent gets, plain example
    ('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>', 'A job description', 'Instructions', 'Turn WhatsApp orders into Sales Orders'),
    ('<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3"/>', 'Logins and keys', 'Tools', 'Check stock, create order, send WhatsApp'),
    ('<path d="M3 7h18M5 7v13h14V7M9 3h6v4H9z"/>', 'The files', 'Memory', 'Customers, prices, past orders'),
    ('<path d="M4 4h16v16H4z"/><path d="M8 9l2 2 4-4M8 15h8"/>', 'Your SOP', 'Rules &amp; skills', 'Over the credit limit? Ask the boss'),
    ('<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>', 'A supervisor', 'Permission', 'Draft yes, delete no, you approve'),
    ('<path d="M9 3h6v3H9z"/><path d="M7 5H5v16h14V5h-2"/><path d="M9 13l2 2 4-4"/>', 'Probation', 'Testing', 'Try it on last month&rsquo;s orders first')]

slide('22-brain-to-staff', 'From brain to staff member', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.mt { font-size: 70px; }
.gd { display:grid; grid-template-columns: 1fr 96px 1.35fr; gap: 10px 0; margin-top: 22px; align-items:center; }
.gh { display:flex; align-items:center; gap: 16px; padding-bottom: 10px; }
.gh img { width: 84px; height: 84px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px var(--line); }
.gh b { font-size: 34px; font-weight: 800; letter-spacing: -.02em; }
.gh.ai b { color: var(--green); }
.cl { padding: 14px 24px; border-radius: 16px; background: #F0F2EF; font-size: 30px; font-weight: 600; color: var(--ink-2); }
.mid { display:flex; align-items:center; justify-content:center; position:relative; }
.mid::before { content:""; position:absolute; left: 0; right: 0; top: 50%; height: 2px; background: linear-gradient(90deg, #D5DBD7, var(--emerald)); }
.mid i { position:relative; display:grid; place-items:center; width: 60px; height: 60px; border-radius: 50%; background: var(--ink); color: var(--neon); }
.ag { display:flex; align-items:baseline; gap: 18px; padding: 14px 24px; border-radius: 16px; background: #fff; box-shadow: 0 0 0 1.5px rgba(0,165,122,.45), 0 16px 30px -26px rgba(2,34,31,.5); }
.ag b { font-size: 32px; font-weight: 800; color: var(--green); white-space: nowrap; letter-spacing: -.01em; }
.ag span { font-size: 25px; color: var(--ink-2); }
.end { margin-top: 30px; display:flex; align-items:center; gap: 20px; padding: 18px 28px; border-radius: 20px; background: var(--ink); color: var(--on-dark); font-size: 34px; }
.end em { font-style: normal; color: var(--neon); font-weight: 800; }
''', '''
<div class="mk u" style="--d:.05s">From brain to staff</div>
<h1 class="mt u" style="--d:.2s">Set up an AI Agent like a <em>new hire</em></h1>
<div class="gd">
  <div class="gh u" style="--d:.4s"><img src="../assets/av/meiling-typing.svg" alt=""><b>A new staff member gets</b></div><div></div>
  <div class="gh ai u" style="--d:.5s"><img src="../assets/av/agent-grad.svg" alt=""><b>Your AI Agent gets</b></div>
  ''' + ''.join('<div class="cl ux" style="--d:%.2fs">%s</div><div class="mid uf" style="--d:%.2fs"><i>%s</i></div><div class="ag u" style="--d:%.2fs"><b>%s</b><span>%s</span></div>'
                % (.7 + k * .2, a, .8 + k * .2, ic(p, 28, 2), .9 + k * .2, b, e) for k, (p, a, b, e) in enumerate(AC_HIRE)) + '''
</div>
<div class="end u" style="--d:2.2s">Brain + this setup = <em>the harness</em></div>
''',
"\"A brilliant brain alone only talks. Think about hiring a brilliant graduate: talent is not enough. You give them 6 things, and an AI Agent needs the same 6.\n\n[Go down the list] A job description: for the AI, its instructions: the goal, and when the job counts as done. Without it, it does too much, or the wrong job. Logins and keys: its tools, 1 for each action. Without them, it can only give advice. The files: its memory: your records, and what you taught it. Without it, it forgets the customer and guesses the price. Your SOP: its rules and skills. Without them, it does the job its own way. A supervisor: permission, who says yes. Without it, nobody checks before stock or money moves. And probation: testing. You try it on last month's orders first, then you watch it. Without that, the same mistake repeats quietly.\n\nThe brain plus this setup has a name: the harness. Every company can rent the same brain. The harness decides whether it helps or hurts.\"\n\nNext: \"Now, let me ask you to imagine something.\"")

# ---------------- 18 · harness ----------------
AC_RING = ['Tools', 'Memory', 'Rules', 'Permission', 'The loop', 'Tests']
AC_LE = [('The steps', 'what it does, in what order'),
         ('When to stop', 'what &ldquo;done&rdquo; means'),
         ('When to ask a person', 'money, doubt or risk')]
def AC_harness_svg():
    import math
    cx, cy = 350, 320
    o = ('<svg class="hn" viewBox="0 0 700 640"><circle class="hring" cx="%d" cy="%d" r="296" fill="rgba(0,165,122,.07)"/>'
         '<text class="ol" x="%d" y="16" text-anchor="middle">THE HARNESS</text>' % (cx, cy, cx))
    for k, t in enumerate(AC_RING):
        a = math.radians(-90 + k * 60)
        x0, y0 = cx + 108 * math.cos(a), cy + 108 * math.sin(a)
        x1, y1 = cx + 168 * math.cos(a), cy + 168 * math.sin(a)
        c, sn = math.cos(a), math.sin(a)
        if abs(c) < .1:
            x, y, anc = x1, y1 + (-24 if sn < 0 else 44), 'middle'
        else:
            x, y, anc = x1 + (20 if c > 0 else -20), y1 + 10, ('start' if c > 0 else 'end')
        o += ('<path class="sp" style="--d:%.2fs" d="M%.1f %.1fL%.1f %.1f" pathLength="1"/>'
              '<g class="rg" style="--d:%.2fs"><circle cx="%.1f" cy="%.1f" r="7" fill="#00A57A"/>'
              '<text class="rl" x="%.1f" y="%.1f" text-anchor="%s">%s</text></g>'
              % (1.0 + k * .18, x0, y0, x1, y1, 1.2 + k * .18, x1, y1, x, y, anc, t))
    o += ('<circle cx="%d" cy="%d" r="100" fill="#02221F"/><text class="ct" x="%d" y="%d" text-anchor="middle">LLM</text>'
          '<text class="cs" x="%d" y="%d" text-anchor="middle">the brain</text>' % (cx, cy, cx, cy + 6, cx, cy + 40))
    return o + '</svg>'


# ---------------- 19 · no tools, no work ----------------
AC_RUN = [('Check stock', '42 bags'), ('Check credit', 'Within limit'), ('Create sales order', 'SO-00451'), ('Send on WhatsApp', 'PDF sent')]

# ---------------- AI without tools is a guru (after the problems, before the tools) ----------------
GU_SAYS = ['You should check your stock first.', 'You should chase Kedai Ali.', 'You should key in orders faster.']
GU_TOOLS = [('<path d="M3 21V8l9-5 9 5v13"/><path d="M7 21v-8h10v8M7 17h10"/>', 'WMS', 'Scans, counts and picks your stock'),
            ('<path d="M3 21V11l6 4v-4l6 4V5h6v16z"/><path d="M7 18h2M12 18h2M17 18h2"/>', 'MES', 'Tracks every job and every batch'),
            ('<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>', 'SQL Account', 'Orders, invoices and payments')]
slide('25-ai-guru', 'AI without tools', SEC[1], 'light', 'data-sparks="none"', MIN_CSS + '''
.two { display:grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 36px; height: 560px; margin-bottom: 28px; }
.two > div { position:relative; display:flex; flex-direction:column; border-radius: 32px; padding: 30px 36px; overflow:hidden; }
.gu { background: #FBF7EF; box-shadow: inset 0 0 0 2px #F1E2C2; }
.ok { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--green), 0 50px 80px -40px rgba(0,108,72,.6); }
.two h3 { font-size: 40px; font-weight: 800; letter-spacing: -.02em; }
.gu h3 { color: #8A3417; } .ok h3 { color: var(--neon); }
.two h3 span { display:block; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .16em; color: var(--ink-3); margin-bottom: 6px; }
.ok h3 span { color: var(--on-dark-3); }
.gsc { position:relative; flex:1; display:flex; align-items:center; gap: 26px; margin-top: 16px; }
.gsc img { width: 220px; height: 220px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px #F1E2C2, 0 20px 40px -20px rgba(90,60,20,.45); flex:none; animation: bob 3.6s ease-in-out infinite; }
@keyframes bob { 50% { transform: translateY(-6px) rotate(-2deg); } }
.bub { display:grid; gap: 14px; align-self: center; }
.bub p { position:relative; font-size: 26px; font-weight: 600; line-height: 1.3; color: #5B4A33; background: #fff; padding: 14px 20px; border-radius: 6px 22px 22px 22px; box-shadow: 0 0 0 1px #F1E2C2, 0 14px 28px -18px rgba(90,60,20,.4);
  opacity: 0; transform: translateX(-14px) scale(.96); animation: pop .5s cubic-bezier(.3,1.5,.5,1) forwards; animation-delay: var(--d); }
@keyframes pop { to { opacity: 1; transform: none; } }
.stamp { position:absolute; right: 30px; top: 26px; padding: 14px 22px 12px; border: 5px solid #D2452B; border-radius: 16px; color: #D2452B; text-align:center; transform: rotate(-9deg) scale(2.2); opacity: 0;
  animation: stamp .45s cubic-bezier(.5,0,.6,1.6) 2.4s forwards; background: rgba(255,255,255,.6); }
.stamp b { display:block; font-size: 48px; font-weight: 900; letter-spacing: .06em; line-height: 1; }
.stamp small { display:block; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .16em; margin-top: 6px; }
@keyframes stamp { to { opacity: 1; transform: rotate(-9deg) scale(1); } }
.tls { display:grid; gap: 14px; margin-top: 20px; }
.tls > div { display:grid; grid-template-columns: 76px 1fr; gap: 20px; align-items:center; padding: 14px 20px; border-radius: 20px; background: rgba(242,251,247,.06); box-shadow: inset 0 0 0 1px rgba(242,251,247,.12);
  opacity: 0; transform: translateY(14px); animation: pop .55s cubic-bezier(.3,1.4,.5,1) forwards; animation-delay: var(--d); }
.tls i { width: 76px; height: 76px; border-radius: 22px; display:grid; place-items:center; color: var(--neon); background: rgba(0,245,169,.12); }
.tls b { display:block; font-size: 32px; font-weight: 800; letter-spacing: -.01em; }
.tls span { display:block; font-size: 24px; color: var(--on-dark-2); margin-top: 2px; }
.ok .vd { display:flex; align-items:center; gap: 12px; margin-top: auto; font-size: 28px; font-weight: 750; color: var(--neon); }
.bt { font-size: 32px; color: var(--ink-2); } .bt b { color: var(--ink); }
html.static .bub p, html.static .tls > div, html.static .stamp { opacity: 1; animation: none; transform: none; }
html.static .stamp { transform: rotate(-9deg); } html.static .gsc img { animation: none; }
/* ---- steps 0-1: the question, then the answer ---- */
.q0 { flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.p2 { display:none; flex:1; flex-direction:column; }
body[data-s="2"] .q0 { display:none; } body[data-s="2"] .p2 { display:flex; }
.q0 .qk { font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .2em; text-transform: uppercase; color: var(--green); }
.q0 .qq { font-size: 92px; font-weight: 800; letter-spacing: -.035em; line-height: 1.08; margin-top: 22px; max-width: 1500px; text-wrap: balance; }
.q0 .an { margin-top: 60px; font-size: 170px; font-weight: 900; letter-spacing: -.04em; line-height: 1; color: #D2452B;
  opacity: 0; transform: scale(1.6) rotate(-4deg); filter: blur(8px); transition: opacity .35s ease, transform .55s cubic-bezier(.3,1.6,.5,1), filter .35s ease; }
body[data-s="1"] .q0 .an { opacity: 1; transform: rotate(-4deg); filter: none; }
.q0 .an2 { font-size: 30px; color: var(--ink-2); margin-top: 26px; opacity: 0; transform: translateY(14px); transition: opacity .5s ease .45s, transform .6s ease .45s; }
body[data-s="1"] .q0 .an2 { opacity: 1; transform: none; }
''', '''
<div class="q0">
  <div class="qk u" style="--d:.05s">Quick question</div>
  <h1 class="qq u" style="--d:.2s">Once you start using AI, are these problems solved?</h1>
  <div class="an">Not necessarily.</div>
  <p class="an2">AI on its own can think. It cannot do.</p>
</div>
<div class="p2">
<div class="mk u" style="--d:.05s">So how do we fix it?</div>
<h1 class="mt u" style="--d:.15s">AI without tools is just a <em>Guru</em>.</h1>
<p class="ml u" style="--d:.3s">It thinks. It gives advice. But it cannot do the work.</p>
<div class="two">
  <div class="gu u" style="--d:.5s"><h3><span>AI WITHOUT TOOLS</span>The AI Guru</h3>
    <div class="gsc"><img src="../assets/av/agent-shades.svg" alt="The AI Guru in sunglasses">
      <div class="bub">''' + ''.join('<p style="--d:%.2fs">%s</p>' % (1.0 + k * .4, x) for k, x in enumerate(GU_SAYS)) + '''</div></div>
    <div class="stamp"><b>只会讲，不会做</b><small>ALL TALK, NO ACTION</small></div></div>
  <div class="ok u" style="--d:.8s"><h3><span>AI WITH SUDU TOOLS</span>The AI that does the work</h3>
    <div class="tls">''' + ''.join('<div style="--d:%.2fs"><i>%s</i><div><b>%s</b><span>%s</span></div></div>' % (1.4 + k * .3, ic(p, 40, 1.9), n, s_) for k, (p, n, s_) in enumerate(GU_TOOLS)) + '''</div>
    <div class="vd">''' + ic(CHECK, 28, 3) + '''It checks, counts, keys in and chases. You approve.</div></div>
</div>
<p class="bt u" style="--d:2.8s">To fix these 5 problems, AI needs hands. <b>SuDu gives it the hands: WMS and MES, on top of SQL Account.</b></p>
</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Quick question. Once you start using AI, are these problems solved?\" (let the room answer; most will say yes)\n\n(Next) \"Not necessarily. AI on its own can think. It cannot do.\"\n\n(Next) \"Here is the catch. AI without tools is just a guru. You know the type: very confident, very good advice. You should check your stock first. You should chase Kedai Ali. You should key in your orders faster. Thank you, guru.\" (pause) \"In Chinese we have a phrase for this: 只会讲，不会做. All talk, no action.\" (let the room laugh)\n\n"
"\"AI is the same. On its own, it can only think and suggest. To actually do the work, it needs tools: hands inside your business. That is what SuDu gives it. WMS for the warehouse: it scans, counts and picks your stock. MES for the factory: it tracks every job and every batch. All on top of SQL Account, where your orders, invoices and payments already live. Now the AI checks, counts, keys in and chases, and you approve.\"\n\nThis slide has 2 extra Next presses: the question, then \"Not necessarily\", then the Guru.\nNext: \"So with tools, the way we work changes.\"")

# ---------------- a new way of working: AI thinks and executes, people set rules and monitor ----------------
NW_AI = [('<path d="M12 5a3 3 0 00-5.9-.7A3 3 0 004 9a3 3 0 00.5 5.5A3 3 0 008 19a3 3 0 004 1V5z"/><path d="M12 5a3 3 0 015.9-.7A3 3 0 0120 9a3 3 0 01-.5 5.5A3 3 0 0116 19a3 3 0 01-4 1"/>', 'Thinks', 'Reads the order, plans every step'),
         ('<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>', 'Executes', 'Checks stock, keys in, sends, chases')]
NW_FEED = ['Read 3 WhatsApp orders', 'Drafted 3 Sales Orders', 'Sent 2 payment reminders']
NW_YOU = [('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>', 'Set the rules', 'Credit limits, prices, who approves'),
          ('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>', 'Monitor', 'See every action on 1 screen'),
          ('<path d="M4 12.5l5 5L20 6.5"/>', 'Approve', 'Nothing is posted without you')]
slide('25-new-way', 'A new way of working', SEC[1], 'light', 'data-sparks="none"', MIN_CSS + '''
.nw { display:grid; grid-template-columns: 1fr 150px 1fr; align-items: stretch; margin-top: 34px; height: 580px; margin-bottom: 24px; }
.nw .col { position:relative; display:flex; flex-direction:column; border-radius: 32px; padding: 28px 34px 26px; }
.nw .ai { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--green), 0 50px 80px -40px rgba(0,108,72,.6); }
.nw .you { background: #fff; box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); }
.nw .who { display:flex; align-items:center; gap: 22px; }
.nw .av { position:relative; width: 110px; height: 110px; flex:none; }
.nw .av img.p { width: 110px; height: 110px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px var(--line); }
.nw .av .logo { position:absolute; left: 50%; top: -22px; transform: translateX(-50%); height: 42px; padding: 6px 10px; border-radius: 10px; background: #fff; box-shadow: 0 6px 18px -6px rgba(0,0,0,.5); }
.nw .who small { display:block; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .16em; color: var(--ink-3); }
.nw .ai .who small { color: var(--on-dark-3); }
.nw .who b { display:block; font-size: 42px; font-weight: 800; letter-spacing: -.02em; margin-top: 4px; }
.nw .ai .who b { color: var(--neon); } .nw .you .who b { color: var(--ink); }
.nw .rl { display:grid; gap: 10px; margin-top: auto; }
.nw .fd { margin-top: 18px; padding: 12px 18px; border-radius: 18px; background: rgba(0,245,169,.06); box-shadow: inset 0 0 0 1px rgba(0,245,169,.25); }
.nw .fd small { display:flex; align-items:center; gap: 10px; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .16em; color: var(--neon); }
.nw .fd small i { width: 9px; height: 9px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 10px var(--neon); animation: blink 1.4s ease-in-out infinite; }
@keyframes blink { 50% { opacity: .25; } }
.nw .fd p { display:flex; align-items:center; gap: 10px; font-size: 21px; color: var(--on-dark); margin-top: 5px; opacity: 0; animation: pop .45s ease forwards; animation-delay: var(--d); }
.nw .fd p svg { color: var(--neon); flex:none; }
html.static .nw .fd p { opacity: 1; animation: none; }
.nw .rl > div { display:grid; grid-template-columns: 60px 1fr; gap: 16px; align-items:center; padding: 11px 16px; border-radius: 20px; opacity: 0; transform: translateY(14px); animation: pop .55s cubic-bezier(.3,1.4,.5,1) forwards; animation-delay: var(--d); }
@keyframes pop { to { opacity: 1; transform: none; } }
.nw .ai .rl > div { background: rgba(242,251,247,.06); box-shadow: inset 0 0 0 1px rgba(242,251,247,.12); }
.nw .you .rl > div { background: #F3F6F4; }
.nw .rl i { width: 60px; height: 60px; border-radius: 20px; display:grid; place-items:center; }
.nw .ai .rl i { color: var(--neon); background: rgba(0,245,169,.12); } .nw .you .rl i { color: var(--green); background: var(--mint); }
.nw .rl b { display:block; font-size: 30px; font-weight: 800; letter-spacing: -.01em; }
.nw .rl span { display:block; font-size: 23px; margin-top: 2px; } .nw .ai .rl span { color: var(--on-dark-2); } .nw .you .rl span { color: var(--ink-2); }
.nw .mid { display:flex; flex-direction:column; justify-content:center; align-items:center; gap: 40px; }
.nw .ar { display:flex; flex-direction:column; align-items:center; gap: 6px; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .14em; color: var(--green); }
.nw .ar svg { animation: nudge 1.8s ease-in-out infinite; } .nw .ar.b svg { animation-name: nudgeb; }
@keyframes nudge { 50% { transform: translateX(-8px); } } @keyframes nudgeb { 50% { transform: translateX(8px); } }
.bt { display:flex; gap: 40px; font-size: 28px; color: var(--ink-2); }
.bt div { display:flex; align-items:baseline; gap: 14px; } .bt small { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .14em; color: var(--ink-3); }
.bt b { color: var(--ink); } .bt .now small { color: var(--green); } .bt .now b { color: var(--green); }
html.static .nw .rl > div { opacity: 1; transform: none; animation: none; } html.static .nw .ar svg { animation: none; }
''', '''
<div class="mk u" style="--d:.05s">A new way of working</div>
<h1 class="mt u" style="--d:.15s">AI does the work. <em>You run the rules.</em></h1>
<p class="ml u" style="--d:.3s">With tools, AI thinks and executes. People set the rules and keep watch.</p>
<div class="nw">
  <div class="col ai u" style="--d:.5s"><div class="who"><div class="av"><img class="p" src="../assets/av/agent-thumbs.svg" alt="The SuDu AI Agent"><img class="logo" src="../assets/logo-dark.png" alt="SuDu AI"></div>
    <div><small>THE AI AGENT</small><b>Does the work</b></div></div>
    <div class="fd"><small><i></i>WORKING NOW</small>''' + ''.join('<p style="--d:%.2fs">%s%s</p>' % (2.0 + k * .4, ic(CHECK, 22, 3), x) for k, x in enumerate(NW_FEED)) + '''</div>
    <div class="rl">''' + ''.join('<div style="--d:%.2fs"><i>%s</i><div><b>%s</b><span>%s</span></div></div>' % (1.0 + k * .25, ic(p, 36, 1.9), h, s_) for k, (p, h, s_) in enumerate(NW_AI)) + '''</div></div>
  <div class="mid"><span class="ar u" style="--d:1.6s">''' + ic('<path d="M19 12H5M11 6l-6 6 6 6"/>', 44, 2.4) + '''RULES</span><span class="ar b u" style="--d:1.8s">''' + ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 44, 2.4) + '''REPORTS</span></div>
  <div class="col you u" style="--d:.7s"><div class="who"><div class="av"><img class="p" src="../assets/av/boss-wow.svg" alt="The boss"></div>
    <div><small>YOU</small><b>Run the rules</b></div></div>
    <div class="rl">''' + ''.join('<div style="--d:%.2fs"><i>%s</i><div><b>%s</b><span>%s</span></div></div>' % (1.2 + k * .25, ic(p, 36, 1.9), h, s_) for k, (p, h, s_) in enumerate(NW_YOU)) + '''</div></div>
</div>
<div class="bt u" style="--d:2.2s"><div><small>BEFORE</small><span>People do the work. Software keeps the records.</span></div><div class="now"><small>NOW</small><b>AI does the work. People run it.</b></div></div>
''',
"\"So with tools, the way we work changes. The AI Agent does the work: it thinks, it reads the order and plans every step, and it executes: checks the stock, keys in, sends, chases.\n\nAnd you? You run the rules. You set them: credit limits, prices, who approves what. You monitor: every action on 1 screen. And you approve: nothing is posted without you. Rules go to the AI, reports come back to you.\n\nBefore, people did the work and software kept the records. Now, AI does the work, and people run it. That is a new way of working.\"\n\nNext: \"And the part that makes this possible is the tools.\"")

# ---------------- meme: before AI the problems run the boss, after AI the boss runs the AI ----------------
MM_PROB = [('Staff on leave', 8, 10, -8), ('High costs', 64, 6, 6), ('Wrong stock', 2, 58, 5), ('Slow work', 66, 56, -6), ('Can&rsquo;t hire', 30, 84, 3)]
MM_DONE = [('Orders keyed in', 4, 4), ('Stock counted', 60, 4), ('Payments chased', 2, 80), ('Reports done', 62, 80)]
slide('25-meme', 'Before AI, after AI', SEC[1], 'dark bare', 'data-sparks="none"', MIN_CSS + '''
body { background: #010F0D; }
.c { flex:1; display:flex; flex-direction:column; }
.mk { color: var(--neon); }
.mt { color: var(--on-dark); font-size: 74px; }
.mt em { color: var(--neon); }
.pn { display:grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 36px; flex:1; min-height: 0; margin-bottom: 40px; }
.pn > div { position:relative; display:flex; flex-direction:column; border-radius: 30px; overflow:hidden; padding: 24px; }
.bf { background: linear-gradient(160deg, #3A1712, #1C0B08); box-shadow: 0 0 0 3px #D2452B; }
.af { background: linear-gradient(160deg, #06352D, #021A17); box-shadow: 0 0 0 3px var(--neon), 0 0 60px rgba(0,245,169,.25); }
.cap { position:relative; z-index: 2; align-self:center; font-size: 52px; font-weight: 900; letter-spacing: .02em; text-transform: uppercase; color: #fff; padding: 6px 26px; border-radius: 12px; }
.bf .cap { background: #D2452B; } .af .cap { background: var(--neon); color: #02221F; }
.stg { position:relative; flex:1; }
.stg .boss { position:absolute; left: 50%; top: 50%; width: 230px; height: 230px; margin: -115px 0 0 -115px; border-radius: 50%; background: #fff; }
.bf .boss { animation: shake .35s ease-in-out infinite; box-shadow: 0 0 0 8px rgba(210,69,43,.35); }
@keyframes shake { 0%, 100% { transform: translate(0, 0) rotate(0); } 25% { transform: translate(-4px, 2px) rotate(-3deg); } 75% { transform: translate(4px, -2px) rotate(3deg); } }
.af .boss { box-shadow: 0 0 0 8px rgba(0,245,169,.3); animation: chill 3s ease-in-out infinite; }
@keyframes chill { 50% { transform: translateY(-6px); } }
.sw { position:absolute; left: calc(50% + 70px); top: calc(50% - 130px); font-size: 60px; font-weight: 900; color: #FFB547; animation: drop 1.2s ease-in infinite; }
@keyframes drop { 0% { opacity: 0; transform: translateY(-10px); } 30% { opacity: 1; } 100% { opacity: 0; transform: translateY(40px); } }
.tg { position:absolute; z-index: 1; font-size: 30px; font-weight: 800; padding: 12px 20px; border-radius: 14px; white-space: nowrap; opacity: 0; animation: hit .45s cubic-bezier(.3,1.7,.5,1) forwards, wob 2.2s ease-in-out infinite; animation-delay: var(--d), calc(var(--d) + .45s); }
.bf .tg { background: #FFE2A8; color: #8A3417; box-shadow: 0 12px 24px -10px rgba(0,0,0,.6); transform: rotate(var(--r)); }
@keyframes hit { from { opacity: 0; transform: scale(2.2) rotate(var(--r)); } to { opacity: 1; transform: scale(1) rotate(var(--r)); } }
@keyframes wob { 50% { transform: scale(1.05) rotate(calc(var(--r) * -1)); } }
.af .tg { display:flex; align-items:center; gap: 10px; background: rgba(0,245,169,.14); color: var(--on-dark); box-shadow: inset 0 0 0 2px rgba(0,245,169,.45); animation: hit2 .5s cubic-bezier(.3,1.4,.5,1) forwards; animation-delay: var(--d); }
.af .tg svg { color: var(--neon); }
@keyframes hit2 { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
.af .agt { position:absolute; width: 96px; height: 96px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 4px rgba(0,245,169,.4); }
.af .agt.a1 { left: calc(50% - 236px); top: calc(50% - 48px); } .af .agt.a2 { left: calc(50% + 140px); top: calc(50% - 48px); }
.af .agt { animation: chill 2.4s ease-in-out infinite; } .af .agt.a2 { animation-delay: .6s; }
.sub { position:relative; z-index: 2; align-self:center; font-size: 34px; font-weight: 800; color: #fff; text-align:center; }
.af .sub { color: var(--neon); }
html.static .tg { opacity: 1; animation: none; } html.static .bf .tg { transform: rotate(var(--r)); } html.static .boss, html.static .agt { animation: none; } html.static .sw { display:none; }
''', '''
<div class="c">
  <div class="mk u" style="--d:.05s">Be honest</div>
  <h1 class="mt u" style="--d:.15s">Who is the boss <em>of your company</em>?</h1>
  <div class="pn">
    <div class="bf u" style="--d:.4s"><span class="cap">Before AI</span>
      <div class="stg"><img class="boss" src="../assets/av/boss-facepalm.svg" alt="The boss, stressed"><span class="sw">!</span>''' + ''.join('<span class="tg" style="--d:%.2fs;--r:%ddeg;left:%d%%;top:%d%%">%s</span>' % (.9 + k * .3, r, x, y, n) for k, (n, x, y, r) in enumerate(MM_PROB)) + '''</div>
      <span class="sub">The problems run the boss.</span></div>
    <div class="af u" style="--d:.7s"><span class="cap">After AI</span>
      <div class="stg"><img class="boss" src="../assets/av/boss-wow.svg" alt="The boss, relaxed"><img class="agt a1" src="../assets/av/agent-typing.svg" alt=""><img class="agt a2" src="../assets/av/agent-thumbs.svg" alt="">''' + ''.join('<span class="tg" style="--d:%.2fs;left:%d%%;top:%d%%">%s%s</span>' % (2.6 + k * .3, x, y, ic(CHECK, 24, 3), n) for k, (n, x, y) in enumerate(MM_DONE)) + '''</div>
      <span class="sub">The boss runs the AI.</span></div>
  </div>
</div>
''',
"(This one is for a laugh. Let it land.)\n\n\"Be honest: who is the boss of your company? Before AI, it is the problems. Staff on leave. High costs. Wrong stock. Slow work. Can't hire anyone. The boss gets beaten up every day.\" (pause)\n\n\"After AI: orders keyed in, stock counted, payments chased, reports done. The AI does the work, and the boss is the boss again.\"\n\nNext: \"And the part that makes this possible is the tools.\"")

# ---------------- meme image (the user's own picture): before AI, after AI ----------------
slide('25-meme-img', 'Before AI, after AI (meme)', SEC[1], 'light bare', 'data-sparks="none"', '''
body { background: #FFFFFF; }
.slide { padding: 0 !important; }
.mi { position:absolute; inset: 0; display:grid; place-items:center; background: #FFFFFF; }
.mi img { height: 96%; width: auto; max-width: 96%; object-fit: contain; display:block; opacity: 0; transform: scale(.96); animation: mIn .8s cubic-bezier(.2,.75,.15,1) .1s forwards; }
@keyframes mIn { to { opacity: 1; transform: none; } }
html.static .mi img { opacity: 1; transform: none; animation: none; }
''', '''
<div class="mi"><img src="../assets/img/meme-before-after.webp" alt="Meme: before AI and after AI"></div>
''',
"(This one is for a laugh. Let it land.)\n\n\"Be honest: before AI, who is really the boss of your company? The problems. Staff on leave, high costs, wrong stock, slow work, can't hire anyone. After AI, the boss is the boss again, and the AI does the hard work.\"\n\nNext: \"So how does AI help? Let's start with the big question: what is AI, really?\"")

slide('24-tools-and-memory', 'No tools, no work', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.chain { display:flex; align-items:stretch; justify-content:space-between; margin-top: 70px; }
.chain .ar { align-self: center; }
.chain .nd { width: 440px; display:flex; flex-direction:column; align-items:center; text-align:center; padding: 40px 30px 36px; border-radius: 32px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); }
.chain .nd.last { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--green), 0 50px 80px -40px rgba(0,108,72,.6); }
.chain .pic { width: 170px; height: 170px; border-radius: 50%; display:grid; place-items:center; background: var(--mint); color: var(--green); overflow:hidden; }
.chain .pic img { width: 100%; height: 100%; }
.chain .pic i { display:flex; }
.chain .last .pic { background: rgba(0,245,169,.14); color: var(--neon); }
.chain b { font-size: 46px; font-weight: 800; letter-spacing: -.025em; margin-top: 26px; }
.chain .nd span { font-size: 27px; color: var(--ink-2); margin-top: 8px; } .chain .last span { color: var(--on-dark-2); }
.chain .ar { color: var(--green); display:flex; }
.erp { margin-top: auto; margin-bottom: 50px; font-size: 30px; color: var(--ink-2); }
.p0, .p1 { flex:1; display:flex; flex-direction:column; }
.p1 { display:none; } body[data-s="1"] .p0 { display:none; } body[data-s="1"] .p1 { display:flex; }
.e2 { display:grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 30px; height: 490px; margin-bottom: 24px; }
.e2 > div { position:relative; display:flex; flex-direction:column; border-radius: 30px; padding: 30px 34px; overflow:hidden; }
.e2 .bd { background: #FBF7EF; box-shadow: inset 0 0 0 2px #F1E2C2; }
.e2 .gd { background: #EAF7F1; box-shadow: inset 0 0 0 3px var(--green); }
.e2 h3 { font-size: 40px; font-weight: 800; letter-spacing: -.02em; }
.e2 .gd h3 { font-size: 31px; line-height: 1.2; }
.e2 .hub .lg { display:flex; align-items:center; justify-content:center; gap: 12px; } .e2 .hub .lg img { height: 38px; } .e2 .hub .lg img.sq { height: 58px; }
.e2 .hub .lg i { font-style: normal; font-size: 28px; font-weight: 800; color: var(--green); }
.e2 .bd h3 { color: #8A3417; } .e2 .gd h3 { color: var(--green); }
.e2 .scene { position:relative; flex:1; min-height: 0; margin-top: 10px; }
.e2 .av { position:absolute; width: 170px; height: 170px; border-radius: 50%; box-shadow: 0 0 0 1px var(--line), 0 20px 40px -20px rgba(2,34,31,.4); background:#fff; }
.e2 .bd .av { left: 50%; top: 50%; transform: translate(-50%, -50%); }
.e2 .qm { position:absolute; left: calc(50% + 60px); top: calc(50% - 120px); font-size: 64px; font-weight: 800; color: #C77800; }
.e2 .src { position:absolute; display:flex; align-items:center; gap: 12px; padding: 14px 18px; border-radius: 16px; background: #fff; font-size: 24px; font-weight: 650; color: #5B4A33; box-shadow: 0 0 0 1px #F1E2C2, 0 14px 30px -18px rgba(90,60,20,.45); }
.e2 .src i { color: #C77800; display:flex; }
.e2 .src.s1 { left: 0; top: 4%; transform: rotate(-4deg); } .e2 .src.s2 { right: 0; top: 8%; transform: rotate(3deg); }
.e2 .src.s3 { left: 2%; bottom: 8%; transform: rotate(3deg); } .e2 .src.s4 { right: 2%; bottom: 4%; transform: rotate(-3deg); }
.e2 .hub { position:absolute; left: 50%; top: 50%; margin: -88px 0 0 -205px; width: 410px; padding: 22px 18px; border-radius: 26px; background: #fff; text-align:center; box-shadow: 0 0 0 3px var(--green), 0 26px 50px -24px rgba(0,108,72,.55); }
.e2 .hub img { height: 42px; } .e2 .hub b { display:block; font-size: 22px; font-weight: 700; color: var(--ink); margin-top: 8px; } .e2 .hub span { display:block; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .1em; color: var(--ink-3); margin-top: 4px; }
.e2 .tl { position:absolute; display:flex; align-items:center; gap: 10px; padding: 12px 18px; border-radius: 999px; background: var(--green); color: #fff; font-size: 23px; font-weight: 700; box-shadow: 0 12px 26px -14px rgba(0,108,72,.7); }
.e2 .tl.t1 { left: 0; top: 4%; } .e2 .tl.t2 { right: 0; top: 4%; } .e2 .tl.t3 { left: 0; bottom: 4%; } .e2 .tl.t4 { right: 0; bottom: 4%; }
.e2 svg.wires { position:absolute; inset: 0; width: 100%; height: 100%; }
.e2 .gd .av { width: 120px; height: 120px; right: 50%; top: -6px; transform: translateX(50%); display:none; }
.e2 .vd2 { display:flex; align-items:center; gap: 12px; font-size: 28px; font-weight: 750; margin-top: 14px; }
.e2 .bd .vd2 { color: #8A3417; } .e2 .gd .vd2 { color: var(--green); }
.bt2 { font-size: 32px; color: var(--ink-2); } .bt2 b { color: var(--ink); }

.erp b { color: var(--ink); }
''', '''
<div class="p0">
<div class="mk u" style="--d:.05s">Tools</div>
<h1 class="mt u" style="--d:.2s">No tools, no <em>work</em></h1>
<p class="ml u" style="--d:.4s">A brain alone gives advice. Tools let it do the job.</p>
<div class="chain"><div class="nd u" style="--d:0.60s"><div class="pic"><img src="../assets/av/agent-hi.svg" alt="The SuDu agent"></div><b>The brain</b><span>Understands and plans</span></div><span class="ar u" style="--d:1.10s"><svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span><div class="nd u" style="--d:0.95s"><div class="pic"><i><svg width="70" height="70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 13V5.5a1.5 1.5 0 013 0V12M11 11V4a1.5 1.5 0 013 0v7M14 11V5.5a1.5 1.5 0 013 0V14c0 4-3 7-7 7-3 0-4.6-1.6-6-4l-2-4a1.5 1.5 0 012.6-1.5L8 15"/></svg></i></div><b>The tools</b><span>Check stock, create orders, send</span></div><span class="ar u" style="--d:1.45s"><svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span><div class="nd u last" style="--d:1.30s"><div class="pic"><i><svg width="70" height="70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg></i></div><b>Your ERP</b><span>Where stock, orders and money live</span></div></div>
<p class="erp u" style="--d:1.8s">Every tool works inside your <b>ERP</b>, the core of the company: customers, stock, invoices, money.</p>
</div>
<div class="p1">
<div class="mk u" style="--d:.05s">Tools need an ERP</div>
<h1 class="mt u" style="--d:.15s">No proper ERP, <em>no AI work</em></h1>
<p class="ml u" style="--d:.3s">Every tool is a button inside your ERP. If your company runs on paper and chats, there is <b>no button to press</b>.</p>
<div class="e2">
  <div class="bd u" style="--d:.5s"><h3>Without a proper ERP</h3><div class="scene"><div class="src s1 u" style="--d:0.80s"><i><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/></svg></i>Paper notebook</div><div class="src s2 u" style="--d:0.95s"><i><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 21h8M12 18v3"/></svg></i>Excel on 3 PCs</div><div class="src s3 u" style="--d:1.10s"><i><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg></i>WhatsApp chats</div><div class="src s4 u" style="--d:1.25s"><i><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i>In the boss&rsquo;s head</div><img class="av" src="../assets/av/agent-mind.svg" alt="The agent, puzzled"><span class="qm">?</span></div><div class="vd2"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18"/></svg>Nothing to check, nothing to click. It can only guess.</div></div>
  <div class="gd u" style="--d:.8s"><h3>With SQL (Accounting) + SuDu AI (WMS &amp; MES)</h3><div class="scene"><svg class="wires" viewBox="0 0 100 100" preserveAspectRatio="none"><g stroke="#00A57A" stroke-width=".5" stroke-dasharray="2 2" fill="none"><path d="M22 12 L50 50"/><path d="M78 12 L50 50"/><path d="M22 88 L50 50"/><path d="M78 88 L50 50"/></g></svg><div class="hub u" style="--d:1.1s"><div class="lg"><img class="sq" src="../assets/logos/sql-account-payroll.png" alt="SQL Account"><i>+</i><img src="../assets/logo-dark.png" alt="SuDu AI"></div><b>1 place for all your data</b><span>SQL ACCOUNT &middot; WMS &middot; MES</span></div><div class="tl t1 u" style="--d:1.30s"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Check stock</div><div class="tl t2 u" style="--d:1.45s"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Create Sales Order</div><div class="tl t3 u" style="--d:1.60s"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Send the DO</div><div class="tl t4 u" style="--d:1.75s"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Record payment</div></div><div class="vd2"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Every tool has a real button. The agent does the job.</div></div>
</div>
<p class="bt2 u" style="--d:2s">That is why SuDu comes first: <b>an AI Agent is only as good as the system it works in.</b></p>
</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Here is the part people forget. The smartest brain in the world, with no tools, can only talk. The brain understands and plans. The tools are its hands: check stock, create an order, send a message. And every tool works inside 1 place: your ERP, where your customers, stock, orders and money live.\"\n\n(Next) \"And here is the catch. Every tool is a button inside your ERP. Look at the left: many companies run on a paper notebook, Excel on 3 different PCs, WhatsApp chats, and things only the boss remembers. Give an AI Agent that company, and what can it do? Nothing to check, nothing to click. It can only guess, and a guess is dangerous. On the right is SuDu: 1 place for all your data, SQL Account, warehouse and factory, and every job has a real button: check stock, create the Sales Order, send the DO, record the payment. Now the agent can do the work. So remember: an AI Agent is only as good as the system it works in. That is why SuDu comes first.\"\n\nThis slide has 1 extra Next press: why tools need a proper ERP.\nNext: \"So in the warehouse, what does that system look like? SuDu WMS.\"")


# ---------------- slide: what is an AI agent ----------------
AGENT_PARTS = [  # (part, name, short, tag, what, hows, like, eg)
    ('brain', 'Brain', 'thinks', '',
     'The language model (LLM). It turns a messy message into a clear plan: what is asked, what is missing, what to do next.',
     ['It understands meaning, not keywords: &ldquo;bwg&rdquo;, &ldquo;bawang&rdquo; and &ldquo;onion&rdquo; are the same thing.',
      'It breaks a job into steps, and picks the next step after every result.',
      'On its own, it has never seen your company: not your customers, prices or stock.'],
     'A smart new graduate: quick to understand, but knows nothing about your company on day 1.',
     '&ldquo;bwg besar 10kg x ---&rdquo; &rarr; big onions, 10 kg bags, quantity missing, so ask.'),
    ('tools', 'Tools', 'does the work', 'NO TOOLS, NO WORK',
     'Each tool is 1 action in a real system. The brain picks the tool, the tool does the job and reports back.',
     ['Tools that look: check stock, read an invoice, check a credit limit.',
      'Tools that act: create an order, send a message, record a payment.',
      'The brain cannot click a button. With no tool, it can only tell you what to do.'],
     'A login to each system, like you give a new clerk.',
     'Check stock &rarr; 42 bags. Create order &rarr; draft order ready to approve.'),
    ('memory', 'Memory', 'knows your data', '',
     'What it can look up while it works. The brain forgets everything after each chat, so memory is kept outside it.',
     ['Short term: this chat and this job, what was said 2 messages ago.',
      'Taught: what you correct once and it keeps, like &ldquo;Milo means the 1 kg pack&rdquo;.',
      'Records: customers, prices and stock, looked up fresh every time, never guessed.'],
     'The desk, the notebook and the filing cabinet.',
     'Jaya Grocer&rsquo;s last price for big onions: RM28 a bag. Messy records in, wrong answers out.'),
    ('rules', 'Rules &amp; skills', 'your SOP', '',
     'Your way of working, written down. Rules say what must never happen. Skills say the steps for each job.',
     ['Rules are hard limits, checked every time, not left to the brain&rsquo;s judgement.',
      'Skills are step-by-step recipes for 1 job, like &ldquo;take a WhatsApp order&rdquo;.',
      'Written in plain words, so a manager can read them and change them.'],
     'Your SOP binder and on-the-job training.',
     'Rule: over the credit limit, stop and ask the boss. Skill: read, match items, check stock, draft, send for approval.'),
    ('perm', 'Permission', 'what it may touch', 'KEEPS IT SAFE',
     'What it is allowed to see and do, set for each agent. This is the difference between a helper and a risk.',
     ['See: only the data its job needs. The order agent never sees salaries.',
      'Do: only the actions you allow. Draft yes, delete no, move money never.',
      'Approve: anything important waits for a person, and every action is logged.'],
     'Which keys you hand over, and which papers still need your signature.',
     'It can draft a sales order. It cannot delete an invoice. A payment waits for you.'),
]
LOOP = [('Read', 'A WhatsApp order comes in from Jaya Grocer.', 'Brain'),
        ('Plan', 'Match each item to your stock codes. Check stock and credit.', 'Memory'),
        ('Act', 'Draft the sales order in your ERP.', 'Tools'),
        ('Check', '&ldquo;25mm clear&rdquo; is unclear, so it asks the customer.', 'Rules'),
        ('Report', 'Sends the order to you. You tap approve.', 'Permission')]

_S = 'rgba(0,245,169,.38)'
def _lbl(k, x, y, lx, ly, ex, ey, anchor='start'):
    """leader from part (x,y) to label end (ex,ey); label text at (lx,ly)"""
    _, name, short, *_r = AGENT_PARTS[k - 1]
    return ('<g class="lb"><path class="ld" d="M%d %dL%d %d" pathLength="1"/><circle class="dot" cx="%d" cy="%d" r="6"/>'
            '<circle class="nb" cx="%d" cy="%d" r="17"/><text class="nn" x="%d" y="%d">%d</text>'
            '<text class="ln" x="%d" y="%d" text-anchor="%s">%s</text><text class="ls" x="%d" y="%d" text-anchor="%s">%s</text></g>'
            % (x, y, ex, ey, x, y, ex, ey, ex, ey + 6, k, lx, ly, anchor, name.replace('&amp;', '&amp;'), lx, ly + 30, anchor, short))

ROBOT = '''<svg class="rbt" viewBox="0 0 820 780" aria-label="An AI agent drawn as a robot, with its 5 parts labelled">
<defs>
 <linearGradient id="rb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22483F"/><stop offset="1" stop-color="#0B2420"/></linearGradient>
 <linearGradient id="rh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2B5A50"/><stop offset="1" stop-color="#0D2A25"/></linearGradient>
 <radialGradient id="rg"><stop offset="0" stop-color="#00F5A9" stop-opacity=".55"/><stop offset="1" stop-color="#00F5A9" stop-opacity="0"/></radialGradient>
</defs>
<ellipse cx="380" cy="706" rx="200" ry="28" fill="url(#rg)" opacity=".7"/>
<g class="bob">
 <ellipse class="flame" cx="380" cy="596" rx="30" ry="40" fill="url(#rg)"/>
 <path d="M334 540h92l-14 34h-64z" fill="#0B2420" stroke="''' + _S + '''" stroke-width="2"/>
 <ellipse cx="380" cy="576" rx="22" ry="5" fill="#00F5A9" opacity=".85"/>
 <path d="M268 340C212 360 192 408 212 466" fill="none" stroke="''' + _S + '''" stroke-width="36" stroke-linecap="round"/>
 <path d="M268 340C212 360 192 408 212 466" fill="none" stroke="#1A3E37" stroke-width="31" stroke-linecap="round"/>
 <path d="M492 340C556 324 590 286 598 232" fill="none" stroke="''' + _S + '''" stroke-width="36" stroke-linecap="round"/>
 <path d="M492 340C556 324 590 286 598 232" fill="none" stroke="#1A3E37" stroke-width="31" stroke-linecap="round"/>
 <rect x="262" y="300" width="236" height="246" rx="58" fill="url(#rb)" stroke="''' + _S + '''" stroke-width="2"/>
 <path d="M290 320h180" stroke="rgba(242,251,247,.12)" stroke-width="2" stroke-linecap="round"/>
 <rect x="352" y="280" width="56" height="26" rx="8" fill="#0B2420" stroke="''' + _S + '''" stroke-width="2"/>
 <line x1="380" y1="86" x2="380" y2="50" stroke="''' + _S + '''" stroke-width="5" stroke-linecap="round"/>
 <circle class="ant" cx="380" cy="42" r="11" fill="#00F5A9"/>
 <rect x="248" y="84" width="264" height="204" rx="76" fill="url(#rh)" stroke="''' + _S + '''" stroke-width="2"/>
 <circle cx="246" cy="208" r="19" fill="#0B2420" stroke="''' + _S + '''" stroke-width="2"/><circle cx="246" cy="208" r="7" fill="#00F5A9" opacity=".6"/>
 <circle cx="514" cy="208" r="19" fill="#0B2420" stroke="''' + _S + '''" stroke-width="2"/><circle cx="514" cy="208" r="7" fill="#00F5A9" opacity=".6"/>
 <rect x="284" y="202" width="192" height="60" rx="30" fill="#021A17" stroke="rgba(0,245,169,.5)" stroke-width="2"/>
 <g class="eyes"><rect x="318" y="222" width="34" height="18" rx="9" fill="#00F5A9"/><rect x="408" y="222" width="34" height="18" rx="9" fill="#00F5A9"/></g>

 <g class="pt p1">
  <circle class="ring" cx="380" cy="142" r="84"/>
  <ellipse cx="380" cy="142" rx="76" ry="48" fill="rgba(0,245,169,.07)" stroke="rgba(0,245,169,.45)" stroke-width="2"/>
  <g class="brain" fill="rgba(0,245,169,.16)" stroke="#00F5A9" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">
   <path d="M377 106C351 98 327 110 327 131C313 141 317 165 335 169C343 179 364 179 377 172Z"/>
   <path d="M383 106C409 98 433 110 433 131C447 141 443 165 425 169C417 179 396 179 383 172Z"/>
   <path d="M347 125c10 0 16 6 16 14M341 151c10-4 20 0 24 8M413 125c-10 0-16 6-16 14M419 151c-10-4-20 0-24 8" fill="none"/>
  </g>
 </g>
 <g class="pt p2">
  <circle class="ring" cx="606" cy="190" r="70"/>
  <circle cx="598" cy="232" r="22" fill="#0B2420" stroke="#00F5A9" stroke-width="3"/>
  <path transform="translate(588 148) scale(3)" d="M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z" fill="#0B2420" stroke="#00F5A9" stroke-width="1.1" stroke-linejoin="round"/>
  <g class="spk" stroke="#00F5A9" stroke-width="3" stroke-linecap="round"><path d="M664 186l16 4M662 206h16M654 224l10 10"/></g>
 </g>
 <g class="pt p3">
  <circle class="ring" cx="380" cy="458" r="80"/>
  <rect x="316" y="404" width="128" height="110" rx="14" fill="#06201C" stroke="#00F5A9" stroke-width="2.5"/>
  <path d="M316 441h128M316 478h128" stroke="#00F5A9" stroke-width="2" opacity=".7"/>
  <g fill="#00F5A9"><rect x="366" y="419" width="28" height="7" rx="3.5"/><rect x="366" y="456" width="28" height="7" rx="3.5"/><rect x="366" y="493" width="28" height="7" rx="3.5"/></g>
 </g>
 <g class="pt p4">
  <circle class="ring" cx="184" cy="478" r="70"/>
  <g transform="rotate(-10 182 478)">
   <rect x="148" y="434" width="70" height="90" rx="8" fill="#0B2420" stroke="#00F5A9" stroke-width="3"/>
   <path d="M160 434v90" stroke="#00F5A9" stroke-width="3"/>
   <path d="M172 462l7 7 14-14M172 492h32M172 506h22" fill="none" stroke="#00F5A9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <circle cx="214" cy="468" r="20" fill="#1A3E37" stroke="''' + _S + '''" stroke-width="2"/>
 </g>
 <g class="pt p5">
  <circle class="ring" cx="380" cy="356" r="56"/>
  <path d="M380 324l32 12v20c0 20-14 32-32 40c-18-8-32-20-32-40v-20z" fill="rgba(255,181,71,.16)" stroke="#FFB547" stroke-width="3" stroke-linejoin="round"/>
  <rect x="369" y="352" width="22" height="17" rx="3" fill="#FFB547"/>
  <path d="M373 352v-5a7 7 0 0114 0v5" fill="none" stroke="#FFB547" stroke-width="3"/>
 </g>
</g>
<g class="lbs">
 <g class="pt p1">''' + _lbl(1, 304, 128, 176, 120, 200, 128, 'end') + '''</g>
 <g class="pt p2">''' + _lbl(2, 628, 162, 656, 100, 628, 106) + '''</g>
 <g class="pt p5">''' + _lbl(5, 414, 356, 626, 350, 604, 364) + '''</g>
 <g class="pt p3">''' + _lbl(3, 446, 470, 626, 490, 604, 504) + '''</g>
 <g class="pt p4">''' + _lbl(4, 160, 528, 30, 660, 112, 604) + '''</g>
</g>
</svg>'''

def _agent_detail():
    out = ''
    for i, (_, t, short, tag, what, hows, like, eg) in enumerate(AGENT_PARTS):
        out += ('<div class="dt" data-s="%d"><small class="pn">PART %d OF 5%s</small><h2>%s</h2><p class="what">%s</p>'
                '<h4>HOW IT WORKS</h4><ul>%s</ul>'
                '<div class="two"><div><small>LIKE</small><b>%s</b></div><div class="eg"><small>EXAMPLE</small><b>%s</b></div></div></div>'
                % (i + 1, i + 1, (' <span class="tg">' + tag + '</span>') if tag else '', t, what,
                   ''.join('<li><i></i><span>%s</span></li>' % h for h in hows), like, eg))
    return out



# ---------------- slide: the agent loop ----------------
LOOP_NODES = [('Think', 'Plan the\nnext step', 330, 70), ('Act', 'Use\n1 tool', 560, 300), ('Observe', 'Read what\ncame back', 330, 530), ('Check', 'Done? Safe?\nRight?', 100, 300)]
ROUNDS = [('1', 'Think', 'Which items are in this order?', 'search items', 'Bawang Besar China 10kg found. 42 bags in stock.', 'ok'),
          ('2', 'Think', 'Can Jaya Grocer take RM560 more?', 'check credit', 'Only RM180 left on the credit limit.', 'warn'),
          ('3', 'Check', 'Over the limit. Rule: the boss decides.', 'ask for approval', 'Request sent to the boss. The agent waits.', 'stop')]
def _loop_svg():
    o = ('<svg class="lp" viewBox="0 0 660 620"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#00F5A9"/></marker></defs>'
         '<circle cx="330" cy="300" r="230" fill="none" stroke="rgba(0,245,169,.25)" stroke-width="3" stroke-dasharray="6 12"/>')
    for a0, a1 in [(-62, -28), (28, 62), (118, 152), (208, 242)]:
        import math
        x0, y0 = 330 + 230 * math.cos(math.radians(a0)), 300 + 230 * math.sin(math.radians(a0))
        x1, y1 = 330 + 230 * math.cos(math.radians(a1)), 300 + 230 * math.sin(math.radians(a1))
        o += '<path d="M%.1f %.1f A230 230 0 0 1 %.1f %.1f" fill="none" stroke="#00F5A9" stroke-width="4" marker-end="url(#ah)"/>' % (x0, y0, x1, y1)
    o += ('<circle r="10" fill="#00F5A9"><animateMotion dur="4s" repeatCount="indefinite" path="M330 70 A230 230 0 1 1 329.9 70"/></circle>'
          '<text class="mid" x="330" y="292" text-anchor="middle">Loop until</text><text class="mid" x="330" y="330" text-anchor="middle">the job is done</text>')
    for k, (n, s_, x, y) in enumerate(LOOP_NODES):
        l1, l2 = s_.split('\n')
        o += ('<g class="nd" style="--d:%.2fs"><circle cx="%d" cy="%d" r="72" fill="#062824" stroke="#00F5A9" stroke-width="3"/>'
              '<text class="nn" x="%d" y="%d" text-anchor="middle">%s</text><text class="ns" x="%d" y="%d" text-anchor="middle">%s</text><text class="ns" x="%d" y="%d" text-anchor="middle">%s</text></g>'
              % (.5 + k * .2, x, y, x, y - 6, n, x, y + 20, l1, x, y + 40, l2))
    return o + '</svg>'
def _rounds():
    out = ''
    for k, (n, kind, th, tool, seen, st) in enumerate(ROUNDS):
        out += ('<div class="rd %s r" style="--d:%.2fs"><div class="rn">ROUND %s</div>'
                '<div class="ln"><b>%s</b><span>%s</span></div><div class="ln"><b>Act</b><span class="tl">%s</span></div><div class="ln"><b>See</b><span>%s</span></div></div>'
                % (st, 1.6 + k * .6, n, kind, th, tool, seen))
    return out

HIRE = [  # icon, new clerk gets, agent gets, what that is, without it
    ('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>', 'A job description', 'Instructions', 'The goal, and when the job counts as done', 'It does too much, or the wrong job.'),
    ('<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3"/>', 'A login and keys', 'Tools', '1 tool per action: some look, some act', 'It can only give advice.'),
    ('<path d="M3 9h18M5 9v11M19 9v11M5 14h14"/><rect x="8" y="4" width="8" height="5" rx="1"/>', 'A desk and the files', 'Memory', 'This chat, what you taught it, your records', 'It forgets the customer and guesses the price.'),
    ('<path d="M4 4h16v16H4z"/><path d="M8 9l2 2 4-4M8 15h8"/>', 'Your SOP and training', 'Rules &amp; skills', 'Hard rules, plus step-by-step recipes', 'It does the job its own way.'),
    ('<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>', 'A supervisor', 'Permission &amp; approval', 'What it may touch, and who says yes', 'Nobody checks before stock or money moves.'),
    ('<path d="M9 3h6v3H9z"/><path d="M7 5H5v16h14V5h-2"/><path d="M9 13l2 2 4-4"/>', 'Probation', 'Testing &amp; review', 'Tried on past orders first, then watched', 'The same mistake repeats quietly.'),
]
def _hire():
    out = ''
    for i, (p, a, b, w, c) in enumerate(HIRE):
        out += ('<div class="hr r" style="--d:%.2fs"><div class="ca"><span class="ic">%s</span>%s</div><i>%s</i><div class="cb"><b>%s</b><span>%s</span></div><div class="cc">%s<span>%s</span></div></div>'
                % (0.5 + i * .15, ic(p, 30), a, ic('<path d="M4 12h16M14 6l6 6-6 6"/>', 28, 2.4), b, w, ic('<path d="M6 6l12 12M18 6L6 18"/>', 20, 3), c))
    return out


# ---------------- slide: harness and loop engineering ----------------
RING = ['Tools', 'Memory', 'Rules', 'Permission', 'The loop', 'Tests']
LOOPENG = [('A clear goal and a stop rule', '&ldquo;Done = the Sales Order is drafted and sent for approval.&rdquo;'),
           ('Small, safe tools', '1 tool = 1 action. Tools that look come before tools that act.'),
           ('Check after every step', 'Read the result back. Did the stock really change?'),
           ('Ask a person at the right moment', 'Over the limit, an unclear item, anything with money: stop and ask.'),
           ('Log every step, handle errors', 'A tool fails? Retry once, then report. Never guess.')]
def _harness_svg():
    import math
    o = ('<svg class="hn" viewBox="0 0 640 600"><circle cx="320" cy="300" r="270" fill="rgba(0,165,122,.05)" stroke="rgba(0,165,122,.4)" stroke-width="2" stroke-dasharray="6 10"/>'
         '<circle cx="320" cy="300" r="185" fill="#fff" stroke="rgba(2,34,31,.12)" stroke-width="2"/>'
         '<circle class="core" cx="320" cy="300" r="92" fill="#02221F"/><text class="ct" x="320" y="296" text-anchor="middle">LLM</text><text class="cs" x="320" y="330" text-anchor="middle">the brain</text>'
         '<text class="ol" x="320" y="22" text-anchor="middle">THE HARNESS</text>')
    for k, t in enumerate(RING):
        a = math.radians(-90 + k * 60)
        x, y = 320 + 228 * math.cos(a), 300 + 228 * math.sin(a)
        o += ('<g class="rg" style="--d:%.2fs"><rect x="%d" y="%d" width="150" height="48" rx="24" fill="#E6F6EE" stroke="#00A57A" stroke-width="2"/>'
              '<text class="rl" x="%d" y="%d" text-anchor="middle">%s</text></g>' % (.6 + k * .15, x - 75, y - 24, x, y + 9, t))
    return o + '</svg>'

TOOL_RUN = [('<path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/>', 'Check stock', '42 bags'),
            ('<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4.5a1.5 1.5 0 010 3H10"/>', 'Check credit', 'Within limit'),
            ('<path d="M6 3h8l4 4v14H6z"/><path d="M9 13h6M9 17h4"/>', 'Create order', 'SO-00451'),
            ('<path d="M4 5h16v11H9l-5 4z"/>', 'Send WhatsApp', 'PDF sent')]
ERP_TOOLS = ['Check stock', 'Read an invoice', 'Create sales order', 'Draft purchase order', 'Record a payment', 'Send WhatsApp']
ERP_ROWS = [('sql', '<img src="../assets/sql-h.png" alt="SQL Account">', 'Customers, prices, invoices, money'),
            ('wms', '<b>WMS</b>', 'Every carton, in every bin'),
            ('mes', '<b>MES</b>', 'What the factory is making')]
def _run():
    return ''.join('<li class="r" style="--d:%.2fs"><span class="ic">%s</span><span class="tn">%s</span><span class="rs pop" style="--d:%.2fs">%s%s</span></li>'
                   % (1.5 + i * .45, ic(p, 26), t, 1.75 + i * .45, r, TICK) for i, (p, t, r) in enumerate(TOOL_RUN))


UFO_PATH = '<ellipse cx="12" cy="13" rx="10" ry="4"/><path d="M7 11.5a5 5 0 0110 0"/><path d="M8 19l-1 2M16 19l1 2M12 17v4"/>'
LAYERS = [  # top to bottom
    ('4', 'AI agents', 'Operates all 3 layers',
     'Reads every layer and does the work: takes orders, buys stock, chases payments, spots problems early. People approve.',
     'Runs the company', 'ai'),
    ('3', 'MES', 'Factory, in real time',
     'Plans each job, gives out materials by the BOM, records output, scrap and machine time as it happens. Every job&rsquo;s progress and true cost, live.',
     'Production you can see', 'mes'),
    ('2', 'WMS', 'Warehouse, in real time',
     'Every carton scanned in, put on the shelf, picked and shipped. Stock moves are recorded the moment they happen.',
     'Stock accurate', 'wms'),
    ('1', 'SQL Account', 'The foundation: accounting',
     'Keeps your accounts: invoices, payments, tax and reports. It records what has already happened.',
     'Accounts right', 'sql'),
]
def _layer_rows():
    out = ''
    for i, (n, name, role, line, badge, cls) in enumerate(LAYERS):
        d = 1.2 - i * 0.25          # build from the foundation up
        nm = '<img src="../assets/sql-h.png" alt="SQL Account">' if cls == 'sql' else '<b>' + name + '</b>'
        out += ('<div class="ly ' + cls + ' r" style="--d:' + '%.2f' % d + 's"><span class="no">' + n + '</span>'
                '<div class="nm">' + nm + '<span>' + role + '</span></div><p>' + line + '</p>'
                '<div class="bd">' + TICK + badge + '</div></div>')
    return out

# ---------------- slide: today, at a glance ----------------
AGENDA = [('<circle cx="12" cy="12" r="8"/><path d="M9 10h.01M15 10h.01M9 15c1.5 1.5 4.5 1.5 6 0"/>', 'What is an AI Agent?', 'How an LLM works, why AI Agents were invented, what they need'),
          ('<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>', 'Problems businesses face', '5 problems every office has, and what they cost you'),
          ('<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8M12 17v4"/>', 'SuDu AI', 'The system, then 6 AI Agents at work, live'),
          ('<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>', 'Workshop', 'Score your company and write your first AI job'),
          ('<path d="M9 3h6v3H9z"/><path d="M7 5H5v16h14V5h-2"/><path d="M9 13l2 2 4-4"/>', 'Get started', 'Where to start, what it saves you, and your next step')]
def _agenda():
    out = ''
    for k, (p, t, s_) in enumerate(AGENDA):
        out += ('<div class="ag" style="--d:%.2fs"><div class="dot"><i>%s</i></div><div class="tx"><small>PART %d</small><b>%s</b><span>%s</span></div></div>'
                % (.55 + k * .16, ic(p, 30), k + 1, t, s_))
    return out
slide('03-today', 'Today', SEC[0], 'light', 'data-sparks="none" style="--gx:85%;--gy:35%;--mx:85%;--my:35%"', '''
.slide { padding-top: 80px; }
.wrap { flex:1; display:grid; grid-template-columns: 640px 1fr; gap: 90px; min-height: 0; }
.lf { display:flex; flex-direction:column; }
.kicker { font-size: 22px; }
.h1 { font-size: 160px; line-height: 1; margin-top: 22px; letter-spacing: -.04em; }
.sub { font-size: 40px; font-weight: 650; color: var(--ink-2); margin-top: 26px; }
.sub em { font-style: normal; color: var(--green); }
.lf { justify-content: center; padding-bottom: 60px; }
.lead { font-size: 30px; line-height: 1.4; margin-top: 22px; }
.lead b { color: var(--ink); }
.tk { margin-top: auto; margin-bottom: 40px; padding: 26px 30px; border-radius: 26px; background: var(--ink); color: var(--on-dark); box-shadow: 0 30px 60px -36px rgba(2,34,31,.7); }
.tk h3 { font-size: 30px; font-weight: 800; letter-spacing: -.01em; }
.tk h3 em { font-style: normal; color: var(--neon); }
.tk ul { list-style:none; display:grid; gap: 14px; margin-top: 18px; }
.tk li { display:flex; gap: 16px; align-items:center; }
.tk li i { flex:none; width: 44px; height: 44px; border-radius: 12px; background: rgba(0,245,169,.14); color: var(--neon); display:grid; place-items:center; font-style: normal; font-weight: 800; font-size: 21px; }
.tk li b { display:block; font-size: 26px; font-weight: 750; }
.tk li span { display:block; font-size: 21px; color: var(--on-dark-2); }
.tl { position:relative; display:flex; flex-direction:column; justify-content:space-between; padding: 6px 0 46px; }
.tl .ln { position:absolute; left: 39px; top: 46px; bottom: 92px; width: 3px; background: rgba(2,34,31,.1); border-radius: 2px; overflow:hidden; }
.tl .ln::after { content:""; position:absolute; inset: 0; background: linear-gradient(180deg, var(--emerald), var(--neon)); transform-origin: top; animation: tlg 1.8s cubic-bezier(.65,0,.2,1) .4s both; }
@keyframes tlg { from { transform: scaleY(0); } }
.ag { position:relative; display:grid; grid-template-columns: 80px 1fr; gap: 28px; align-items:center; opacity: 0; animation: agin .7s cubic-bezier(.2,.8,.2,1) forwards; animation-delay: var(--d); }
@keyframes agin { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: none; } }
.ag .dot { width: 80px; height: 80px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 3px var(--emerald), 0 14px 26px -16px rgba(2,34,31,.5); display:grid; place-items:center; color: var(--green); position:relative; z-index:1; }
.ag .tx { padding: 18px 28px; border-radius: 22px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 18px 32px -26px rgba(2,34,31,.45); }
.ag small { font-family: var(--mono); font-size: 17px; font-weight: 700; letter-spacing: .14em; color: var(--green); }
.ag b { display:block; font-size: 38px; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; margin-top: 2px; }
.ag span { display:block; font-size: 25px; line-height: 1.35; color: var(--ink-2); margin-top: 4px; }
''', '''
<div class="wrap">
  <div class="lf">
    <div class="kicker r" style="--d:.05s">Hire Your First AI Agent</div>
    <h1 class="h1 r" style="--d:.15s">Today</h1>
    <p class="sub r" style="--d:.3s">in <em>5</em> parts</p>
  </div>
  <div class="tl"><div class="ln"></div>''' + _agenda() + '''</div>
</div>
''',
"\"Here is what we cover today, in 5 parts.\n\nPart 1, what is an AI Agent: how an LLM really works, why people invented the AI Agent, and what it needs to work in a real company. Part 2, the problems businesses face: the 5 problems we see in almost every office, and what they cost you. You will work out your own company's cost. Part 3, SuDu AI: the system, and then 6 AI Agents doing real jobs live on the screen, sales, stock, buying, payments and finance. Part 4, the workshop: you score your own company, check if you need a WMS or MES, and write your first AI job. Part 5, get started: where your company should start, what it saves you, and your next step.\"\n\nNext: \"So what do you take home today?\"")

TK_GIFT = '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13"/><path d="M12 8C10.5 5 7 4.5 7 6.5S10 8 12 8zM12 8c1.5-3 5-3.5 5-1.5S14 8 12 8z"/>'
TK_BULB = '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 00-3.6 10.8c.7.5 1.1 1.3 1.1 2.2h5c0-.9.4-1.7 1.1-2.2A6 6 0 0012 3z"/>'
TK_ROUTE = '<circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="6" r="2.2"/><path d="M7 18h7a3.5 3.5 0 000-7h-4a3.5 3.5 0 010-7h7"/>'
def _tk_ic(p):
    return '<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg></span>'
slide('03-takeaways', 'What you take home', SEC[0], 'light', 'data-sparks="9,0 1,5" style="--gx:82%;--gy:28%;--mx:80%;--my:30%"', '''
.slide { padding-top: 96px; }
.top { display:flex; align-items:flex-end; justify-content:space-between; gap: 40px; }
.h1 { font-size: 120px; line-height: 1; letter-spacing: -.04em; margin-top: 18px; }
.sub { font-size: 42px; font-weight: 650; color: var(--ink-2); margin-top: 24px; }
.sub em { font-style: normal; color: var(--green); }
.top .av { width: 230px; height: 230px; flex: none; margin-bottom: -10px; }
.cards { flex:1; display:grid; grid-template-columns: repeat(3, 1fr); gap: 34px; margin-top: 56px; margin-bottom: 10px; }
.cd { position:relative; padding: 44px 44px 46px; border-radius: 34px; display:flex; flex-direction:column; overflow:hidden; }
.cd .n { font-family: var(--mono); font-size: 26px; font-weight: 700; letter-spacing: .1em; color: var(--green); }
.cd .ic { width: 112px; height: 112px; border-radius: 30px; display:grid; place-items:center; background: var(--mint); color: var(--green); margin-top: 30px; }
.cd .ic svg { width: 58px; height: 58px; }
.cd b { display:block; font-size: 54px; font-weight: 750; letter-spacing: -.025em; line-height: 1.18; margin-top: auto; text-wrap: balance; }
.cd .big { position:absolute; right: 26px; top: -18px; font-size: 260px; font-weight: 800; letter-spacing: -.06em; line-height: 1; color: rgba(2,34,31,.045); pointer-events:none; }
/* the gift: dark card, neon accent */
.cd.hi { background: var(--ink); color: var(--on-dark); box-shadow: 0 40px 80px -40px rgba(2,34,31,.7); }
.cd.hi .n { color: var(--neon); }
.cd.hi .ic { background: rgba(0,245,169,.14); color: var(--neon); }
.cd.hi .big { color: rgba(0,245,169,.08); }
.cd.hi b em { font-style: normal; color: var(--neon); }
.cd.hi b em:lang(en) { margin-left: .25em; }
.cd.hi .tag { position:absolute; right: 36px; top: 40px; font-size: 24px; font-weight: 800; letter-spacing: .04em; padding: 8px 18px; border-radius: 999px; background: var(--neon); color: var(--ink); }
''', '''
<div class="top">
  <div>
    <div class="kicker r" style="--d:.05s">Hire Your First AI Agent</div>
    <h1 class="h1 r" style="--d:.15s">What you take home</h1>
    <p class="sub r" style="--d:.3s">Leave with <em>3</em> things</p>
  </div>
  <img class="av pop" style="--d:.45s" src="../assets/av/agent-thumbs.svg" alt="The SuDu agent giving a thumbs up">
</div>
<div class="cards">
  <div class="glass cd r" style="--d:.6s"><span class="big">1</span><span class="n">01</span>
    ''' + _tk_ic(TK_BULB) + '''
    <b>A clear picture of AI</b></div>
  <div class="glass cd r" style="--d:.8s"><span class="big">2</span><span class="n">02</span>
    ''' + _tk_ic(TK_ROUTE) + '''
    <b>Know how to plan<br>AI for your business</b></div>
  <div class="cd hi r" style="--d:1s"><span class="big">3</span><span class="n">03</span>
    ''' + _tk_ic(TK_GIFT) + '''
    <b>Get a<em>free</em><br>Demo AI Account</b></div>
</div>
''', "\"By the end of today, you take home 3 things.\n\nOne: a clear picture of AI. What AI really is, how an AI Agent works, what it can and cannot do, with no tech talk.\n\nTwo: you know how to plan AI for your business. Where your company should start, and which job is best to hand to AI first.\n\nThree: a free Demo AI Account. Go back and try it yourself: watch AI Agents work on sample data.\"\n\nNext: \"But first, be honest: who is really the boss of your company?\"")

# ---------------- SuDu WMS: 3 slides between "No tools, no work" and the WMS video ----------------
# From the SuDu WMS workflow chart: flow 1 reorder, 2 approval, 3 goods in, 4 goods out, 5 stock count, 6 item assembly.
# Each node pops in along its flow, the arrows draw, a neon dot runs each arrow. wms-supply and wms-stock have 1 extra Next press.
WMS_CSS = '''
/* ---- SuDu WMS flow slides: nodes pop in along the flow, arrows draw, a neon dot runs each arrow ---- */
.slide { padding-top: 84px; }
.mt { font-size: 70px; } .ml { font-size: 30px; margin-top: 16px; } .ml b { white-space: nowrap; }
.wf { display:flex; flex-direction:column; gap: 84px; margin-top: 92px; }
.wr { display:grid; grid-template-columns: 190px 1fr; gap: 28px; align-items:center; }
.wl b { display:block; font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--green); }
.wl span { display:block; font-size: 32px; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; margin-top: 6px; }
.wc { display:flex; align-items:stretch; }
.wn { position:relative; flex: 1 1 0; min-width: 0; min-height: 200px; display:flex; flex-direction:column; justify-content:center; padding: 36px 24px 22px; border-radius: 24px; background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 30px 50px -36px rgba(2,34,31,.5); border-bottom: 6px solid var(--emerald); }
.wn > b { font-size: 32px; font-weight: 780; letter-spacing: -.02em; line-height: 1.12; }
.wn .wt { font-size: 23px; line-height: 1.32; color: var(--ink-3); margin-top: 8px; }
.wn small { display:block; font-family: var(--mono); font-size: 17px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); margin: 4px 0; }
.wn.warn { background: #FFF5EF; border-bottom-color: #E0662E; }
.wn.ai { background: var(--ink); color: var(--on-dark); border-bottom-color: var(--neon); }
.wn.ai .wt { color: var(--on-dark-2); }
.wn.ai::after { content:""; position:absolute; inset: -7px; border-radius: 31px; border: 3px solid var(--neon); opacity: 0; pointer-events:none; animation: wGlow 2.4s ease-in-out infinite; animation-delay: calc(var(--d, 0s) + 1s); }
@keyframes wGlow { 0%, 100% { opacity: 0; transform: scale(.98); } 50% { opacity: .9; transform: none; } }
.wn.end { background: var(--mint); border-bottom-color: var(--green); }
.wb { position:absolute; left: 18px; top: -19px; display:inline-flex; align-items:center; gap: 8px; height: 38px; padding: 0 16px 0 10px; border-radius: 999px; font-size: 18px; font-weight: 750; white-space: nowrap;
  box-shadow: 0 10px 20px -12px rgba(2,34,31,.5); animation: wPop .55s var(--spring) both; animation-delay: calc(var(--d, 0s) + .35s); }
.wb svg { flex: none; }
.wb.ok { background: #D9F5E7; color: var(--green); } .wb.alert { background: #FFE1D6; color: #B4351A; } .wb.wait { background: #FFF0CC; color: #8A5A00; }
.wb.app, .wb.web { background: #E6ECFA; color: #2D4C93; }
.wb.auto { background: var(--ink); color: var(--neon); padding-left: 4px; }
.wn.ai .wb.auto { background: var(--neon); color: var(--ink); }
.wb img { width: 30px; height: 30px; border-radius: 50%; background: #fff; }
@keyframes wPop { from { opacity: 0; transform: scale(.5) translateY(8px); } to { opacity: 1; transform: none; } }
.wi { opacity: 0; transform: translateY(22px) scale(.96); animation: wIn .75s var(--spring) forwards; animation-delay: var(--d, 0s); }
@keyframes wIn { to { opacity: 1; transform: none; } }
.wa { position:relative; flex: 0 0 62px; align-self: center; height: 20px; }
.wa::before { content:""; position:absolute; left: 6px; right: 12px; top: 8px; height: 4px; border-radius: 2px; background: var(--emerald); transform-origin: left; transform: scaleX(0); animation: mGrow .45s ease forwards; animation-delay: var(--d, 0s); }
.wa::after { content:""; position:absolute; right: 2px; top: 1px; border-left: 14px solid var(--emerald); border-top: 9px solid transparent; border-bottom: 9px solid transparent; opacity: 0; animation: mFade .25s ease forwards; animation-delay: calc(var(--d, 0s) + .35s); }
.wa s { position:absolute; left: 4px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 10px 2px rgba(0,245,169,.8); opacity: 0; animation: wDot 1.5s linear infinite; animation-delay: calc(var(--d, 0s) + .7s); }
@keyframes wDot { 0% { opacity: 0; transform: translateX(0); } 20%, 75% { opacity: 1; } 100% { opacity: 0; transform: translateX(38px); } }
.p0, .p1 { flex:1; display:flex; flex-direction:column; }
.p1 { display:none; } body[data-s="1"] .p0 { display:none; } body[data-s="1"] .p1 { display:flex; }
.nx { margin-top: auto; align-self: flex-end; display:flex; align-items:center; gap: 14px; font-size: 24px; font-weight: 700; color: var(--green); }
.nx i { display:grid; place-items:center; width: 44px; height: 44px; border-radius: 50%; background: var(--ink); color: var(--neon); }
html.static .wi, html.static .wb { opacity: 1; transform: none; animation: none; }
html.static .wa::before { transform: none; animation: none; } html.static .wa::after { opacity: 1; animation: none; }
html.static .wa s, html.static .wn.ai::after { display: none; }
'''

slide('24-wms-intro', 'SuDu WMS: what it does', SEC[3], 'light', 'data-sparks="none"', MIN_CSS + WMS_CSS + '''
.mt, .ml { max-width: 1260px; }
.mt { font-size: 62px; }
.hero { position:absolute; right: 128px; top: 64px; width: 240px; height: 240px; }
.pz { display:flex; align-items:stretch; margin-top: 54px; }
.pz .wa { flex-basis: 72px; }
.pc { flex: 1 1 0; min-width: 0; display:flex; flex-direction:column; padding: 30px 34px 28px; border-radius: 30px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); }
.pc .hd { display:flex; align-items:center; justify-content:space-between; }
.pc .ico { width: 84px; height: 84px; border-radius: 50%; display:grid; place-items:center; background: var(--mint); color: var(--green); }
.pc .no { font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .1em; color: var(--ink-3); }
.pc h3 { font-size: 36px; font-weight: 800; letter-spacing: -.025em; line-height: 1.1; margin-top: 20px; }
.pc p { font-size: 24px; line-height: 1.42; color: var(--ink-2); margin-top: 12px; }
.pc .ch { display:flex; flex-wrap:wrap; gap: 10px; margin-top: auto; padding-top: 20px; }
.pc .ch span { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .05em; padding: 7px 12px; border-radius: 999px; background: var(--mint); color: var(--green); }
.usp { display:grid; grid-template-columns: auto repeat(4, 1fr); align-items:center; gap: 26px; margin-top: auto; padding: 24px 32px; border-radius: 26px; background: var(--ink); color: var(--on-dark); }
.usp > b { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--neon); }
.usp div { display:flex; align-items:center; gap: 12px; font-size: 23px; font-weight: 650; line-height: 1.25; }
.usp div i { flex:none; display:grid; place-items:center; width: 36px; height: 36px; border-radius: 50%; background: rgba(0,245,169,.15); color: var(--neon); }
''', '''
<div class="mk u" style="--d:.05s">SuDu WMS</div>
<h1 class="mt u" style="--d:.2s">AI Agent with <em>SuDu AI&rsquo;s warehouse system</em></h1>
<p class="ml u" style="--d:.4s">An AI Agent is only as good as the system it works in. For buying, stock and making, that system is <b>SuDu WMS</b>, linked straight to SQL Account.</p>
<img class="hero av u" style="--d:.5s" src="../assets/av/agent-thumbs.svg" alt="">
<div class="pz"><div class="pc wi" style="--d:0.60s"><div class="hd"><i class="ico"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="12" height="10" rx="1"/><path d="M14 10h4l3 3v4h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg></i><span class="no">01</span></div><h3>Supply chain management</h3><p>Stock runs low, the AI raises the Purchase Request, you approve, and the PO goes to the supplier.</p><div class="ch"><span>Flow 1 &middot; Reorder</span><span>Flow 2 &middot; Approval</span></div></div><i class="wa" style="--d:0.80s"><s></s></i><div class="pc wi" style="--d:1.00s"><div class="hd"><i class="ico"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/></svg></i><span class="no">02</span></div><h3>Inventory management</h3><p>Receive, put away, pick, pack and count. Every move is scanned on the mobile app, and every batch is tracked.</p><div class="ch"><span>Flow 3 &middot; Goods in</span><span>Flow 4 &middot; Goods out</span><span>Flow 5 &middot; Stock Count</span></div></div><i class="wa" style="--d:1.20s"><s></s></i><div class="pc wi" style="--d:1.40s"><div class="hd"><i class="ico"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20V10l5 3V10l5 3V10l5 3V5h3v15z"/></svg></i><span class="no">03</span></div><h3>Basic production management</h3><p>Build finished goods from a BOM with many versions and layers. Materials go out, finished goods come in.</p><div class="ch"><span>Flow 6 &middot; Item assembly</span></div></div></div>
<div class="usp u" style="--d:1.90s"><b>Why SuDu WMS</b><div><i><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg></i>AI creates the documents</div><div><i><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg></i>Staff work on the mobile app</div><div><i><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg></i>Every batch tracked</div><div><i><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg></i>Posts straight to SQL Account</div></div>
''',
"\"So an AI Agent needs a proper system with real buttons. In the warehouse, that system is SuDu WMS. It covers 3 jobs.\n\nOne, supply chain: when stock runs low, the AI raises the Purchase Request, you approve, and the PO goes to the supplier.\n\nTwo, inventory: goods in, goods out and the stock count, all scanned on the mobile app, with every batch tracked.\n\nThree, basic production: build finished goods from a BOM, and the stock updates itself.\n\nAnd everything posts straight to SQL Account, so the accounts always match the warehouse.\"\n\nNext: \"Let me walk you through each flow, starting with buying.\"")

slide('24-wms-supply', 'SuDu WMS: supply chain and production', SEC[3], 'light', 'data-sparks="none"', MIN_CSS + WMS_CSS, '''
<div class="p0">
<div class="mk u" style="--d:.05s">SuDu WMS &middot; Supply chain management</div>
<h1 class="mt u" style="--d:.2s">Stock runs low? <em>AI buys it for you</em></h1>
<p class="ml u" style="--d:.4s">From the Sales Order to the supplier, nobody keys in anything twice.</p>
<div class="wf"><div class="wr"><div class="wl wi" style="--d:0.70s"><b>Flow 1</b><span>Reorder</span></div><div class="wc"><div class="wn  wi" style="--d:0.95s"><span class="wb ok"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Completed</span><b>Sales Order issued</b><span class="wt">Customer order confirmed</span></div><i class="wa" style="--d:1.09s"><s></s></i><div class="wn warn wi" style="--d:1.31s"><span class="wb alert"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17h.01"/></svg>Alert</span><b>Stock not enough</b><span class="wt">Balance is below the order</span></div><i class="wa" style="--d:1.45s"><s></s></i><div class="wn ai wi" style="--d:1.67s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">AI auto-creates</span><b>Purchase Request</b><span class="wt">Raised for the shortfall</span></div></div></div><div class="wr"><div class="wl wi" style="--d:2.13s"><b>Flow 2</b><span>Approval</span></div><div class="wc"><div class="wn  wi" style="--d:2.38s"><span class="wb wait"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12M6 21h12M7 3v3l5 6 5-6V3M7 21v-3l5-6 5 6v3"/></svg>Pending approval</span><b>Needs approval</b><span class="wt">Waits for the boss</span></div><i class="wa" style="--d:2.52s"><s></s></i><div class="wn  wi" style="--d:2.74s"><span class="wb ok"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Completed</span><b>Approved</b><span class="wt">1 tap on the phone</span></div><i class="wa" style="--d:2.88s"><s></s></i><div class="wn  wi" style="--d:3.10s"><b>Converted to PO</b><span class="wt">No retyping</span></div><i class="wa" style="--d:3.24s"><s></s></i><div class="wn ai wi" style="--d:3.46s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">AI auto-sends</span><b>Sent to supplier</b><span class="wt">Sent automatically</span></div></div></div></div>
</div>
<div class="p1">
<div class="mk u" style="--d:.05s">SuDu WMS &middot; Basic production management</div>
<h1 class="mt u" style="--d:.2s">Make it, and the stock <em>updates itself</em></h1>
<p class="ml u" style="--d:.4s">Build finished goods from a BOM. Materials go out, finished goods come in, each with a batch number.</p>
<div class="wf"><div class="wr"><div class="wl wi" style="--d:0.70s"><b>Flow 6</b><span>Item assembly</span></div><div class="wc"><div class="wn  wi" style="--d:0.95s"><b>Item Assembly</b><span class="wt">Start the job</span></div><i class="wa" style="--d:1.09s"><s></s></i><div class="wn  wi" style="--d:1.31s"><b>Make to stock</b><small>or</small><b>Make to order</b></div><i class="wa" style="--d:1.45s"><s></s></i><div class="wn  wi" style="--d:1.67s"><b>BOM</b><span class="wt">Multiple versions, multiple layers</span></div></div></div><div class="wr"><div class="wl wi" style="--d:2.13s"><b>Done</b><span>Stock updates</span></div><div class="wc"><div class="wn  wi" style="--d:2.38s"><span class="wb ok"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Item assembly completed</span><b>&minus;Materials, +Finished good</b><span class="wt">Used as per the BOM</span></div><i class="wa" style="--d:2.52s"><s></s></i><div class="wn ai wi" style="--d:2.74s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">AI auto-generates</span><b>+Finished good batch</b><span class="wt">Batch number for tracking</span></div><i class="wa" style="--d:2.88s"><s></s></i><div class="wn end wi" style="--d:3.10s"><b>+Item balance</b><span class="wt">Stock is right at once</span></div></div></div></div>
</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Flow 1, reorder. A Sales Order is issued. The WMS checks the balance and sees the stock is not enough, so it raises an alert, and the AI creates the Purchase Request by itself.\n\nFlow 2, approval. The request waits for you. You approve with 1 tap, it converts to a Purchase Order, and the AI sends it to the supplier. Nobody keys in anything twice.\"\n\n(Next) \"Now production. Flow 6, item assembly. Make to stock or make to order, from a BOM that can have many versions and many layers. When the assembly is done, the materials go out, the finished good comes in with its own batch number, and the item balance updates by itself.\"\n\nThis slide has 1 extra Next press: basic production.\nNext: \"And the stock itself: every carton in, every carton out.\"")

slide('24-wms-stock', 'SuDu WMS: inventory', SEC[3], 'light', 'data-sparks="none"', MIN_CSS + WMS_CSS, '''
<div class="p0">
<div class="mk u" style="--d:.05s">SuDu WMS &middot; Inventory management</div>
<h1 class="mt u" style="--d:.2s">Every carton in and out, <em>scanned</em></h1>
<p class="ml u" style="--d:.4s">Staff work on the mobile app. The item balance moves by itself.</p>
<div class="wf"><div class="wr"><div class="wl wi" style="--d:0.70s"><b>Flow 3</b><span>Goods in</span></div><div class="wc"><div class="wn  wi" style="--d:0.95s"><b>Receiving</b><span class="wt">Goods arrive from the supplier</span></div><i class="wa" style="--d:1.09s"><s></s></i><div class="wn  wi" style="--d:1.31s"><span class="wb ok"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Direct convert</span><b>Putaway</b><span class="wt">Straight onto the shelf</span></div><i class="wa" style="--d:1.45s"><s></s></i><div class="wn ai wi" style="--d:1.67s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">AI auto-generates</span><b>New Batch</b><span class="wt">Batch number created</span></div><i class="wa" style="--d:1.81s"><s></s></i><div class="wn end wi" style="--d:2.03s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">Auto add</span><b>+Item balance</b><span class="wt">Stock goes up</span></div></div></div><div class="wr"><div class="wl wi" style="--d:2.49s"><b>Flow 4</b><span>Goods out</span></div><div class="wc"><div class="wn  wi" style="--d:2.74s"><b>Delivery Order</b><span class="wt">Ready to deliver</span></div><i class="wa" style="--d:2.88s"><s></s></i><div class="wn  wi" style="--d:3.10s"><span class="wb app"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>Mobile app</span><b>Picking</b><span class="wt">Scan each item</span></div><i class="wa" style="--d:3.24s"><s></s></i><div class="wn  wi" style="--d:3.46s"><span class="wb app"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>Mobile app</span><b>Packing</b><span class="wt">Check and pack</span></div><i class="wa" style="--d:3.60s"><s></s></i><div class="wn end wi" style="--d:3.82s"><b>&minus;Item balance</b><span class="wt">Stock goes down</span></div></div></div></div>
</div>
<div class="p1">
<div class="mk u" style="--d:.05s">SuDu WMS &middot; Stock Count</div>
<h1 class="mt u" style="--d:.2s">A stock count you <em>can trust</em></h1>
<p class="ml u" style="--d:.4s">The office assigns, the floor counts on the app. A wrong count goes back for a recount. Only approved counts post to SQL Account.</p>
<div class="wf"><div class="wr"><div class="wl wi" style="--d:0.70s"><b>Flow 5</b><span>Count</span></div><div class="wc"><div class="wn  wi" style="--d:0.95s"><span class="wb web"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>Web</span><b>Create count task</b><span class="wt">Assigner, on the web</span></div><i class="wa" style="--d:1.09s"><s></s></i><div class="wn  wi" style="--d:1.31s"><span class="wb app"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>Mobile app</span><b>Count</b><span class="wt">Assignee, on the mobile app</span></div><i class="wa" style="--d:1.45s"><s></s></i><div class="wn warn wi" style="--d:1.67s"><span class="wb alert"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17h.01"/></svg>Reject alert</span><b>Review</b><span class="wt">Count looks wrong?</span></div><i class="wa" style="--d:1.81s"><s></s></i><div class="wn  wi" style="--d:2.03s"><span class="wb app"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>Mobile app</span><b>Recount</b><span class="wt">Assignee counts again</span></div></div></div><div class="wr"><div class="wl wi" style="--d:2.49s"><b>Then</b><span>Approve and post</span></div><div class="wc"><div class="wn  wi" style="--d:2.74s"><span class="wb ok"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Approved</span><b>Approve</b><span class="wt">Assigner, on the web</span></div><i class="wa" style="--d:2.88s"><s></s></i><div class="wn ai wi" style="--d:3.10s"><span class="wb auto"><img src="../assets/av/agent-hi.svg" alt="">AI auto-generates</span><b>Stock Adjustment</b><span class="wt">Made from the count</span></div><i class="wa" style="--d:3.24s"><s></s></i><div class="wn end wi" style="--d:3.46s"><b>Post to SQL Account</b><span class="wt">Accounts match the shelf</span></div></div></div></div>
<div class="nx u" style="--d:4.02s"><i><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M8 5l11 7-11 7z"/></svg></i>Next: see it in a real warehouse</div>
</div>
<script>
(function () {
  document.body.dataset.s = '0';
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') document.body.dataset.s = String(e.data.deckStep); });
})();
</script>
''',
"\"Flow 3, goods in. Receive the goods and put them away. The WMS creates the new batch and adds the item balance by itself.\n\nFlow 4, goods out. From the Delivery Order, staff pick and pack on the mobile app, and the balance goes down as they scan.\"\n\n(Next) \"Flow 5, stock count. The office creates the count task on the web. The floor counts on the mobile app. If a count looks wrong, the office rejects it and it goes back for a recount. Once it is approved, the AI generates the Stock Adjustment and posts it to SQL Account. So your accounts match the shelf.\"\n\nThis slide has 1 extra Next press: stock count.\nNext: \"Enough diagrams. Let me show you what that looks like in a real warehouse.\"")

# ---------------- video: SuDu WMS seminar preview (plays after "No tools, no work") ----------------
slide('24-video-wms', 'Video: SuDu WMS', SEC[3], 'dark bare', 'data-sparks="none"', '''
body { background: #000; }
.slide { padding: 0 !important; }
.vw { position:absolute; inset: 0; background: #000; }
.vw video { width: 100%; height: 100%; object-fit: contain; display:block; cursor: pointer; }
.src { position:absolute; left: 48px; bottom: 36px; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; color: rgba(242,251,247,.6); text-transform: uppercase; }
body .deck-foot, body .foot { display:none !important; }
''', '''
<div class="vw"><video id="v" src="../assets/video/wms-preview.mp4" playsinline preload="auto"></video></div>
<div class="src">Video: SuDu WMS &middot; seminar preview</div>
<script>
(function () {
  var v = document.getElementById('v');
  var STATIC = navigator.webdriver || location.hash === '#static';
  if (STATIC) { v.addEventListener('loadedmetadata', function () { v.currentTime = Math.min(20, v.duration / 4); }); return; }
  function go() { var p = v.play(); if (p && p.catch) p.catch(function () { v.muted = true; v.play(); }); }
  if (v.readyState >= 2) go(); else v.addEventListener('canplay', go, { once: true });
  v.addEventListener('click', function () { if (v.muted) { v.muted = false; return; } v.paused ? v.play() : v.pause(); });
})();
</script>
''',
"(The video plays: about 3 minutes, the SuDu WMS preview with subtitles. Let it run.)\n\n\"That is what tools look like in a real warehouse: every carton scanned, every bin known, every count matching the system.\"\n\nDo: click the video to pause or play. If it starts with no sound, click it once to turn the sound on.\nNext: \"Before the demo, the 2 questions I get asked the most.\"")

# ---------------- meme image (the user's own picture): the pool, AI Agent vs the admins ----------------
slide('12-meme-pool', 'Meme: who gets saved', SEC[3], 'light bare', 'data-sparks="none"', '''
body { background: #FFFFFF; }
.slide { padding: 0 !important; }
.mi { position:absolute; inset: 0; display:grid; place-items:center; background: #FFFFFF; }
.mi img { height: 100%; width: 100%; object-fit: contain; display:block; opacity: 0; transform: scale(.96); animation: mIn .8s cubic-bezier(.2,.75,.15,1) .1s forwards; }
@keyframes mIn { to { opacity: 1; transform: none; } }
html.static .mi img { opacity: 1; transform: none; animation: none; }
''', '''
<div class="mi"><img src="../assets/img/meme-pool.webp" alt="Meme: the boss saves the AI Agent while the admins sink"></div>
''',
"(This one is for a laugh. Let it land.)\n\n\"Be honest, admins in the room. The boss is busy playing with the new AI Agent. The admin preparing the report is drowning. And the admin keying in orders? Already at the bottom of the pool, since last year.\" (pause for the laugh)\n\n\"That is exactly why we built SuDu: so nobody in your company has to drown in reports and keying in again.\"\n\nNext: \"Enough talking. Let me show you.\"")

slide('12-why-sudu', 'Why SuDu if I have SQL Account', SEC[0], 'light', 'data-sparks="9,0" style="--gx:80%;--gy:30%;--mx:80%;--my:30%"', '''
.slide { padding-top: 84px; }
.h1 { font-size: 64px; max-width: 1500px; }
.lead { font-size: 30px; margin-top: 10px; }
.stk { position:relative; flex:1; display:grid; grid-template-rows: 1.15fr 1fr 1fr 1fr; gap: 12px; margin-top: 28px; margin-right: 150px; }
.ly { display:grid; grid-template-columns: 70px 330px 1fr 260px; align-items:center; gap: 22px; padding: 0 26px 0 18px; border-radius: 22px; background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 20px 40px -30px rgba(2,34,31,.35); }
.ly .no { width: 54px; height: 54px; border-radius: 16px; background: var(--mint); color: var(--green); display:grid; place-items:center; font-size: 28px; font-weight: 700; }
.ly .nm b { display:block; font-size: 40px; font-weight: 700; letter-spacing: -.02em; line-height: 1.05; }
.ly .nm img { height: 40px; display:block; }
.ly .nm span { display:block; font-size: 22px; font-weight: 600; color: var(--green); margin-top: 6px; }
.ly p { font-size: 24px; line-height: 1.32; color: var(--ink-2); }
.ly .bd { justify-self: end; display:flex; align-items:center; gap: 8px; white-space: nowrap; font-size: 21px; font-weight: 700; padding: 9px 13px; border-radius: 12px; background: var(--mint); color: var(--ink); }
.ly .bd svg { color: var(--green); flex:none; }
.ly.sql { background: linear-gradient(110deg, #F3EEFF, #EAF2FF); }
.ly.sql .no { background: rgba(124,92,255,.15); color: #5B43D6; }
.ly.ai { background: var(--ink); box-shadow: 0 0 60px rgba(0,245,169,.22); }
.ly.ai .no { background: var(--neon); color: var(--ink); }
.ly.ai .nm b { color: var(--on-dark); } .ly.ai .nm span { color: var(--neon); } .ly.ai p { color: var(--on-dark-2); }
.ly.ai .bd { background: var(--neon); }
.ly.ai .bd svg { color: var(--ink); }
.brk { position:absolute; right: -128px; top: calc(25% + 10px); bottom: 6px; width: 100px; }
.brk i { position:absolute; left: 0; top: 0; bottom: 0; width: 26px; border: 3px solid var(--emerald); border-left: 0; border-radius: 0 16px 16px 0; }
.brk span { position:absolute; left: 40px; top: 50%; transform: translateY(-50%); writing-mode: vertical-rl; white-space: nowrap; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .12em; color: var(--green); }
.end { margin-top: 22px; font-size: 32px; font-weight: 600; }
.end span { color: var(--ink-3); font-weight: 500; }
.end .sig { color: var(--ink); font-weight: 600; }
/* 2-stage reveal: big title first, then the content */
.ttlw { display:inline-block; align-self:flex-start; transform-origin: 0 0; transition: transform 1.05s cubic-bezier(.65,0,.15,1); will-change: transform; }
.rest { flex:1; display:flex; flex-direction:column; min-height: 0; transition: opacity .6s ease .8s, transform .8s cubic-bezier(.2,.8,.2,1) .75s; }
body[data-s="0"] .rest { opacity: 0; transform: translateY(40px); pointer-events: none; transition: opacity .35s ease, transform .5s ease; }
''', '''
<div class="ttlw"><div class="kicker r" style="--d:0s">FAQ 1</div><h1 class="h1 r" style="--d:.05s">&ldquo;I already have SQL Account.<br>Why do I still need SuDu AI?&rdquo;</h1></div>
<div class="rest">
<p class="lead r" style="--d:.2s">Because accounting is only the first layer of a company.</p>
<div class="stk">''' + _layer_rows() + '''<div class="brk f" style="--d:1.6s"><i></i><span>AI OPERATES ALL 3 LAYERS</span></div></div>
<p class="end r" style="--d:1.7s">SQL Account tells you what <span class="sig" style="--sd:2.3s">already happened.</span> <span>SuDu runs what happens next.</span></p>
</div>
<script>
(function () {
  var B = document.body, w = document.querySelector('.ttlw'), rest = document.querySelector('.rest');
  var STATIC = navigator.webdriver || location.hash === '#static', big = 'none';
  function measure() {                       // where the title sits normally -> big and centred
    var prev = w.style.transform; w.style.transition = 'none'; w.style.transform = 'none';
    var sl = document.querySelector('.slide').getBoundingClientRect(), k = sl.width / 1920, r = w.getBoundingClientRect();
    var x = (r.left - sl.left) / k, y = (r.top - sl.top) / k, wd = r.width / k, ht = r.height / k, sc = Math.min(2.2, 1720 / wd);
    big = 'translate(' + (960 - x - sc * wd / 2) + 'px,' + (520 - y - sc * ht / 2) + 'px) scale(' + sc + ')';
    w.style.transform = prev; void w.offsetWidth; w.style.transition = '';
  }
  function replay() { rest.querySelectorAll('.r,.f,.pop,.sig,.draw').forEach(function (el) { el.style.animation = 'none'; void el.offsetWidth; el.style.animation = ''; }); }
  function set(n, instant) {
    if (instant) w.style.transition = 'none';
    if (n >= 1) { if (B.dataset.s !== '1') { B.dataset.s = '1'; w.style.transform = 'none'; rest.querySelectorAll('.r,.f,.pop,.sig,.draw').forEach(function (el) { el.style.animation = 'none'; }); setTimeout(replay, instant ? 0 : 750); } }
    else { B.dataset.s = '0'; w.style.transform = big; }
    if (instant) { void w.offsetWidth; w.style.transition = ''; }
  }
  if (STATIC) { B.dataset.s = '1'; return; }
  B.dataset.s = '0'; measure(); set(0, true);
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () { if (B.dataset.s === '0') { measure(); set(0, true); } });
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
  if (window.parent === window) addEventListener('keydown', function (e) { if (e.key === 'ArrowRight' || e.key === ' ') set(1); if (e.key === 'ArrowLeft') set(0); });
})();
</script>
''',
"\"(The question fills the screen. Let it sit.) Here is the question I hear most: I already have SQL Account, why do I need SuDu?\" (Next: the answer appears.) \"Good question, because SQL Account is excellent. Think of your company in layers.\n\nLayer one, the foundation, is accounting. SQL Account keeps your accounts: invoices, payments, tax, reports. But notice: it records what has already happened.\n\nLayer two is the warehouse. A warehouse system runs the floor: every carton is scanned when it arrives, goes on a shelf, is picked and is shipped. The stock moves are recorded the moment they happen, so your stock figure is real and accurate.\n\nLayer three, if you manufacture, is the factory: MES, a manufacturing execution system. It plans each job, issues materials against the BOM, and records output, scrap and machine time as they happen. So at any moment you can see where every job is, whether it is late, and what it really cost. No more waiting for the paper logsheet tomorrow. You can see every job.\n\nAnd layer four sits on top: the AI agents. They read all three layers and do the work: take orders, buy stock, chase payments, spot problems early, and people approve. SQL Account tells you what already happened. SuDu runs what happens next.\"\n\nNext: \"So can I just connect ChatGPT or Claude to SQL Account myself? Here is a question I get every week.\"")

def danger(icon, t, s, d):
    return '<div class="glass dg r" style="--d:%s"><div class="i">%s</div><h3>%s</h3><p>%s</p></div>' % (d, ic(icon, 44), t, s)
DANGERS = [
    (KEY, 'No access control', 'It can read every figure and change any of them. Nothing asks you first.',
     'Like giving a new temp the master key and the company chop on day 1.'),
    (SNOW, 'It can freeze the server', '1 heavy question, like &ldquo;every sale for 5 years&rdquo;, can lock the database.',
     'Nobody in the office can issue an invoice until it recovers.'),
    (TANGLE, 'It messes up your accounts', 'Writing straight into the database skips SQL Account&rsquo;s own checks.',
     'Running numbers, stock and accounts stop matching.'),
]
def _dangers():
    out = ''
    for i, (icn, t, line, eg) in enumerate(DANGERS):
        out += ('<div class="dg r" style="--d:%.2fs"><div class="hd"><span class="i">%s</span><span class="n">%d</span></div><h3>%s</h3><p>%s</p><p class="eg">%s</p></div>'
                % (0.9 + i * .18, ic(icn, 40), i + 1, t, line, eg))
    return out
SAFE = ['Permission for every user', 'A person approves before it is saved', 'Every action logged', 'SQL Account&rsquo;s own rules kept']

PLUG_COLS = [('diy', 'Do it yourself', 'Claude wired straight into the database'),
             ('con', 'A connector', 'An SQL Account plug-in + Claude or ChatGPT'),
             ('sudu', 'SuDu AI', 'AI staff on a full ERP')]
PLUG_ROWS = [  # label, diy, connector, sudu ; each (ok?, text) ok: 1 good, 0 neutral, -1 bad
    ('Who does the work', (-1, 'You, when you ask it'), (0, 'Mostly when you ask, plus a daily briefing'), (1, 'It works on its own, every day')),
    ('Your accounts', (-1, 'Writes straight in, skips the checks'), (1, 'Uses SQL Account&rsquo;s own login'), (1, 'Keeps SQL Account&rsquo;s rules')),
    ('Approval and log', (-1, 'None'), (0, 'You approve each order'), (1, 'Approval queue, every action logged')),
    ('What it covers', (0, 'Accounting'), (0, 'Accounting only'), (1, 'Accounting, warehouse and factory')),
    ('Runs on', (-1, 'A programmer&rsquo;s laptop'), (-1, '1 office PC that must stay on'), (1, 'The cloud: web, mobile, WhatsApp')),
    ('What you pay', (-1, 'Programmer + AI subscription'), (-1, 'Licence + AI subscription + extra SQL Account user licences'), (1, '1 price. AI included.')),
]
PLUG_IC = {1: '<path d="M4 12.5l5 5L20 6.5"/>', 0: '<path d="M6 12h12"/>', -1: '<path d="M6 6l12 12M18 6L6 18"/>'}
def _plug_table():
    o = '<div class="pt"><div class="hc"></div>' + ''.join('<div class="hc %s u" style="--d:%.2fs"><b>%s</b><span>%s</span></div>' % (c, .35 + k * .12, t, s_) for k, (c, t, s_) in enumerate(PLUG_COLS))
    for r, (lab, *cells) in enumerate(PLUG_ROWS):
        d = .8 + r * .14
        o += '<div class="lb u" style="--d:%.2fs">%s</div>' % (d, lab)
        for (c, _, _), (v, t) in zip(PLUG_COLS, cells):
            o += '<div class="cl %s v%d u" style="--d:%.2fs"><i>%s</i><span>%s</span></div>' % (c, v, d, ic(PLUG_IC[v], 20, 3), t)
    return o + '</div>'

slide('13-plug-straight-in', 'Why not plug it straight in?', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.slide { padding-top: 76px; }
.mt { font-size: 60px; }
.pt { display:grid; grid-template-columns: 260px 1fr 1fr 1.12fr; margin-top: 26px; }
.hc { padding: 0 20px 14px; display:flex; flex-direction:column; justify-content:flex-end; }
.hc b { font-size: 32px; font-weight: 800; letter-spacing: -.02em; }
.hc span { font-size: 20px; color: var(--ink-3); margin-top: 2px; line-height: 1.3; }
.hc.sudu { background: var(--ink); border-radius: 22px 22px 0 0; padding-top: 18px; }
.hc.sudu b { color: var(--neon); } .hc.sudu span { color: var(--on-dark-2); }
.lb, .cl { padding: 13px 20px; border-top: 1px solid var(--line); display:flex; align-items:center; }
.lb { font-family: var(--mono); font-size: 17px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); }
.cl { gap: 12px; font-size: 24px; line-height: 1.28; color: var(--ink-2); }
.cl i { flex:none; display:grid; place-items:center; width: 32px; height: 32px; border-radius: 50%; }
.cl.v1 i { background: var(--mint); color: var(--green); }
.cl.v0 i { background: #ECEFEC; color: var(--ink-3); }
.cl.v-1 i { background: #FFE9DF; color: #B4451F; }
.cl.sudu { background: var(--ink); color: var(--on-dark); border-top-color: rgba(242,251,247,.12); font-weight: 600; }
.cl.sudu.v1 i { background: rgba(0,245,169,.16); color: var(--neon); }
.pt > .cl.sudu:last-child { border-radius: 0 0 22px 22px; }
.bt { margin-top: 26px; font-size: 32px; color: var(--ink-2); }
.bt b { color: var(--ink); } .bt em { font-style: normal; color: var(--green); font-weight: 750; }
''', '''
<div class="mk u" style="--d:.05s">FAQ 2</div>
<h1 class="mt u" style="--d:.15s">&ldquo;Can I just connect Claude to SQL Account?&rdquo; <em>3 ways, compared</em></h1>
''' + _plug_table() + '''
<p class="bt u" style="--d:1.8s"><b>Claude and ChatGPT are great brains.</b> With SuDu you get the brain, the ERP and the AI staff, <em>all in 1 price</em>.</p>
''',
"\"Every week someone asks me: can I just connect Claude or ChatGPT to my SQL Account? You can. There are 3 ways, so let's compare them honestly.\n\nWay 1: do it yourself. A programmer wires Claude straight into the database. It only works when you ask it. It writes straight into the tables and skips SQL Account's own checks, there is no approval and no log, and it lives on a programmer's laptop. You pay the programmer and the AI subscription.\n\nWay 2: a connector. A plug-in that lets Claude or ChatGPT talk to SQL Account. This is a proper product: it uses SQL Account's own login, and you approve orders. Apart from a daily briefing, it mostly works when someone asks it something. It covers accounting only, and it runs on 1 office PC that must stay switched on. And the costs add up: the licence, an AI subscription, and often extra SQL Account user licences, because every staff member needs their own SQL Account login.\n\nWay 3: SuDu AI. AI staff that work on their own every day: chasing payments, sending reports, taking orders. It keeps SQL Account's rules, everything waits in an approval queue and is logged. It covers accounting, warehouse and factory. It runs in the cloud, on web, mobile and WhatsApp. And it is 1 price, with the AI included.\n\nClaude and ChatGPT are great brains. With SuDu you get the brain, the ERP and the AI staff, all in 1 price.\"\n\nNote: keep it fair: do not name any connector product. Claude is made by Anthropic, ChatGPT by OpenAI.\nNext: \"Let me go 1 level deeper.\"")

# ---------------- FAQ 2b: under the hood (connector vs SuDu) ----------------
DEEP_ROWS = [  # icon, topic, connector, sudu, sudu tag
    ('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>', 'WhatsApp',
     'No groups. It knows a customer only if their phone matches SQL Account.', 'Reads group and private chats by itself, even from unsaved numbers. Matches customer and item nicknames.', ''),
    ('<path d="M6 3h8l4 4v14H6z"/><path d="M9 13h6M9 17h4"/>', 'Orders',
     'Staff key in orders 1 at a time. Customer self-service is a paid add-on.', 'Customer orders on WhatsApp turn into Sales Order drafts. You just approve.', ''),
    ('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 'Follow-up',
     'A scheduled message fires once and is done. No waiting for replies.', 'Tasks that run for days: send, wait for the reply, follow up, stop when paid.', ''),
    ('<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16"/>', 'Memory',
     'Reads SQL Account live for each question.', 'A memory layer: every customer&rsquo;s history, habits and past chats, across millions of records.', ''),
    ('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>', 'If it goes down',
     '1 Windows PC, always on. Everything on 1 disk: no backup, nobody alerted.', 'The cloud: monitored, with alerts. Big questions run on SuDu&rsquo;s data platform, not your SQL Account server.', ''),
    ('<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>', 'Setup &amp; access',
     'On-site IT. No mobile app; admin page only on that PC. Licence tied to 1 PC.', 'Sign in on web or mobile. Several companies in 1 account.', ''),
]
slide('13-plug-deep', 'Under the hood: connector vs SuDu', SEC[2], 'light', 'data-sparks="none"', MIN_CSS + '''
.slide { padding-top: 76px; }
.mt { font-size: 62px; }
.dp { display:grid; grid-template-columns: 290px 1fr 1.25fr; margin-top: 18px; }
.dh { padding: 0 22px 12px; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .12em; color: var(--ink-3); display:flex; align-items:flex-end; }
.dh.s { background: var(--ink); color: var(--neon); border-radius: 22px 22px 0 0; padding-top: 16px; }
.tp, .cn, .su { padding: 11px 22px; border-top: 1px solid var(--line); display:flex; align-items:center; }
.tp { gap: 14px; font-size: 27px; font-weight: 800; letter-spacing: -.01em; }
.tp i { flex:none; display:grid; place-items:center; width: 44px; height: 44px; border-radius: 14px; background: var(--mint); color: var(--green); }
.cn { font-size: 22px; line-height: 1.3; color: var(--ink-3); }
.su { background: var(--ink); color: var(--on-dark); font-size: 22px; line-height: 1.3; font-weight: 600; border-top-color: rgba(242,251,247,.12); flex-wrap: wrap; gap: 8px 12px; }
.su em { font-style: normal; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; padding: 4px 10px; border-radius: 999px; border: 1.5px solid #FFB547; color: #FFB547; }
.dp > .su:last-child { border-radius: 0 0 22px 22px; }
.fb { margin-top: 18px; display:flex; align-items:center; gap: 22px; padding: 18px 26px; border-radius: 20px; background: #FFF6E8; box-shadow: inset 0 0 0 2px rgba(255,181,71,.5); }
.fb i { flex:none; display:grid; place-items:center; width: 54px; height: 54px; border-radius: 50%; background: #FFB547; color: var(--ink); }
.fb p { font-size: 24px; line-height: 1.38; color: var(--ink); }
.fb b { color: #8A3417; }
''', '''
<div class="mk u" style="--d:.05s">FAQ 2 &middot; Under the hood</div>
<h1 class="mt u" style="--d:.15s">Chatting with your data vs <em>running your company</em></h1>
<div class="dp">
  <div class="dh u" style="--d:.3s"></div><div class="dh u" style="--d:.35s">A connector + Claude or ChatGPT</div><div class="dh s u" style="--d:.4s">SuDu AI</div>
  ''' + ''.join('<div class="tp u" style="--d:%.2fs"><i>%s</i>%s</div><div class="cn u" style="--d:%.2fs">%s</div><div class="su u" style="--d:%.2fs"><span>%s</span>%s</div>'
                % (.6 + k * .2, ic(p, 26, 2), t, .65 + k * .2, c, .7 + k * .2, s_, ('<em>%s</em>' % g) if g else '') for k, (p, t, c, s_, g) in enumerate(DEEP_ROWS)) + '''
</div>
<div class="fb u" style="--d:1.6s"><i>''' + ic('<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>', 28, 2.4) + '''</i>
  <p>SQL Account runs on a <b>Firebird</b> database, built for daily bookkeeping, not for an AI scanning years of data. <b>Heavy AI questions on it can clash with your staff&rsquo;s work.</b></p></div>
''',
"\"Let me go 1 level deeper, because this is where the difference really shows. A connector lets you chat with your data. SuDu runs your company. 6 things.\n\nWhatsApp. A connector cannot read WhatsApp groups, and it only knows a customer if their phone number matches the mobile in SQL Account. SuDu reads group and private chats by itself, even from numbers nobody saved, and it matches the nicknames customers use for items.\n\nOrders. With a connector, your staff still key in orders 1 at a time; customer self-service is a paid add-on. In SuDu, a customer's WhatsApp order becomes a Sales Order draft, and you just approve.\n\nFollow-up. A connector's scheduled message fires once and is done: it does not wait for the reply, and it does not stop when the customer pays. SuDu is rolling out tasks that run for days: send, wait, follow up, stop when paid.\n\nMemory. A connector reads SQL Account live for each question. SuDu has a memory layer: every customer's history, habits and past chats, across millions of records.\n\nIf it goes down. A connector lives on 1 Windows PC that must always be on. Everything sits on 1 disk: no backup, and nobody is alerted when it stops. SuDu runs in the cloud, monitored, with alerts. And SuDu is moving big questions onto its own data platform, so your SQL Account server, which runs on Firebird and is built for bookkeeping, stays fast for your staff.\n\nSetup. A connector needs on-site IT, there is no mobile app, the admin page only opens on that PC, and the licence is tied to that PC. SuDu: sign in on web or mobile, and run several companies in 1 account.\"\n\nNote: the data platform and multi-day tasks are rolling out; say \"is moving\" / \"is rolling out\", not \"already\". Keep it fair: no connector product is named.\nNext: \"So AI needs something underneath it.\"")


HOUSE = [  # top to bottom: n, part, title, what, without, check, marker (x, y), delay
    ('4', 'ROOF', 'AI Agents', 'Do the daily work: orders, stock, payments, reports.',
     'People keep typing and chasing by hand.', 'Which job eats the most hours each week?', (623, 300), 3.3),
    ('3', 'WALLS', 'Permissions and approvals', 'Who may see what, do what, and say yes. Every action logged.',
     'The AI can change anything, and nobody knows who did what.', 'Is it written down who approves discounts, credit and purchases?', (730, 450), 2.4),
    ('2', 'DOOR', 'A safe connection', 'The AI goes through a controlled door that keeps your accounting rules.',
     '1 wrong command can freeze the server or break your accounts.', 'Does any tool write straight into your SQL database?', (475, 590), 1.8),
    ('1', 'FOUNDATION', 'Clean data', '1 code per item, fixed units, and stock that matches the shelf (WMS + MES).',
     'It quotes the wrong price and promises stock you don&rsquo;t have.', 'When you count, does the system match the shelf?', (800, 740), 1.0),
]
def _house_rows():
    out = ''
    for n, part, t, what, wo, ck, _xy, d in HOUSE:
        out += ('<div class="lv r" style="--d:%.2fs"><div class="h"><i>%s</i><small>%s</small><b>%s</b></div><p>%s</p>'
                '<div class="ln no">%s<span><em>Without it:</em> %s</span></div><div class="ln ck">%s<span><em>Check:</em> %s</span></div></div>'
                % (d + .2, n, part, t, what, ic('<path d="M6 6l12 12M18 6L6 18"/>', 18, 3), wo, ic('<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 114 2c-1 .6-1.5 1-1.5 2M12 17h.01"/>', 20, 2.2), ck))
    return out
def _house_marks():
    return ''.join('<g class="pop" style="--d:%.2fs"><circle cx="%d" cy="%d" r="26" fill="#00F5A9" stroke="#02221F" stroke-width="4"/><text x="%d" y="%d" class="mk">%s</text></g>'
                   % (d, x, y, x, y + 11, n) for n, _p, _t, _w, _o, _c, (x, y), d in HOUSE)

slide('14-the-house', 'What AI needs underneath', SEC[2], 'light', 'data-sparks="none" style="--gx:22%;--gy:70%;--mx:22%;--my:60%"', '''
.slide { padding-top: 80px; }
.h1 { font-size: 64px; }
.lead { font-size: 28px; margin-top: 8px; }
.lead b { color: var(--ink); }
.wrap { flex:1; display:grid; grid-template-columns: 640px 1fr; gap: 40px; margin-top: 12px; min-height: 0; }
.hs { position:relative; }
.hs svg { width: 640px; height: auto; overflow: visible; }
.hs .av { position:absolute; left: 245px; top: -18px; width: 140px; height: 140px; }
.mk { font: 800 28px var(--sans, Figtree); fill: #02221F; stroke: none; text-anchor: middle; }
.fill1 { fill: rgba(0,245,169,.18); } .fill2 { fill: rgba(255,255,255,.75); }
.lvs { display:grid; gap: 10px; align-content:start; }
.lv { padding: 12px 20px; border-radius: 18px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 14px 24px -22px rgba(2,34,31,.4); }
.lv .h { display:flex; align-items:center; gap: 12px; }
.lv .h i { font-style: normal; display:grid; place-items:center; width: 38px; height: 38px; border-radius: 50%; background: #00F5A9; color: var(--ink); font-size: 20px; font-weight: 800; box-shadow: 0 0 0 3px var(--ink); }
.lv .h small { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .12em; color: var(--green); }
.lv .h b { font-size: 29px; font-weight: 800; letter-spacing: -.01em; }
.lv p { font-size: 22px; color: var(--ink-2); line-height: 1.3; margin-top: 4px; }
.lv .ln { display:flex; gap: 8px; align-items:flex-start; font-size: 20px; line-height: 1.3; margin-top: 4px; }
.lv .ln svg { flex:none; margin-top: 3px; }
.lv .ln em { font-style: normal; font-weight: 700; }
.lv .no { color: #8A3417; } .lv .no svg { color: #B4451F; }
.lv .ck { color: var(--green); } .lv .ck svg { color: var(--emerald); }
''', '''
<h1 class="h1 r" style="--d:.05s">AI is like a house</h1>
<p class="lead r" style="--d:.2s">Most people only look at the roof. <b>AI on messy data only makes mistakes faster.</b> Build from the foundation up.</p>
<div class="wrap">
  <div class="hs">
  <svg viewBox="0 120 840 680" fill="none" stroke="#02221F" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
    <rect class="fill1 f" style="--d:1s" x="40" y="680" width="760" height="80" stroke="none"/>
    <path class="draw" pathLength="1" style="--d:.3s" d="M40 680 H800 V760 H40 Z"/>
    <path class="draw" pathLength="1" style="--d:.5s;--dur:1s" d="M80 720 h60 M180 720 h60 M280 720 h60 M380 720 h60 M480 720 h60 M580 720 h60 M680 720 h60" stroke="rgba(2,34,31,.25)" stroke-width="3"/>
    <rect class="fill2 f" style="--d:1.8s" x="110" y="390" width="620" height="290" stroke="none"/>
    <path class="draw" pathLength="1" style="--d:1.1s" d="M110 680 V390 H730 V680"/>
    <path class="draw" pathLength="1" style="--d:1.9s;--dur:1s" d="M365 680 V520 H475 V680"/>
    <circle class="pop" style="--d:2.6s" cx="455" cy="604" r="7" fill="#02221F"/>
    <path class="draw" pathLength="1" style="--d:2.6s" d="M60 400 L420 170 L780 400" stroke-width="6"/>
    ''' + _house_marks() + '''
  </svg>
  <img class="av pop" style="--d:3.6s" src="../assets/av/agent-salute.svg" alt="The agent on the roof"></div>
  <div class="lvs">''' + _house_rows() + '''</div>
</div>
''', "\"AI is like a house. Most people only look at the roof. The AI is the exciting part. But a roof needs a house under it, and AI on messy data only makes mistakes faster. So build from the foundation up. For each level, 1 risk and 1 question to check yourself.\n\n1, the foundation: clean data. 1 code per item, fixed units, and stock that matches the shelf because every carton is scanned and every job recorded. Without it, the AI quotes the wrong price and promises stock you do not have. Check: when you count, does the system match the shelf?\n\n2, the door: a safe connection. The AI goes through a controlled door that keeps your accounting rules, never straight into the database. Without it, 1 wrong command can freeze the server or break your accounts. Check: does any tool write straight into your SQL database?\n\n3, the walls: permissions and approvals. Who may see what, do what, and say yes, with every action logged. Without them, the AI can change anything, and nobody knows who did what. Check: is it written down who approves discounts, credit and purchases?\n\n4, the roof: the AI Agents doing the daily work. Without them, people keep typing and chasing by hand. Check: which job eats the most hours each week?\n\nFor the next part, I will show you the whole house, working.\"\n\nThe house builds itself from the ground up; the numbered dots match the 4 levels. This is thread 2; it returns later in the deck.\nNext: \"Before the demo, 1 picture every admin in this room will understand.\"")

# ============================================================ 4 · SUDU AI AND LIVE DEMO
def col16(h, items, d, mid=False):
    li = ''.join('<li>%s</li>' % x for x in items)
    return '<div class="%s c r" style="--d:%s"><h3>%s</h3><ul>%s</ul></div>' % ('mid' if mid else 'glass', d, h, li)
ARROW16 = '<div class="arr f" style="--d:%s"><svg viewBox="0 0 80 20" fill="none"><path d="M2 10H74M66 3l8 7-8 7" stroke="rgba(2,34,31,.35)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle r="5" fill="#00A57A"><animateMotion dur="1.6s" repeatCount="indefinite" path="M2 10H70"/></circle></svg></div>'
slide('16-sql-stays', 'SQL Account stays', SEC[3], 'light', 'data-sparks="9,1 1,5" style="--gx:50%;--gy:55%;--mx:50%;--my:55%"', '''
.h1 { max-width: 1664px; }
.flow { display:grid; grid-template-columns: 1fr 80px 1fr 80px 1fr; gap: 18px; align-items:stretch; margin-top: 56px; }
.c { padding: 40px 42px; border-radius: 30px; }
.c h3 { font-size: 34px; font-weight: 650; letter-spacing: -.015em; margin-bottom: 26px; display:flex; align-items:center; gap: 14px; }
.c ul { list-style:none; display:grid; gap: 16px; }
.c li { font-size: 32px; color: var(--ink-2); padding-left: 26px; position:relative; }
.c li::before { content:""; position:absolute; left:0; top: .58em; width: 9px; height: 9px; border-radius: 50%; background: var(--emerald); }
.mid { background: var(--ink); color: var(--on-dark); box-shadow: 0 40px 80px -40px rgba(2,34,31,.6), 0 0 80px rgba(0,245,169,.18); }
.mid li { color: var(--on-dark-2); } .mid li::before { background: var(--neon); }
.arr { display:grid; place-items:center; }
.arr svg { width: 80px; }
.sync { margin-top: auto; display:flex; align-items:center; gap: 36px; font-size: 32px; color: var(--ink-2); }
.sync img { height: 190px; border-radius: 10px; box-shadow: 0 0 0 1px var(--line), 0 18px 30px -18px rgba(2,34,31,.4); }
''', '''
<h1 class="h1 r" style="--d:.1s">SQL Account keeps the records. <span class="g">SuDu AI does the work.</span></h1>
<div class="flow">
%s%s%s%s%s
</div>
<div class="sync r" style="--d:1.6s"><img src="../assets/shot-sqlsync.png" alt="SQL Sync Agent setup screen">Connected by SuDu’s own tool, with permission control.</div>
''' % (col16('SQL Account knows', ['Customers', 'Prices', 'Credit', 'Your accounts'], '.4s'), ARROW16 % '.9s',
       col16('SuDu AI does', ['Takes orders', 'Moves stock', 'Runs production', 'Collects payments'], '.6s', True), ARROW16 % '1.1s',
       col16('Back in SQL Account', ['Orders', 'Invoices', 'GRNs', 'Receipts'], '.8s')),
"\"You keep SQL Account. Your accounts team keeps working in it exactly as they do today. SQL Account keeps the records: it knows your customers, prices and credit terms. SuDu does the daily work using that knowledge. And every result goes back into SQL Account. This is the door of the house: SuDu connects through its own tool, with permission control. Nothing writes straight into your database.\"\n\nNote: confirm with the product team exactly which documents post back to SQL Account in the version on sale.\nNext: \"Now the foundation.\"")

slide('17-foundation', 'The foundation: WMS and MES', SEC[3], 'light', 'data-sparks="9,1 1,5" style="--gx:50%;--gy:50%;--mx:50%;--my:50%"', '''
.cols { flex:1; display:grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 48px; }
.c { padding: 40px 46px; display:grid; grid-template-columns: 220px 1fr; gap: 36px; align-items:center; }
.c .av, .phone { width: 220px; height: 220px; }
.phone { border-radius: 50%; background:#fff; display:grid; place-items:center; box-shadow: 0 30px 60px -28px rgba(2,34,31,.45), 0 0 0 1px rgba(2,34,31,.06); }
.phone .ph2 { width: 100px; height: 170px; border-radius: 18px; border: 5px solid var(--ink); position:relative; display:grid; place-items:center; overflow:hidden; }
.phone .tag { width: 58px; height: 58px; background: conic-gradient(var(--ink) 25%, #fff 0 50%, var(--ink) 0 75%, #fff 0) 0 0/19px 19px; border: 4px solid var(--ink); }
.phone .bar { position:absolute; left: 8px; right: 8px; height: 3px; background: var(--neon); box-shadow: 0 0 10px 3px rgba(0,245,169,.7); animation: scan 1.8s ease-in-out infinite alternate; top: 30px; }
.k { font-family: var(--mono); font-size: 22px; letter-spacing: .12em; color: var(--green); font-weight: 600; }
.steps { font-size: 30px; line-height: 1.35; color: var(--ink-2); margin-top: 12px; }
.res { grid-column: 1 / -1; border-top: 1px solid var(--line); padding-top: 30px; display:flex; align-items:baseline; gap: 22px; }
.res .n { font-size: 124px; font-weight: 650; letter-spacing: -.05em; line-height: 1; color: var(--green); }
.res .t { font-size: 32px; font-weight: 600; line-height: 1.2; }
.res .t small { display:block; font-size: 24px; font-weight: 500; color: var(--ink-3); margin-top: 6px; }
h1 .sig:lang(en) { margin-left: .26em; }
''', '''
<h1 class="h1 r" style="--d:.1s">AI + mobile app make work<span class="sig" style="--sd:1.1s">easier</span></h1>
<div class="cols">
  <div class="glass c r" style="--d:.3s">
    <img class="av pop" style="--d:.6s" src="../assets/av/rahman-scan.svg" alt="Rahman scanning a carton">
    <div><div class="k">WAREHOUSE · WMS</div><p class="steps">Receive, put away, pick, deliver, count. All by scanning.</p></div>
    <div class="res"><span class="n">−<span data-count="90" data-delay="1.2">0</span>%</span><span class="t">Stock differences down</span></div>
  </div>
  <div class="glass c r" style="--d:.5s">
    <div class="phone pop" style="--d:.8s"><div class="ph2"><div class="tag"></div><div class="bar"></div></div></div>
    <div><div class="k">FACTORY · MES</div><p class="steps">Plan, issue materials, report output.</p></div>
    <div class="res"><span class="n">−<span data-count="80" data-delay="1.4">0</span>%</span><span class="t">Manual data entry down</span></div>
  </div>
</div>
''', "\"The foundation is simple: scan it once, where it happens. In the warehouse, the storekeeper scans the carton when it arrives, when it goes on the shelf, when it is picked. No paper, no typing later. One of our customers cut their stock differences by ninety percent. In the factory it is the same idea: scan the job, record what was used and what was made. Another customer cut manual data entry by eighty percent. If you have no factory, ignore the right side. The point is the same. Scanned, not typed.\"\n\nNote: the company profile credits -90% stock discrepancy to Twin Arrow and -80% manual data entry to BHPetrol. Name them only with permission.\nNext: \"On top of that clean data sits the AI team.\"")

team = [('agent-typing.svg', 'Sales AI', 'takes orders'), ('av-agent-clip.png', 'Purchase AI', 'buys stock'), ('agent-bullseye.svg', 'Inventory AI', 'watches stock'),
        ('agent-payday.svg', 'Collection AI', 'collects payments'), ('av-agent-invoice.png', 'Payment AI', 'pays suppliers'), ('av-agent-mega.png', 'Up Sales AI', 'brings customers back'),
        ('av-agent-chart.png', 'Finance AI', 'tracks the numbers')]
t18 = ''.join('<div class="glass m pop" style="--d:%.2fs"><img class="av" src="../assets/av/%s" alt=""><b>%s</b><span>%s</span></div>' % (0.35 + i * 0.12, f, n, j) for i, (f, n, j) in enumerate(team))
slide('18-ai-team', 'The AI team', SEC[3], 'light', 'data-sparks="9,1 1,5" style="--gx:50%;--gy:60%;--mx:50%;--my:60%"', '''
.team { display:flex; flex-wrap:wrap; gap: 24px; justify-content:center; margin-top: 36px; }
.m { width: 396px; padding: 30px 34px 32px; display:flex; flex-direction:column; align-items:flex-start; }
.m .av { width: 128px; height: 128px; margin-bottom: 22px; }
.m b { font-size: 36px; font-weight: 650; letter-spacing: -.015em; white-space: nowrap; }
.m span { font-size: 28px; color: var(--ink-2); line-height: 1.25; margin-top: 4px; }
.end { margin-top: auto; text-align:center; font-size: 34px; font-weight: 600; letter-spacing: -.01em; }
.end span { color: var(--ink-3); font-weight: 500; }
.end span:lang(en) { margin-left: .28em; }
''', '''
<h1 class="h1 r" style="--d:.1s">7 agents, each with 1 job</h1>
<div class="team">%s</div>
<p class="end r" style="--d:1.4s">AI handles the normal cases,<span>people decide the special ones.</span></p>
''' % t18,
"\"You do not get one AI that does everything. You get a team, like your own office. One takes orders. One watches stock. One chases payments. And they all follow one rule: the AI handles the normal cases, and the special cases go to a person to decide. Enough slides. Let me show you a working day.\"\n\nNext: hand over to the demo.")

# demo day — stops on a sun arc
# ---------------- Live demo: setting up + use cases, one slide each ----------------
AGENT_AV = {'Setting up': 'agent-salute.svg', 'Sales AI': 'agent-typing.svg', 'Inventory AI': 'agent-bullseye.svg', 'Purchase AI': 'av-agent-clip.png',
            'Collection AI': 'agent-payday.svg', 'Up Sales AI': 'av-agent-mega.png', 'Finance AI': 'av-agent-chart.png'}
PDF_I = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/></svg>'
IMG_I = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 17l-5-5-9 8"/></svg>'

def att(name, kind='pdf'):
    return '<span class="att">' + (PDF_I if kind == 'pdf' else IMG_I) + name + '</span>'
def tbl(head, rows, foot=None):
    h = '<tr>' + ''.join('<th>' + c + '</th>' for c in head) + '</tr>'
    b = ''.join('<tr>' + ''.join('<td>' + c + '</td>' for c in r) + '</tr>' for r in rows)
    f = '<tr class="ft">' + ''.join('<td>' + c + '</td>' for c in foot) + '</tr>' if foot else ''
    return '<table>' + h + b + f + '</table>'
def card(title, status, body, btns=None, tag=None):
    st = '<span class="st ' + status[0] + '">' + status[1] + '</span>' if status else ''
    tg = '<span class="src">' + tag + '</span>' if tag else ''
    bt = '<div class="bt">' + ''.join('<span class="%s">%s</span>' % ('p' if i == 0 else '', x) for i, x in enumerate(btns)) + '</div>' if btns else ''
    return '<div class="cd"><div class="ch"><b>' + title + '</b>' + st + tg + '</div>' + body + bt + '</div>'
def bars(vals, labels):
    m = max(vals)
    return '<div class="bars">' + ''.join('<div><i style="--h:%d%%"></i><span>%s</span></div>' % (v * 100 / m, l) for v, l in zip(vals, labels)) + '</div>'

def ui(msgs, title='Chat'):
    body = ''
    for k, m in enumerate(msgs):
        d = 0.8 + k * 0.6
        if m[0] == 'u':
            body += '<div class="mu pop" style="--d:%.1fs">%s%s</div>' % (d, ''.join(m[2:]) if len(m) > 2 else '', m[1])
        else:
            body += '<div class="ma pop" style="--d:%.1fs"><span class="who">SuDu AI</span>%s</div>' % (d, m[1])
    return ('<div class="app r" style="--d:.3s"><div class="rail"><b>S</b><i class="on">' + ic(CHAT, 26) + '</i><i>' + ic(LIST, 26) + '</i><i>'
            + ic('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>', 26) + '</i></div>'
            '<div class="win"><div class="wh"><b>' + title + '</b><span>Maju Jaya Foods &middot; Web and mobile</span></div><div class="wb">' + body + '</div>'
            '<div class="wc"><span>Ask SuDu AI&hellip;</span><i>' + ic('<path d="M5 12h14M13 6l6 6-6 6"/>', 22, 2.4) + '</i></div></div></div>')

def wa(who, msgs):
    body = ''
    for k, (w, t) in enumerate(msgs):
        body += '<div class="b %s pop" style="--d:%.1fs">%s</div>' % ({'c': 'inc', 'a': 'ai', 's': 'sys'}[w], 0.8 + k * .55, t)
    return ('<div class="ph r" style="--d:.3s"><div class="hd"><i>' + who[0] + '</i><div>' + who + '<span>WhatsApp</span></div></div><div class="bd">' + body + '</div></div>')

UC_CSS = '''
.slide { padding-top: 78px; }
.grid2 { flex:1; display:grid; grid-template-columns: 1fr 1000px; gap: 50px; }
.ag { display:flex; align-items:center; gap: 14px; }
.ag .av { width: 76px; height: 76px; }
.ag b { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .12em; color: var(--green); }
.ag span { display:block; font-size: 22px; color: var(--ink-3); }
.lf h1 { font-size: 58px; font-weight: 750; letter-spacing: -.03em; line-height: 1.04; margin-top: 18px; }
.chn { display:flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
.chn span { font-size: 21px; font-weight: 700; padding: 6px 14px; border-radius: 999px; }
.chn .web { background: #DBEAFE; color: #1D4ED8; } .chn .wa { background: rgba(37,211,102,.16); color: #128C7E; } .chn .rt { background: #EDE9FE; color: #6D28D9; }
.lf ol { list-style:none; margin-top: 26px; display:grid; gap: 12px; }
.lf li { display:grid; grid-template-columns: 48px 1fr; gap: 14px; align-items:center; font-size: 29px; line-height: 1.25; padding: 14px 16px; border-radius: 16px; background: #fff; box-shadow: 0 0 0 1px var(--line); }
.lf li i { font-style: normal; width: 48px; height: 48px; border-radius: 13px; background: var(--mint); color: var(--green); display:grid; place-items:center; font-weight: 800; font-size: 24px; }
.lf .wt { margin-top: 20px; font-size: 25px; color: var(--ink-2); display:flex; gap: 10px; align-items:flex-start; }
.lf .wt b { color: var(--ink); }
/* AI agent UI (Tasks module look) */
.app { display:flex; height: 830px; margin-top: -10px; border-radius: 22px; overflow:hidden; background: #fff; font-family: Inter, var(--sans); color: #111827;
  box-shadow: 0 0 0 1px #E5E7EB, 0 40px 80px -40px rgba(2,34,31,.5); }
.rail { width: 74px; background: #F7F7F8; border-right: 1px solid #E5E7EB; display:flex; flex-direction:column; align-items:center; gap: 10px; padding-top: 18px; }
.rail b { width: 42px; height: 42px; border-radius: 12px; background: #05976a; color: #fff; display:grid; place-items:center; font-size: 22px; margin-bottom: 8px; }
.rail i { width: 52px; height: 52px; border-radius: 12px; display:grid; place-items:center; color: #6B7280; }
.rail i.on { background: #ecfdf5; color: #047857; }
.win { flex:1; display:flex; flex-direction:column; min-width: 0; }
.wh { padding: 16px 24px; border-bottom: 1px solid #E5E7EB; display:flex; align-items:baseline; gap: 14px; }
.wh b { font-size: 26px; font-weight: 600; } .wh span { font-size: 19px; color: #6B7280; }
.wb { flex:1; padding: 22px 24px; display:flex; flex-direction:column; gap: 16px; justify-content:flex-end; background: #FCFCFD; overflow:hidden; }
.mu { align-self:flex-end; max-width: 82%; background: #D3F0E2; border-radius: 18px 18px 4px 18px; padding: 14px 18px; font-size: 24px; line-height: 1.38; }
.mu .att { margin-bottom: 8px; }
.ma { align-self:flex-start; width: 92%; font-size: 23px; line-height: 1.4; }
.ma .who { display:block; font-size: 18px; font-weight: 600; color: #047857; margin-bottom: 6px; }
.att { display:inline-flex; align-items:center; gap: 8px; padding: 8px 12px; border-radius: 10px; background: #fff; border: 1px solid #E5E7EB; font-size: 20px; font-weight: 600; margin-right: 8px; }
.att svg { color: #E11D48; }
.cd { border: 1px solid #E5E7EB; border-radius: 16px; background: #fff; overflow:hidden; box-shadow: 0 1px 2px rgba(0,0,0,.05); }
.ch { display:flex; align-items:center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid #E5E7EB; }
.ch b { font-size: 23px; font-weight: 600; }
.st { font-size: 17px; font-weight: 600; padding: 2px 10px; border-radius: 999px; }
.st.d { background: #FEF3C7; color: #92400E; } .st.g { background: #DCFCE7; color: #15803D; } .st.b { background: #DBEAFE; color: #1D4ED8; } .st.v { background: #EDE9FE; color: #6D28D9; } .st.bl { background: #DBEAFE; color: #1D4ED8; }
.src { margin-left: auto; font-size: 17px; color: #6B7280; }
.cd table { width: 100%; border-collapse: collapse; font-size: 20px; }
.cd th { text-align:left; font-weight: 600; font-size: 16px; text-transform: uppercase; letter-spacing: .05em; color: #6B7280; background: #F9FAFB; padding: 8px 16px; }
.cd td { padding: 9px 16px; border-top: 1px solid #F1F2F4; }
.cd td:not(:first-child), .cd th:not(:first-child) { text-align: right; }
.cd tr.ft td { font-weight: 700; }
.cd .tx { padding: 12px 16px; font-size: 21px; color: #374151; }
.cd .kv { display:grid; grid-template-columns: auto 1fr; gap: 6px 20px; padding: 12px 16px; font-size: 21px; }
.cd .kv span { color: #6B7280; }
.bt { display:flex; gap: 10px; justify-content:flex-end; padding: 10px 16px; border-top: 1px solid #E5E7EB; }
.bt span { font-size: 19px; font-weight: 600; padding: 6px 14px; border-radius: 9px; border: 1px solid #E5E7EB; }
.bt span.p { background: #05976a; border-color: #05976a; color: #fff; }
.bars { display:flex; align-items:flex-end; gap: 14px; height: 170px; padding: 14px 18px 8px; }
.bars div { flex:1; height: 100%; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; gap: 6px; }
.bars i { display:block; width: 100%; height: var(--h); border-radius: 6px 6px 0 0; background: linear-gradient(#10B981, #05976a); }
.bars span { font-size: 15px; color: #6B7280; }
.kp { display:grid; grid-template-columns: repeat(3, 1fr); border-bottom: 1px solid #F1F2F4; }
.kp div { padding: 10px 16px; } .kp small { display:block; font-size: 16px; color: #6B7280; } .kp b { font-size: 26px; font-weight: 700; }
.kp b.up { color: #15803D; } .kp b.dn { color: #BE123C; }
.wc { margin: 12px 20px 16px; display:flex; align-items:center; justify-content:space-between; border: 1px solid #E5E7EB; border-radius: 22px; padding: 10px 10px 10px 20px; background: #F9FAFB; font-size: 21px; color: #9CA3AF; }
.wc i { width: 40px; height: 40px; border-radius: 50%; background: #05976a; color: #fff; display:grid; place-items:center; }
/* WhatsApp phone */
.ph { height: 830px; margin-top: -10px; border-radius: 30px; overflow:hidden; display:flex; flex-direction:column; box-shadow: 0 0 0 1px var(--line), 0 40px 70px -40px rgba(2,34,31,.45); }
.ph .hd { display:flex; align-items:center; gap: 14px; padding: 18px 24px; background: #075E54; color: #fff; font-size: 28px; font-weight: 700; }
.ph .hd i { width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,.25); display:grid; place-items:center; font-style: normal; font-size: 22px; }
.ph .hd span { font-size: 19px; font-weight: 500; opacity: .8; display:block; }
.ph .bd { flex:1; padding: 24px; display:flex; flex-direction:column; gap: 14px; justify-content:flex-end; background: radial-gradient(circle, rgba(0,0,0,.04) 1.2px, transparent 1.6px) 0 0 / 22px 22px, #EFE7DD; }
.b { max-width: 82%; font-size: 28px; line-height: 1.32; padding: 14px 20px; border-radius: 18px; box-shadow: 0 1px 1px rgba(0,0,0,.12); color: #111; }
.b.inc { align-self:flex-start; background: #fff; border-top-left-radius: 4px; }
.b.ai { align-self:flex-end; background: #D9FDD3; border-top-right-radius: 4px; }
.b.ai::before { content: "SuDu AI"; display:block; font-family: var(--mono); font-size: 17px; font-weight: 700; color: var(--green); letter-spacing: .06em; margin-bottom: 2px; }
.b.sys { align-self:center; background: #FFF4C2; font-size: 22px; border-radius: 10px; text-align:center; }
.b .att { display:flex; margin: 8px 0 0; }
'''

CH = {'web': '<span class="web">Web &middot; Mobile</span>', 'wa': '<span class="wa">WhatsApp</span>', 'rt': '<span class="rt">Routine</span>'}

USECASES = [
  # (agent, n_of, title, channels, steps, watch, mock)
  ('Setting up', '', 'Set it up once', ['web'],
   ['Link WhatsApp', 'Set up contacts', 'Auto-save to SQL Account', 'Check the stock balance', 'Set approvals: credit limit, minimum price', 'Load past prices'],
   'Done once. Every agent uses these settings.',
   ui([('a', card('Settings', ('g', 'Ready'), '<div class="kv"><span>WhatsApp</span><b>Connected &middot; +60 12-345 6789</b><span>Contacts</span><b>128 synced from SQL Account</b>'
        '<span>Auto-post</span><b>Draft first, you approve</b><span>Stock balance</span><b>Checked &middot; 1,240 items</b><span>Approval</span><b>Over credit limit &rarr; Boss</b>'
        '<span>Approval</span><b>Below minimum price &rarr; Sales manager</b><span>Prices</span><b>Last price per customer</b></div>'))], 'Settings')),
  ('Sales AI', '1 of 3', 'Create a sales order', ['web'],
   ['Type the order in plain words', 'Or upload the customer&rsquo;s PDF or photo', 'Check the draft, then approve'],
   'Prices come from the customer&rsquo;s history.',
   ui([('u', 'Create SO for Jaya Grocer: bawang besar 10kg x 6, ayam cincang 8 ekor x 4. Deliver tomorrow before 12pm.', att('PO26111504SMK.pdf')),
       ('a', card('Sales Order SO-10231', ('d', 'Draft'), tbl(['Item', 'Qty', 'Price', 'Amount'], [['Bawang Besar China 10kg', '6', '28.00', '168.00'], ['Ayam Cincang (8 ekor)', '4', '96.00', '384.00']], ['Total', '', '', 'RM552.00']),
                  ['Approve', 'Edit'], 'Delivery: tomorrow, before 12pm'))])),
  ('Sales AI', '2 of 3', 'Send the SO or invoice to the customer', ['web', 'wa'],
   ['Add the customer&rsquo;s WhatsApp number in Contacts', 'Ask: &ldquo;Send SI-2001 to Jaya Grocer&rdquo;', 'The PDF lands in their WhatsApp'],
   'No download, no forwarding.',
   wa('Jaya Grocer KL', [('a', 'Hi Jaya Grocer, here is your invoice SI-2001 for RM552.00. Thank you!' + att('SI-2001.pdf')), ('c', 'Received, thanks')])),
  ('Sales AI', '3 of 3', 'Turn the sales order into an invoice', ['web'],
   ['Ask in plain words', 'It copies every line from the SO', 'Saved into SQL Account'],
   'No retyping between SO and invoice.',
   ui([('u', 'Convert SO-10231 into an invoice.'),
       ('a', card('Sales Invoice SI-2001', ('g', 'Posted'), '<div class="kv"><span>From</span><b>SO-10231 &middot; Jaya Grocer KL</b><span>Lines</span><b>2 items, RM552.00</b><span>SQL Account</span><b>Posted &middot; 15/11/2026 10:02</b></div>', ['Send to customer', 'Open']))])),
  ('Inventory AI', '1 of 3', 'Check stock balance', ['web'],
   ['Type /accounting to ask SQL Account directly', 'Or ask the ERP, after it updates', 'Get the answer in seconds'],
   '/accounting reads straight from SQL Account.',
   ui([('u', '/accounting stock balance for Milo and Maggi'),
       ('a', card('Stock balance', None, tbl(['Item', 'Balance', 'Min'], [['Milo 1kg', '40 ctn', '50'], ['Maggi Kari 5s', '85 ctn', '40'], ['Maggi Ayam 5s', '62 ctn', '40']]), None, 'Source: SQL Account'))])),
  ('Inventory AI', '2 of 3', 'Create a stock report', ['web', 'wa'],
   ['Ask for a PDF report and send it on WhatsApp', 'Or ask for a live dashboard', 'Change it by asking again'],
   'A PDF to share, or a dashboard that keeps updating.',
   ui([('u', 'Make an inventory dashboard: low stock and slow movers.'),
       ('a', card('Inventory dashboard', ('bl', 'Live'), '<div class="kp"><div><small>Items low</small><b class="dn">7</b></div><div><small>Slow movers</small><b>12</b></div><div><small>Stock value</small><b>RM482k</b></div></div>'
                  + bars([40, 85, 62, 120, 30, 95], ['Milo', 'Kari', 'Ayam', 'Rice', 'Oil', 'Sugar']), ['Send PDF to WhatsApp', 'Open dashboard']))])),
  ('Inventory AI', '3 of 3', 'Send a report on a schedule', ['web', 'rt', 'wa'],
   ['Ask once, in plain words', 'It becomes a routine', 'The report arrives every week'],
   'Ask once. It runs every week.',
   ui([('u', 'Every Monday 8am, send the inventory report to my WhatsApp.'),
       ('a', card('Routine created', ('v', 'Routine'), '<div class="kv"><span>When</span><b>Every Monday, 8:00 am</b><span>Does</span><b>Inventory report (PDF)</b><span>Sends to</span><b>Boss &middot; WhatsApp</b><span>Next run</span><b>Mon 17 Nov, 8:00 am</b></div>', ['Done', 'Edit']))])),
  ('Purchase AI', '1 of 3', 'Create a purchase order', ['web'],
   ['Type it in plain words', 'Or upload a photo of a handwritten list', 'Approve and send'],
   'Even messy handwriting becomes a clean PO.',
   ui([('u', 'Make a PO to Golden Palm from this.', att('handwritten-list.jpg', 'img')),
       ('a', card('Purchase Order PO-55012', ('d', 'Draft'), tbl(['Item', 'Qty', 'Cost'], [['Milo 1kg', '160 ctn', 'RM7,040'], ['Maggi Kari 5s', '40 ctn', 'RM1,180']], ['Total', '', 'RM8,220']), ['Approve', 'Edit'], 'Golden Palm Sdn Bhd'))])),
  ('Purchase AI', '2 of 3', 'Supplier invoice to purchase invoice', ['web'],
   ['Upload the supplier&rsquo;s invoice', 'It matches the PO and goods received', 'Saved as a purchase invoice'],
   'Wrong qty or price is caught first.',
   ui([('u', 'Record this supplier invoice.', att('GoldenPalm-INV-8841.pdf')),
       ('a', card('Purchase Invoice PI-778', ('g', 'Matched'), '<div class="kv"><span>Supplier</span><b>Golden Palm &middot; INV-8841</b><span>Matched to</span><b>PO-55012 &middot; GRN-3301</b><span>Amount</span><b>RM8,220.00 &middot; 2 lines</b><span>Check</span><b>Qty and price match</b></div>', ['Post to SQL Account', 'Review']))])),
  ('Purchase AI', '3 of 3', 'Chase late deliveries', ['web', 'wa'],
   ['Set a task: chase POs not yet received', 'It messages the supplier on WhatsApp', 'The reply goes back to the buyer'],
   'No more calling suppliers one by one.',
   wa('Golden Palm (supplier)', [('a', 'Hi Golden Palm, PO-55012 (Milo 1kg, 160 ctn) was due Monday. When can you deliver?'), ('c', 'Sorry boss, tomorrow morning.'),
                                 ('a', 'Noted, thank you. I have updated the buyer.'), ('s', 'Task updated: PO-55012 expected tomorrow')])),
  ('Collection AI', '1 of 3', 'Check overdue customers', ['web', 'rt', 'wa'],
   ['Create a routine to check overdue customers', 'It opens a task with the list', 'Send each statement on WhatsApp'],
   'Every weekday, nobody has to remember.',
   ui([('u', 'Every weekday 9am, check overdue customers and send their statements.'),
       ('a', card('Task: overdue customers', ('d', 'Needs you'), tbl(['Customer', 'Overdue', 'Days'], [['Kedai Ali', 'RM4,820', '45'], ['Mega Mart', 'RM5,100', '62'], ['Sri Murni', 'RM2,460', '71']]), ['Send SOA on WhatsApp', 'Edit list']))])),
  ('Collection AI', '2 of 3', 'Customer asks for more time', ['wa', 'web'],
   ['The customer replies on WhatsApp', 'The reply shows up in the task', 'You approve the next step'],
   'You decide. It follows up on the day.',
   ui([('a', card('Kedai Ali replied', ('d', 'Approve?'), '<div class="tx">&ldquo;Jumaat saya bayar.&rdquo;</div><div class="kv"><span>Overdue</span><b>RM4,820</b><span>Plan</span><b>Remind again Friday, 10:00 am</b></div>', ['Approve', 'Reply myself']))], 'Tasks')),
  ('Collection AI', '3 of 3', 'Customer sends a|payment receipt', ['wa'],
   ['The customer sends the payment receipt on WhatsApp', 'It reads the amount and matches invoices', 'A customer payment is created'],
   'No payment receipts lost in the chat.',
   wa('Kedai Ali', [('c', 'Dah bank in boss' + att('bank-slip.jpg', 'img')), ('a', 'Received RM2,640, matched to INV-3301 and INV-3307. Thank you!'),
                    ('s', 'Customer Payment OR-1102 created in SQL Account')])),
  ('Up Sales AI', '1 of 1', 'Win back lost customers', ['web', 'wa'],
   ['Find customers with no order in 30 days', 'Send them a promotion on WhatsApp', 'Attach a promo PDF'],
   'Customers come back before they forget you.',
   ui([('u', 'Find customers with no order in 30 days and send them our November promo.'),
       ('a', card('12 lost customers', ('d', 'Approve send'), tbl(['Customer', 'Last order'], [['Kedai Ah Seng', '34 days'], ['Restoran Hijau', '41 days'], ['+ 10 more', '']]) + '<div class="tx">' + att('November-promo.pdf') + '</div>', ['Send to 12', 'Edit message']))])),
  ('Finance AI', '1 of 2', 'Ask for financial numbers', ['web'],
   ['Ask in plain words', 'Profit and loss, sales, who owes you', 'Answers straight from SQL Account'],
   'An afternoon in Excel becomes 1 question.',
   ui([('u', 'What is my profit this month compared with last month?'),
       ('a', card('Profit and loss &middot; November', None, '<div class="kp"><div><small>Sales</small><b>RM412k</b></div><div><small>Gross profit</small><b>RM86k</b></div><div><small>vs October</small><b class="up">+8%</b></div></div>'
                  + tbl(['', 'Nov', 'Oct'], [['Sales', '412,300', '398,900'], ['Cost of sales', '326,100', '319,200'], ['Gross profit', '86,200', '79,700']]), None, 'Source: SQL Account'))])),
  ('Finance AI', '2 of 2', 'Create a financial dashboard', ['web', 'wa'],
   ['Ask for a PDF and send it on WhatsApp', 'Or ask for a live dashboard', 'Share it with your partners'],
   'Your numbers, any time.',
   ui([('u', 'Make a finance dashboard: sales, profit and cash, by month.'),
       ('a', card('Finance dashboard', ('bl', 'Live'), '<div class="kp"><div><small>Cash</small><b>RM238k</b></div><div><small>Debtors</small><b>RM164k</b></div><div><small>Margin</small><b>20.9%</b></div></div>'
                  + bars([360, 375, 392, 380, 399, 412], ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']), ['Send PDF to WhatsApp', 'Open dashboard']))])),
]

TEAM = [  # name, agent, avatar, job, colour, background
    ('Sasha', 'Sales AI', 'team-sasha.svg', 'Takes orders from WhatsApp, PDF and chat', '#00A57A', 'linear-gradient(160deg,#E9FFF6,#C8F5E3)'),
    ('Ivan', 'Inventory AI', 'team-ivan.svg', 'Checks stock, sends stock reports', '#2563EB', 'linear-gradient(160deg,#EEF4FF,#D3E2FF)'),
    ('Puteri', 'Purchase AI', 'team-puteri.svg', 'Makes POs, records supplier invoices', '#7C5CFF', 'linear-gradient(160deg,#F4F0FF,#E0D7FF)'),
    ('Cody', 'Collection AI', 'team-cody.svg', 'Chases overdue payments, reads bank slips', '#E5762B', 'linear-gradient(160deg,#FFF5EC,#FFDFC6)'),
    ('Uma', 'Up Sales AI', 'team-uma.svg', 'Wins back lost customers', '#DB2777', 'linear-gradient(160deg,#FFF0F7,#FFD3E7)'),
    ('Felix', 'Finance AI', 'team-felix.svg', 'Explains the numbers, builds dashboards', '#0F766E', 'linear-gradient(160deg,#ECFBF9,#C7EFEA)'),
]
TEAM_CSS = '''
body { background: #FBFAF6; }
.bg { display: none; }
.slide { padding-top: 100px; }
.kicker { font-size: 22px; letter-spacing: .2em; color: var(--green); }
.h1 { font-size: 80px; margin-top: 14px; }
.lead { font-size: 31px; margin-top: 14px; max-width: 1300px; color: var(--ink-2); }
.row { display:grid; grid-template-columns: repeat(6, 1fr); gap: 20px; margin-top: 60px; }
.tm { border-radius: 26px; padding: 30px 18px 28px; background: #fff; text-align:center; display:flex; flex-direction:column; align-items:center;
  box-shadow: 0 0 0 1px rgba(2,34,31,.06), 0 24px 44px -30px rgba(2,34,31,.35); }
.tm .ph { width: 190px; height: 190px; border-radius: 50%; background: #fff; display:grid; place-items:center; box-shadow: 0 0 0 1px rgba(2,34,31,.08); }
.tm .av { width: 180px; height: 180px; box-shadow: none; }
.tm b { font-size: 40px; font-weight: 700; letter-spacing: -.02em; margin-top: 22px; color: var(--ink); }
.tm .ag { font-size: 25px; color: var(--ink-3); margin-top: 6px; }
.tm p { font-size: 24px; line-height: 1.3; color: var(--green); font-weight: 600; margin-top: 14px; }
.foot { margin-top: auto; font-size: 22px; color: var(--ink-3); }
'''
def demo_section():
    cnt = {}
    for u in USECASES: cnt[u[0]] = cnt.get(u[0], 0) + 1
    cards = ''
    for i, (nm, ag, av, job, col, bg) in enumerate(TEAM):
        cards += ('<div class="tm r" style="--d:%.2fs"><div class="ph"><img class="av" src="../assets/av/%s" alt=""></div>'
                  '<b>%s</b><span class="ag">%s</span><p>%s</p></div>' % (0.45 + i * .1, av, nm, ag, job))
    html = ('<div class="kicker r" style="--d:.05s">Live demo &middot; Meet the AI team</div>'
            '<h1 class="h1 r" style="--d:.15s">The 6 AI Agents in today&rsquo;s demo</h1>'
            '<p class="lead r" style="--d:.3s">A sample food distributor that runs SQL Account, with SuDu AI connected. Each agent has one job.</p>'
            '<div class="row">' + cards + '</div>')
    slide('19-demo-day', 'Live demo', SEC[3], 'light', 'data-sparks="none" style="--gx:50%;--gy:40%"', TEAM_CSS, html,
          "\"Let me introduce the 6 AI Agents in today's demo. They work for Maju Jaya Foods, a sample company with sample data. Sasha takes the orders. Ivan watches the stock. Puteri does the buying. Cody chases the money. Uma brings lost customers back. Felix keeps the numbers. First we set them up once, then each one does real jobs on the screen.\"\n\nEach next slide is 1 use case. Show it live, then come back to the slide.\nNext: \"Before we start, 1 quick note about today's demo account.\"")


def demo_uc(i):
    agent, nof, title, chans, steps, watch, mock = USECASES[i]
    st = ''.join('<li class="r" style="--d:%.2fs"><i>%d</i><span>%s</span></li>' % (0.4 + k * .12, k + 1, x) for k, x in enumerate(steps))
    sub = ('Use case ' + nof) if nof else 'Before the demo'
    plain = lambda t: re.sub('<[^>]+>', '', t).replace('&rsquo;', "'").replace('&ldquo;', '"').replace('&rdquo;', '"').replace('&middot;', '·').replace('|', ' ')
    nxt = USECASES[i + 1] if i + 1 < len(USECASES) else None
    note = ("\"" + agent + (", use case " + nof if nof else "") + ": " + plain(title).lower() + ". " + ' '.join(plain(x) + '.' for x in steps) + " " + plain(watch) + "\"\n\n"
            "Do: show it live on the real screen (" + ', '.join({'web': 'web or mobile app', 'wa': 'WhatsApp', 'rt': 'routine'}[c] for c in chans) + "), then come back to this slide."
            + ("\nPrep: historical prices to be prepared by Jordan Lee." if agent == 'Setting up' else '')
            + "\nNote: sample company and sample data; the screen on the slide is an illustration of the real one."
            + (("\nNext: \"" + nxt[0] + ": " + plain(nxt[2]).lower() + ".\"") if nxt and nxt[0] == agent else ("\nNext: the " + nxt[0] + " intro slide.") if nxt else "\nNext: \"So that is the whole team at work. Now, what does it never do without you?\""))
    slide('19-uc-%02d' % (i + 1), 'Demo: ' + agent + ' ' + nof, SEC[3], 'light', 'data-sparks="none" style="--gx:30%;--gy:70%;--mx:30%;--my:70%"', UC_CSS, '''
<div class="grid2">
  <div class="lf">
    <div class="ag r" style="--d:.05s"><img class="av" src="../assets/av/''' + AGENT_AV[agent] + '''" alt=""><div><b>''' + ({t[1]: t[0].upper() + ' &middot; ' for t in TEAM}.get(agent, '')) + agent.upper() + '''</b><span>''' + sub + '''</span></div></div>
    <h1 class="r" style="--d:.15s">''' + title.replace('|', '<br>') + '''</h1>
    <div class="chn r" style="--d:.25s">''' + ''.join(CH[c] for c in chans) + '''</div>
    <ol>''' + st + '''</ol>
    <p class="wt r" style="--d:1.2s">''' + ic(CHECK, 28, 3) + '''<b>''' + watch + '''</b></p>
  </div>
  ''' + mock + '''
</div>
''', note)

DEMO_ORDER = ['Setting up', 'Sales AI', 'Inventory AI', 'Purchase AI', 'Collection AI', 'Up Sales AI', 'Finance AI']
INTRO_CSS = '''
body { background: #FBFAF6; }
.bg { display: none; }
.slide { padding-top: 92px; }
.wrap { flex:1; display:grid; grid-template-columns: 1fr 600px; gap: 70px; align-items:start; padding-top: 30px; }
.wrap > .port { align-self:center; }
.kicker { font-size: 22px; letter-spacing: .2em; color: var(--green); }
.ti { font-size: 150px; font-weight: 800; letter-spacing: -.045em; line-height: .95; margin-top: 18px; color: var(--ink); }
.meet { font-size: 36px; color: var(--ink-2); margin-top: 22px; line-height: 1.3; }
.meet b { color: var(--ink); font-weight: 700; }
.lst h4 { font-family: var(--mono); font-size: 19px; font-weight: 700; letter-spacing: .14em; color: var(--ink-3); margin-top: 48px; }
.lst ol { list-style:none; margin-top: 14px; border-top: 2px solid var(--ink); }
.lst li { display:grid; grid-template-columns: 64px 1fr auto; align-items:center; gap: 12px; padding: 16px 0; border-bottom: 1px solid var(--line); }
.lst li i { font-style: normal; font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--green); }
.lst li span { font-size: 32px; font-weight: 600; letter-spacing: -.01em; }
.lst li em { font-style: normal; display:flex; gap: 8px; }
.lst li em u { text-decoration: none; font-size: 19px; font-weight: 700; padding: 5px 12px; border-radius: 999px; background: #EEF0EC; color: var(--ink-2); }
.lst.six li { padding: 11px 0; } .lst.six li span { font-size: 29px; }
.port { position:relative; width: 600px; height: 600px; display:grid; place-items:center; }
.port .disc { position:absolute; inset: 40px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 1px rgba(2,34,31,.07), 0 50px 90px -50px rgba(2,34,31,.45); }
.port .orb { position:absolute; inset: 0; border-radius: 50%; border: 1.5px dashed rgba(0,108,72,.28); animation: spin 60s linear infinite; }
.port .orb::after { content:""; position:absolute; top: 50%; left: -8px; width: 14px; height: 14px; margin-top: -7px; border-radius: 50%; background: var(--emerald); box-shadow: 0 0 0 6px rgba(0,165,122,.15); }
@keyframes spin { to { transform: rotate(360deg); } }
.port img { position:relative; width: 440px; height: 440px; }
.port .tag { position:absolute; bottom: 18px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 24px; font-weight: 700; padding: 10px 22px; border-radius: 999px; background: var(--ink); color: var(--on-dark); }
.port .tag b { color: var(--neon); font-weight: 700; }
.prog { display:grid; grid-template-columns: repeat(7, 1fr); gap: 12px; margin-top: 30px; }
.prog div { display:flex; flex-direction:column; gap: 10px; font-size: 20px; color: var(--ink-3); font-weight: 600; }
.prog i { display:block; height: 6px; border-radius: 3px; background: #E3E6E1; position:relative; overflow:hidden; }
.prog .dn i { background: var(--ink); } .prog .dn { color: var(--ink-2); }
.prog .on { color: var(--green); font-weight: 800; }
.prog .on i::after { content:""; position:absolute; inset: 0; background: var(--emerald); transform-origin: left; animation: grow 1s cubic-bezier(.2,.8,.2,1) .6s both; }
@keyframes grow { from { transform: scaleX(0); } }
'''
def demo_intro(agent):
    k = DEMO_ORDER.index(agent)
    team = {t[1]: t for t in TEAM}.get(agent)
    ucs = [u for u in USECASES if u[0] == agent]
    if team:
        nm, _, av, job, *_r = team
        meet = 'Meet <b>' + nm + '</b>. ' + job + '.'
        tag = nm + ' &middot; <b>' + agent + '</b>'
        rows = ''.join('<li class="r" style="--d:%.2fs"><i>%02d</i><span>%s</span><em>%s</em></li>'
                       % (0.55 + j * .12, j + 1, u[2].replace('|', ' '), ''.join('<u>' + {'web': 'Web', 'wa': 'WhatsApp', 'rt': 'Routine'}[c] + '</u>' for c in u[3])) for j, u in enumerate(ucs))
        cap, cls = '%d USE CASE%s' % (len(ucs), '' if len(ucs) == 1 else 'S'), ''
    else:
        av, meet, tag = AGENT_AV[agent], 'Done once, before the agents start.<br><b style="white-space:nowrap">Every AI Agent needs basic setup.</b>', '<b>Step 1</b>'
        rows = ''.join('<li class="r" style="--d:%.2fs"><i>%02d</i><span>%s</span><em></em></li>' % (0.55 + j * .1, j + 1, s_) for j, s_ in enumerate(ucs[0][4]))
        cap, cls = '%d THINGS TO SET' % len(ucs[0][4]), ' six'
    prog = ''.join('<div class="%s"><i></i>%s</div>' % ('dn' if j < k else 'on' if j == k else '', a.replace(' AI', '')) for j, a in enumerate(DEMO_ORDER))
    html = ('<div class="wrap"><div>'
            '<div class="kicker r" style="--d:.05s">Live demo &middot; Part %d of %d</div>' % (k + 1, len(DEMO_ORDER)) +
            '<h1 class="ti r" style="--d:.15s">' + agent + '</h1>'
            '<p class="meet r" style="--d:.3s">' + meet + '</p>'
            '<div class="lst' + cls + '"><h4 class="r" style="--d:.45s">' + cap + '</h4><ol>' + rows + '</ol></div>'
            '</div><div class="port pop" style="--d:.25s"><div class="orb"></div><div class="disc"></div><img src="../assets/av/' + av + '" alt=""><span class="tag">' + tag + '</span></div></div>'
            '<div class="prog r" style="--d:.5s">' + prog + '</div>')
    first = ucs[0]
    plain = lambda t: re.sub('<[^>]+>', '', t).replace('&rsquo;', "'").replace('&middot;', '·').replace('|', ' ')
    if team:
        note = ("\"Part %d: %s. Meet %s. %s. %s will show you %d %s.\"\n\nNext: \"%s, use case 1: %s.\""
                % (k + 1, agent, team[0], plain(team[3]), team[0], len(ucs), 'job' if len(ucs) == 1 else 'jobs', agent, plain(first[2]).lower()))
    else:
        note = "\"Step 1: before any agent works, we set it up once: WhatsApp, contacts, posting, stock, approvals and prices. Every AI Agent needs this basic setup.\"\n\nNext: \"Setting up, step by step.\""
    slide('19-intro-%02d' % (k + 1), 'Demo: ' + agent, SEC[3], 'light', 'data-sparks="none"', INTRO_CSS, html, note)

demo_section()

# ---------------- demo account disclaimer ----------------
def _disc_cards():
    out = ''
    for k, (nm, ag, av, *_r) in enumerate(TEAM):
        off = ag == 'Collection AI'
        out += ('<div class="dc%s u" style="--d:%.2fs"><div class="ph"><img src="../assets/av/%s" alt=""></div><b>%s</b><span>%s</span><em>%s</em></div>'
                % (' off' if off else '', .7 + k * .1, av, nm, ag, 'Slides only today' if off else 'Live demo'))
    return out
slide('19-demo-note', 'Demo account note', SEC[3], 'light', 'data-sparks="none"', MIN_CSS + '''
body { background: #FBFAF6; }
.mt { font-size: 72px; }
.nt { display:flex; align-items:flex-start; gap: 22px; margin-top: 34px; padding: 26px 32px; border-radius: 24px; background: #FFF6E8; box-shadow: inset 0 0 0 2px rgba(255,181,71,.55); }
.nt i { flex:none; display:grid; place-items:center; width: 60px; height: 60px; border-radius: 50%; background: #FFB547; color: var(--ink); }
.nt p { font-size: 34px; line-height: 1.4; color: var(--ink); }
.nt p b { color: #8A3417; }
.row { display:grid; grid-template-columns: repeat(6, 1fr); gap: 18px; margin-top: 44px; }
.dc { position:relative; padding: 22px 14px 20px; border-radius: 22px; background: #fff; text-align:center; display:flex; flex-direction:column; align-items:center; box-shadow: 0 0 0 1px rgba(2,34,31,.06), 0 20px 36px -30px rgba(2,34,31,.4); }
.dc .ph { width: 120px; height: 120px; border-radius: 50%; display:grid; place-items:center; box-shadow: 0 0 0 1px rgba(2,34,31,.08); }
.dc img { width: 112px; height: 112px; }
.dc b { font-size: 32px; font-weight: 750; margin-top: 14px; }
.dc span { font-size: 22px; color: var(--ink-3); margin-top: 2px; }
.dc em { font-style: normal; margin-top: 14px; font-size: 20px; font-weight: 750; padding: 6px 14px; border-radius: 999px; background: var(--mint); color: var(--green); }
.dc.off { background: #F4F4F1; box-shadow: inset 0 0 0 2px rgba(255,181,71,.6); }
.dc.off img { filter: grayscale(1); opacity: .55; }
.dc.off b, .dc.off span { color: var(--ink-3); }
.dc.off em { background: #FFF1DC; color: #8A3417; }
.ft { margin-top: auto; margin-bottom: 56px; font-size: 28px; color: var(--ink-2); }
.ft b { color: var(--ink); }
''', '''
<div class="mk u" style="--d:.05s">Before the demo</div>
<h1 class="mt u" style="--d:.15s">A quick note: this is a <em>demo account</em></h1>
<div class="nt u" style="--d:.4s"><i>''' + ic('<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>', 30, 2.4) + '''</i>
  <p>In a demo account we can&rsquo;t sync the full data from SQL Account, such as the <b>opening ledger</b>. So <b>Collection AI can&rsquo;t run its tasks live today</b>.</p></div>
<div class="row">''' + _disc_cards() + '''</div>
<p class="ft u" style="--d:1.5s">For Collection AI, we&rsquo;ll walk you through the slides. <b>On your own account with full data, it runs live.</b></p>
''',
"\"Before we start the demo, 1 quick note. What you are about to see runs on a demo account. In a demo account, we cannot sync the full data from SQL Account, for example the opening ledger, the balances each customer already owes. Collection AI needs exactly that data to know who is overdue. So today, Sales, Inventory, Purchase, Up Sales and Finance AI run live, and for Collection AI I will walk you through the slides instead. On your own account, with your full data synced, Collection AI runs live like the others.\"\n\nNext: \"Before any agent works, we set it up once.\"")
for _i in range(len(USECASES)):
    if _i == 0 or USECASES[_i - 1][0] != USECASES[_i][0]:
        demo_intro(USECASES[_i][0])
    demo_uc(_i)

slide('20-you-stay-the-boss', '4 things AI never does', SEC[3], 'light', 'data-sparks="1,1 6,5" style="--gx:75%;--gy:50%;--mx:75%;--my:50%"', '''
.wrap { flex:1; display:grid; grid-template-columns: 1fr 700px; gap: 80px; align-items:center; }
ol { list-style:none; display:grid; gap: 30px; margin-top: 50px; counter-reset: n; }
li { display:grid; grid-template-columns: 70px 1fr; font-size: 42px; line-height: 1.2; font-weight: 550; letter-spacing: -.015em; counter-increment: n; }
li::before { content: counter(n); font-family: var(--mono); font-size: 28px; color: var(--green); padding-top: 8px; }
.shot { position:relative; }
.shot img { width: 640px; border-radius: 26px; box-shadow: 0 0 0 1px var(--line), 0 60px 100px -50px rgba(2,34,31,.55); transform: rotate(2deg); }
.shot .cap { position:absolute; left: -40px; bottom: 60px; }
''', '''
<div class="wrap">
  <div>
    <h1 class="h1 r" style="--d:.1s">4 things it never does without you</h1>
    <ol>
      <li class="r" style="--d:.5s">Nothing is saved until you approve.</li>
      <li class="r" style="--d:.7s">It never moves money.</li>
      <li class="r" style="--d:.9s">It reads only the WhatsApp groups you switch on.</li>
      <li class="r" style="--d:1.1s">Everything it did is recorded for you to see.</li>
    </ol>
  </div>
  <div class="shot r" style="--d:.6s"><img src="../assets/shot-approve.png" alt="Approval card: Create sales order, waiting for you"><span class="pill cap pop" style="--d:1.6s">%s Waiting for your approval</span></div>
</div>
''' % ic(LOCK, 26),
"\"You just saw it do a lot. So let me tell you the 4 things AI never does. It does not save anything you have not approved. It never changes your financial figures. It only reads the WhatsApp groups you allow. And every single thing it did is recorded, so you can check it any time. You are still the boss. Now, would this work in your company? Let's find out.\"\n\nNext: \"Would this work in your company? Let's score it.\"")

# ============================================================ 5 · WORKSHOP
WG_GROUPS = [  # group number on the name tag, colour
    ('1', '#00A57A'),
    ('2', '#4DA3FF'),
    ('3', '#FFB547'),
]
WG_COACH = [('Guides you through the workshop', '1 step at a time'),
            ('Checks your answers', 'with you, at your table'),
            ('Tells you where to start', 'for your own company')]
WG_PERSON = '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>'
slide('23-workshop-groups', 'Workshop groups', SEC[5], 'light', 'data-sparks="none"', MIN_CSS + '''
.gp { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 36px; margin-top: auto; margin-bottom: 60px; }
.gp > div { display:flex; flex-direction:column; align-items:center; text-align:center; padding: 44px 24px 40px; border-radius: 32px; background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 40px 70px -50px rgba(2,34,31,.45); border-top: 10px solid var(--c); }
.gp .n { width: 190px; height: 190px; border-radius: 50%; display:grid; place-items:center; font-size: 116px; font-weight: 800; color: #02221F; background: var(--c); box-shadow: 0 24px 50px -24px var(--c); }
.gp small { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .16em; color: var(--ink-3); margin-top: 30px; }
.gp b { font-size: 34px; font-weight: 700; letter-spacing: -.01em; margin-top: 8px; }
.gp .co { display:flex; align-items:center; gap: 12px; margin-top: 22px; padding: 12px 22px; border-radius: 999px; background: var(--mint); color: var(--green); font-size: 24px; font-weight: 700; }
''', '''
<div class="mk u" style="--d:.05s">Workshop</div>
<h1 class="mt u" style="--d:.15s">Find your number. <em>Join your group.</em></h1>
<p class="ml u" style="--d:.3s">Your name tag has a number: <b>1, 2 or 3</b>. Sit with your group. Your coach will guide you through every step.</p>
<div class="gp">''' + ''.join('<div class="u" style="--d:%.2fs;--c:%s"><span class="n">%s</span><small>GROUP</small><b>Number %s on your tag</b><span class="co">%sYour coach guides you here</span></div>' % (.5 + k * .15, c, l, l, ic(WG_PERSON, 24, 2)) for k, (l, c) in enumerate(WG_GROUPS)) + '''</div>
''', "\"Before we start the workshop, let's sit in groups. Look at your name tag: you have a number, 1, 2 or 3. Find the table with your number and sit with your group.\n\nEach group has 1 SuDu coach. Your coach will guide you through every step of the workshop, check your answers with you, and tell you where your company should start. Stuck at any point? Raise your hand, and your coach comes to you.\"\n\nDo: coaches stand up and hold up their group number so people can find them. Give 2 minutes to move.\nPrep: give every participant a name tag with 1, 2 or 3 at registration, spread evenly; put a group number card on each table; say each coach's name out loud here.\nNext: \"Everyone with your group? Let's start.\"")

slide('23-readiness-qr', 'Scan: AI readiness', SEC[5], 'light', 'data-sparks="2,1 8,4" style="--gx:22%;--gy:50%;--mx:25%"', '''
.wrap { display:grid; grid-template-columns: 460px 1fr; gap: 130px; align-items:center; height:100%; }
ol { list-style:none; margin-top: 44px; display:grid; gap: 34px; counter-reset: q; }
li { display:grid; grid-template-columns: 76px 1fr; align-items:baseline; font-size: 40px; line-height: 1.25; font-weight: 500; letter-spacing: -.01em; counter-increment: q; }
li::before { content: counter(q); font-family: var(--mono); font-size: 28px; color: var(--green); }
.small { margin-top: 52px; padding-left: 76px; font-size: 28px; }
.qrimg { position:absolute; inset: 62px; width: calc(100% - 124px); height: calc(100% - 124px); image-rendering: pixelated; }
''', '''
<div class="wrap">
  <div class="qr glass pop" style="--d:.2s"><img class="qrimg" src="../assets/qr-readiness.png" alt="AI readiness check QR code"><div class="frame"></div><div class="scan"></div></div>
  <div>
    <h1 class="h1 r" style="--d:.1s">Is your company ready for AI?</h1>
    <p class="lead r" style="--d:.3s;margin-top:22px">Scan and answer 8 questions to see your AI readiness straight away.</p>
    <ol>
      <li class="r" style="--d:.5s">Is your data clean? Item codes, units, stock</li>
      <li class="r" style="--d:.65s">Are your rules clear? Credit limits, price list, who approves</li>
      <li class="r" style="--d:.8s">Are your orders and contacts complete?</li>
    </ol>
  </div>
</div>
''', "\"Take out your phone and scan this QR code. 8 questions about your own company. Answer honestly, it takes a few minutes. Is your data clean? Are your rules clear? Are your orders and contacts complete? When you finish, you see straight away whether your company is ready for AI.\"\n\nDo: coaches help anyone who cannot scan.\nNext: \"Let's go through the questions 1 by 1.\"")

qs = ['Does every item have exactly 1 code?', 'Is the unit fixed for each item: carton, piece or kg?', 'Does the stock in your system match the shelf when you count?', 'Do orders arrive in 1 place, not on 5 phones?',
      'Does every customer have a credit limit and payment term in SQL Account?', 'Is your price list in the system up to date?', 'Is it written down who approves discounts, credit and purchases?', 'Are your customers’ and suppliers’ phone numbers saved in the system?']
q23 = ''.join('<div class="q r" style="--d:%.2fs"><i></i><span class="n">%d</span><span>%s</span></div>' % (0.4 + i * 0.1, i + 1, q) for i, q in enumerate(qs))
slide('23-readiness-check', 'AI readiness check', SEC[5], 'light', 'data-sparks="9,1" style="--gx:90%;--gy:10%;--mx:90%;--my:10%"', '''
.top { display:flex; justify-content:space-between; align-items:flex-start; }
.sub { font-size: 32px; color: var(--ink-2); margin-top: 14px; }
.grid { flex:1; display:grid; grid-template-columns: 1fr 1fr; grid-auto-flow: column; grid-template-rows: repeat(4, 1fr); column-gap: 64px; margin-top: 30px; }
.q { display:grid; grid-template-columns: 52px 46px 1fr; align-items:center; gap: 8px; font-size: 31px; line-height: 1.25; border-bottom: 1px solid var(--line); }
.q i { width: 36px; height: 36px; border: 3px solid var(--ink); border-radius: 8px; background:#fff; }
.q .n { font-family: var(--mono); font-size: 24px; color: var(--green); }
''', '''
<div class="top"><div><h1 class="h1 r" style="--d:.1s">Is your company ready for AI?</h1><p class="sub r" style="--d:.25s">1 point for every yes.</p></div>%s</div>
<div class="grid">%s</div>
''' % (ws(2, 'Score out of 8', '1.3s'), q23),
"\"Worksheet, box 2. Eight questions about your own company. Be honest: nobody sees this but you and your coach. 1 point for every yes.\"\n\nThen, as they work, why each one matters:\n1 One code per item — it cannot tell whether two codes are the same Milo.\n2 Fixed units — \"10\" could mean ten cartons or ten pieces.\n3 System matches shelf — it will promise customers stock you do not have.\n4 Orders in one place — it can only read the chats it is connected to.\n5 Credit limits set — it cannot check a limit that is not there.\n6 Price list up to date — it will quote last year's price.\n7 Approvers written down — it needs to know who to ask.\n8 Phone numbers saved — it cannot message someone it cannot find.\n\nDo: eight minutes to answer, then five minutes to talk at the table. 1 to 3 points: foundation first; 4 to 6: start with the AI Agent; 7 or 8: ready for the whole system.\nNext: \"1 more check: how big does your house need to be?\"")


NEED = [
    ('wms', 'WMS', 'Warehouse', [
        'Do you keep stock in more than 1 warehouse, or across many racks?',
        'Do staff waste time looking for stock?',
        'Do you track batch or expiry dates, or throw away expired stock?',
        'Does your stock count often not match the system?',
        'Do you pick and pack more than 30 orders a day?']),
    ('mes', 'MES', 'Factory', [
        'Do you make, mix or assemble your own products?',
        'Do you issue raw materials by a recipe or BOM?',
        'Is it hard to know how far each job has gone?',
        'Is the real cost or waste of each batch unclear?',
        'Do you plan production on paper or in Excel?']),
]
def _need_col(k, name, sub, qs, d0):
    rows = ''.join('<div class="q r" style="--d:%.2fs"><i></i><span class="n">%d</span><span>%s</span></div>' % (d0 + i * .1, i + 1, q) for i, q in enumerate(qs))
    return ('<div class="nc %s r" style="--d:%.2fs"><div class="hd"><b>%s</b><span>%s</span><em>___ / 5</em></div>%s</div>' % (k, d0 - .2, name, sub, rows))

slide('24-need-wms-mes', 'Do you need WMS and MES?', SEC[5], 'light', 'data-sparks="9,1" style="--gx:90%;--gy:10%;--mx:90%;--my:10%"', '''
.top { display:flex; justify-content:space-between; align-items:flex-start; }
.sub { font-size: 30px; color: var(--ink-2); margin-top: 10px; }
.cols { display:grid; grid-template-columns: 1fr 1fr; gap: 34px; margin-top: 30px; }
.nc { border-radius: 26px; padding: 22px 30px 12px; background: #fff; box-shadow: 0 0 0 1px var(--line), 0 24px 40px -30px rgba(2,34,31,.4); }
.nc .hd { display:flex; align-items:baseline; gap: 14px; padding-bottom: 12px; border-bottom: 3px solid var(--ink); }
.nc .hd b { font-size: 46px; font-weight: 800; letter-spacing: -.02em; }
.nc .hd span { font-size: 26px; color: var(--green); font-weight: 600; }
.nc .hd em { margin-left: auto; font-style: normal; font-family: var(--mono); font-size: 26px; font-weight: 700; color: var(--ink-3); }
.mes .hd { border-color: var(--emerald); }
.q { display:grid; grid-template-columns: 50px 34px 1fr; align-items:center; gap: 6px; font-size: 27px; line-height: 1.28; padding: 13px 0; border-bottom: 1px solid var(--line); }
.q:last-child { border: 0; }
.q i { width: 34px; height: 34px; border: 3px solid var(--ink); border-radius: 8px; background:#fff; }
.q .n { font-family: var(--mono); font-size: 22px; color: var(--green); }
.key { margin-top: 24px; display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.key div { display:flex; align-items:center; gap: 16px; padding: 16px 22px; border-radius: 18px; background: #F1F2F0; }
.key b { font-family: var(--mono); font-size: 28px; font-weight: 700; white-space: nowrap; }
.key span { font-size: 25px; line-height: 1.3; color: var(--ink-2); }
.key .hi { background: var(--ink); color: var(--on-dark); }
.key .hi b { color: var(--neon); } .key .hi span { color: var(--on-dark-2); }
''', '''
<div class="top"><div><h1 class="h1 r" style="--d:.1s">Do you need WMS and MES?</h1><p class="sub r" style="--d:.25s">Tick every yes. Count each side on its own.</p></div>''' + ws('2B', 'Score each side out of 5', '1.6s') + '''</div>
<div class="cols">''' + ''.join(_need_col(k, n, s_, qs, .5 + j * .3) for j, (k, n, s_, qs) in enumerate(NEED)) + '''</div>
<div class="key">
  <div class="r" style="--d:1.9s"><b>0</b><span>SQL Account + AI agents is enough for now.</span></div>
  <div class="r" style="--d:2.05s"><b>1 to 2</b><span>Start with AI agents. Add it later.</span></div>
  <div class="hi r" style="--d:2.2s"><b>3 to 5</b><span>You need it. Plan it from day 1.</span></div>
</div>
''',
"\"First question for your company: how big does the house need to be? 2 short lists, 5 questions each. Tick every yes, and count each side on its own.\n\nWMS, the warehouse: more than 1 warehouse or many racks; staff wasting time looking for stock; batch or expiry dates, or stock thrown away because it expired; a stock count that does not match the system; more than 30 orders a day to pick and pack. Every yes is a problem a WMS fixes.\n\nMES, the factory: you make, mix or assemble your own products; you issue raw materials by a recipe or BOM; you cannot tell how far a job has gone; the real cost or waste of each batch is unclear; you plan production on paper or in Excel.\n\nScore: 0, SQL Account plus AI agents is enough for now. 1 or 2, start with the agents and add it later. 3 or more, you need it, so plan it from day 1.\n\nIf you do not make anything, skip the MES side: it is 0.\"\n\nDo: coaches note both scores on the lead sheet next to the readiness score.\nNext: \"So how do you start? Just 3 steps.\"")



# ============================================================ 6 · HOW TO START

slide('28-what-it-gives-back', 'Manual work cost', SEC[6], 'light', 'data-sparks="9,0" style="--gx:30%;--gy:60%;--mx:30%;--my:60%"', '''
.slide { padding-top: 96px; }
.h1 { font-size: 80px; margin-top: 14px; }
.h1 em { font-style: normal; color: #B4451F; }
.wrap { flex:1; display:grid; grid-template-columns: 1fr 520px; gap: 40px; margin-top: 44px; min-height: 0; }
.tb { padding: 30px 40px 26px; display:flex; flex-direction:column; }
.tr { display:grid; grid-template-columns: 76px 1fr 110px 150px 190px; align-items:center; gap: 18px; padding: 16px 0; border-bottom: 1px solid var(--line); }
.tr.h { padding: 0 0 12px; font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .1em; color: var(--ink-3); }
.tr .ic { width: 64px; height: 64px; border-radius: 18px; background: rgba(255,138,91,.14); color: #B4451F; display:grid; place-items:center; }
.tr .ic svg { width: 34px; height: 34px; }
.tr b { display:block; font-size: 32px; font-weight: 750; letter-spacing: -.02em; }
.tr small { display:block; font-size: 22px; color: var(--ink-3); margin-top: 2px; }
.tr .n { font-size: 30px; font-weight: 650; text-align:right; color: var(--ink-2); }
.tr .rm { font-size: 34px; font-weight: 750; text-align:right; letter-spacing: -.02em; }
.tr.t { border: 0; margin-top: auto; padding-top: 20px; border-top: 3px solid var(--ink); }
.tr.t b, .tr.t .n, .tr.t .rm { color: var(--ink); font-weight: 800; }
.tr.t .rm { color: #B4451F; font-size: 40px; }
.sd { border-radius: 34px; background: var(--ink); color: var(--on-dark); padding: 44px 46px; display:flex; flex-direction:column; box-shadow: 0 40px 80px -40px rgba(2,34,31,.7); }
.sd .k { font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .14em; color: #FFB08F; }
.sd .yr { font-size: 80px; font-weight: 800; letter-spacing: -.05em; line-height: 1; margin-top: 16px; }
.sd .yr small { display:block; font-size: 28px; font-weight: 600; letter-spacing: 0; color: var(--on-dark-2); margin-top: 10px; }
.sd .eq { margin-top: 30px; padding-top: 26px; border-top: 1px solid rgba(242,251,247,.16); font-size: 30px; line-height: 1.45; color: var(--on-dark-2); }
.sd .eq b { color: var(--on-dark); font-weight: 750; }
.sd .ppl { display:flex; gap: 10px; margin-top: auto; }
.sd .ppl i { width: 46px; height: 46px; border-radius: 50%; background: rgba(255,138,91,.2); color: #FFB08F; display:grid; place-items:center; }
.note { margin-top: 16px; font-size: 21px; color: var(--ink-3); }
.sd .eq b:lang(en) { margin-right: .25em; }
''', '''
<div class="kicker r" style="--d:.05s">Your manual work cost</div>
<h1 class="h1 r" style="--d:.1s">Manual work, every month: <em>RM<span data-count="25556" data-delay=".9" data-dur="1.6">0</span></em></h1>
<div class="wrap">
  <div>
    <div class="glass tb r" style="--d:.3s">
      <div class="tr h"><span></span><span>Team · manual work</span><span style="text-align:right">Staff</span><span style="text-align:right">Hrs / month</span><span style="text-align:right">Cost / month</span></div>
      <div class="tr r" style="--d:.5s"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/></svg></span><div><b>Sales</b><small>Keying in orders, replying to customers</small></div><span class="n">3</span><span class="n">519 h</span><span class="rm">RM10,350</span></div>
      <div class="tr r" style="--d:.62s"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12v18l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21z"/><path d="M9 8h6M9 11.5h6M9 15h4"/></svg></span><div><b>Finance</b><small>Invoices, chasing payments, reconciling</small></div><span class="n">2</span><span class="n">346 h</span><span class="rm">RM7,820</span></div>
      <div class="tr r" style="--d:.74s"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h2.5l2.2 10.5h10.8L21 7H7"/><circle cx="9.5" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/></svg></span><div><b>Purchasing</b><small>POs, chasing deliveries, keying in supplier invoices</small></div><span class="n">1</span><span class="n">173 h</span><span class="rm">RM3,680</span></div>
      <div class="tr r" style="--d:.86s"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7.5L12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/></svg></span><div><b>Stock</b><small>Checking stock, making reports</small></div><span class="n">1</span><span class="n">173 h</span><span class="rm">RM3,706</span></div>
      <div class="tr t r" style="--d:1s"><span></span><b>Total</b><span class="n">7</span><span class="n">1,211 h</span><span class="rm">RM25,556</span></div>
    </div>
    <p class="note r" style="--d:1.3s">Estimate: a wholesaler with about 80 orders a day, incl. EPF and SOCSO. Yours will differ.</p>
  </div>
  <div class="sd r" style="--d:.7s">
    <span class="k">Over a year</span>
    <div class="yr">RM306,672<small>spent on typing, chasing and checking stock</small></div>
    <p class="eq">That is <b>7 full-time staff</b>doing the same manual work every day.</p>
    <div class="ppl"><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i><i><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg></i></div>
  </div>
</div>
''', "\"First, the cost of manual work. Take a wholesaler with about 80 orders a day. Sales: 3 people key in orders and reply to customers, 519 hours a month, costing RM10,350. Finance: 2 people do invoices, chase payments and reconcile, 346 hours, RM7,820. Purchasing: 1 person does POs, chases deliveries and keys in supplier invoices, RM3,680. Stock: 1 person checks stock and makes reports, RM3,706.\n\nAdded up: 7 people, 1,211 hours a month, costing RM25,556. That is RM306,672 a year, spent on the same manual work. Now look at the staff cost you worked out yourself, and compare.\"\n\nNote: this is an estimate; monthly cost includes EPF and SOCSO. Say \"estimate\" out loud.\nNext: \"And with AI?\"")

slide('28-cost-compare', 'Manual vs AI cost', SEC[6], 'light', 'data-sparks="9,0" style="--gx:80%;--gy:50%;--mx:80%;--my:50%"', '''
.slide { padding-top: 96px; }
.h1 { font-size: 80px; margin-top: 14px; }
.h1 em { font-style: normal; color: var(--green); }
.wrap { flex:1; display:grid; grid-template-columns: 1fr 560px; gap: 40px; margin-top: 46px; min-height: 0; }
.wrap > div:first-child { display:flex; flex-direction:column; }
.cmp { flex:1; display:flex; flex-direction:column; gap: 26px; }
.cmp .row { flex:1; display:flex; flex-direction:column; justify-content:center; }
.row { padding: 30px 36px; border-radius: 30px; }
.row .hd { display:flex; align-items:baseline; justify-content:space-between; gap: 20px; }
.row h3 { font-size: 36px; font-weight: 750; letter-spacing: -.02em; }
.row h3 small { font-size: 24px; font-weight: 500; color: var(--ink-3); margin-left: 12px; }
.row .tot { font-size: 64px; font-weight: 800; letter-spacing: -.04em; line-height: 1; }
.row .tot small { font-size: 26px; font-weight: 600; letter-spacing: 0; color: var(--ink-3); margin-left: 6px; }
.bar { display:flex; height: 56px; border-radius: 14px; overflow:hidden; margin-top: 22px; background: #EEF1EF; }
.bar i { display:flex; align-items:center; padding: 0 16px; font-style: normal; font-size: 21px; font-weight: 700; white-space: nowrap; transform-origin: left; animation: grow 1.4s cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--d); }
@keyframes grow { from { transform: scaleX(0); } }
html.static .bar i { animation: none; }
.man .tot { color: #B4451F; }
.man .bar i { background: #FF8A5B; color: #1A0F0A; }
.ai .bar i.s { background: var(--ink); color: var(--neon); }
.ai .bar i.h { background: var(--emerald); color: #fff; }
.ai .tot { color: var(--green); }
.lines { display:flex; gap: 26px; flex-wrap: wrap; margin-top: 16px; font-size: 24px; color: var(--ink-2); }
.lines b { color: var(--ink); font-weight: 700; }
/* savings */
.sv { border-radius: 34px; background: var(--ink); color: var(--on-dark); padding: 44px 46px; display:flex; flex-direction:column; box-shadow: 0 40px 80px -40px rgba(2,34,31,.7), 0 0 100px rgba(0,245,169,.2); }
.sv .k { font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .14em; color: var(--neon); }
.sv .pc { font-size: 170px; font-weight: 800; letter-spacing: -.06em; line-height: .95; color: var(--neon); margin-top: 14px; }
.sv .pc small { font-size: 48px; letter-spacing: -.02em; color: var(--on-dark); margin-left: 10px; }
.sv .yr { margin-top: 26px; padding-top: 24px; border-top: 1px solid rgba(242,251,247,.16); }
.sv .yr b { display:block; font-size: 66px; font-weight: 800; letter-spacing: -.04em; line-height: 1; }
.sv .yr span { display:block; font-size: 26px; color: var(--on-dark-2); margin-top: 8px; }
.sv .pb { margin-top: auto; display:flex; align-items:center; gap: 14px; font-size: 24px; font-weight: 650; padding: 16px 20px; border-radius: 16px; background: rgba(0,245,169,.12); }
.sv .pb svg { flex:none; color: var(--neon); }
.note { margin-top: 18px; font-size: 21px; color: var(--ink-3); }
''', '''
<div class="kicker r" style="--d:.05s">Compare the cost</div>
<h1 class="h1 r" style="--d:.1s">Manual vs AI, monthly saving: <em>RM<span data-count="23556" data-delay="1.6" data-dur="1.4">0</span></em></h1>
<div class="wrap">
  <div>
    <div class="cmp">
      <div class="glass row man r" style="--d:.35s">
        <div class="hd"><h3>Manual<small>7 people · 1,211 hours</small></h3><div class="tot">RM25,556<small>/ month</small></div></div>
        <div class="bar"><i style="width:100%;--d:.7s">The cost of 7 full-time staff</i></div>
        <div class="lines"><span>Sales <b>RM10,350</b></span><span>Finance <b>RM7,820</b></span><span>Purchasing <b>RM3,680</b></span><span>Stock <b>RM3,706</b></span></div>
      </div>
      <div class="glass row ai r" style="--d:.55s">
        <div class="hd"><h3>With SuDu AI<small>AI works, people approve</small></h3><div class="tot">RM2,000<small>/ month</small></div></div>
        <div class="bar"><i class="s" style="width:7.83%;--d:1s"></i></div>
        <div class="lines"><span>SuDu AI plan <b>RM2,000 / month</b></span><span>Staff move to <b>serving customers and growing sales</b></span></div>
      </div>
    </div>
    <p class="note r" style="--d:1.4s">Estimate: a wholesaler with about 80 orders a day, incl. EPF and SOCSO (previous slide). Yours will differ.</p>
  </div>
  <div class="sv r" style="--d:.8s">
    <span class="k">Monthly cost cut by</span>
    <div class="pc">92%<small>↓</small></div>
    <div class="yr"><b>≈ RM282,672</b><span>saved in a year</span></div>
    <div class="pb"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/></svg>The setup fee pays for itself in under 1 month</div>
  </div>
</div>
''', "\"Manual: RM25,556 a month. With SuDu AI: RM2,000 a month. The AI does the daily work, people only approve.\n\nYou save RM23,556 a month, a 92% cut in cost. That is about RM282,672 a year. The setup fee pays for itself in under 1 month. And the people you free up can move to serving customers and growing sales.\"\n\nNote: this is an estimate, using the manual cost on the previous slide and a RM2,000 a month plan (Pro); say \"estimate\" out loud. It does not yet count what HRDF can cover.\nNext: \"Here are the plans.\"")

plans = [('Basic', 'RM850', 'RM9,500', 'runs daily jobs: chasing payments, morning checks'), ('Standard', 'RM1,200', 'RM12,000', 'takes customer orders on WhatsApp'),
         ('Pro', 'RM2,000', 'RM19,000', 'group companies and more warehouse work'), ('Max', 'RM3,500', 'RM35,000', 'everything, with your own SuDu contact person')]
p29 = ''.join('<tr class="%s r" style="--d:%.2fs"><td><b>%s</b>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %
              ('on' if n == 'Standard' else '', 0.45 + i * 0.1, n, ' <span class="tag">Most start here</span>' if n == 'Standard' else '', m, s, a) for i, (n, m, s, a) in enumerate(plans))
slide('29-plans', 'Plans and prices', SEC[6], 'light', 'data-sparks="9,1" style="--gx:85%;--gy:20%;--mx:85%;--my:20%"', '''
table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 44px; font-size: 30px; table-layout: fixed; }
th:nth-child(1) { width: 420px; } th:nth-child(2) { width: 210px; } th:nth-child(3) { width: 240px; }
th { white-space: nowrap; }
th { font-family: var(--mono); font-size: 20px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-3); text-align:left; font-weight: 600; padding: 0 28px 16px; border-bottom: 2px solid var(--ink); }
td { padding: 19px 28px; border-bottom: 1px solid var(--line); color: var(--ink-2); }
td:nth-child(2), td:nth-child(3) { font-feature-settings: "tnum"; color: var(--ink); white-space: nowrap; }
td b { color: var(--ink); font-weight: 650; }
tr.on td { background: var(--ink); color: var(--on-dark-2); border-color: var(--ink); }
tr.on td b, tr.on td:nth-child(2), tr.on td:nth-child(3) { color: var(--on-dark); }
tr.on td:first-child { border-radius: 18px 0 0 18px; } tr.on td:last-child { border-radius: 0 18px 18px 0; }
.tag { white-space: nowrap; font-size: 18px; font-family: var(--mono); letter-spacing: .06em; color: var(--ink); background: var(--neon); padding: 5px 10px; border-radius: 8px; margin-left: 12px; vertical-align: 3px; font-weight: 600; }
.note { font-size: 26px; color: var(--ink-3); margin-top: 26px; }
''', '''
<h1 class="h1 r" style="--d:.1s">Plans</h1>
<table><tr class="f" style="--d:.2s"><th>Plan</th><th>Per month</th><th>Setup, 1x</th><th>The agent…</th></tr>%s</table>
<p class="note f" style="--d:1.1s">Billed yearly. Standard is where most companies start.</p>
''' % p29,
"\"4 plans, starting from Basic, and I will make it simple. Most companies in this room should start at [recommended plan]. Compare the yearly price with the number in your box 1.\"\n\nTO CONFIRM: the highlighted row is Standard because taking WhatsApp orders, as shown in the demo, starts there. Change it if you pick another plan. Check prices are current.\nNext: \"And the fees are HRDF claimable.\"")

slide('29-plan-details', 'Plan details', SEC[6], 'light', 'data-sparks="9,0" style="--gx:85%;--gy:20%;--mx:85%;--my:20%"', '''
.slide { padding-top: 88px; }
.h1 { font-size: 76px; margin-top: 12px; }
.h1 em { font-style: normal; color: var(--green); }
.sub { font-size: 29px; color: var(--ink-2); margin-top: 14px; }
.pl { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 26px; margin-top: 48px; }
.pc { position:relative; display:flex; flex-direction:column; padding: 30px 30px 22px; border-radius: 30px; }
.pc h3 { font-size: 40px; font-weight: 800; letter-spacing: -.02em; color: var(--green); }
.pc .for { font-size: 21px; line-height: 1.35; color: var(--ink-3); margin-top: 8px; min-height: 58px; }
.pc .pr { margin-top: 16px; font-size: 62px; font-weight: 800; letter-spacing: -.04em; line-height: 1; color: var(--ink); font-feature-settings: "tnum"; white-space: nowrap; }
.pc .pr small { font-size: 23px; font-weight: 600; letter-spacing: 0; color: var(--ink-3); margin-left: 6px; }
.pc .su { font-size: 20px; color: var(--ink-3); margin-top: 10px; }
.pc dl { margin-top: 18px; border-top: 1px solid var(--line); }
.pc dl div { display:flex; justify-content:space-between; align-items:baseline; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
.pc dt { font-size: 21px; color: var(--ink-2); white-space: nowrap; }
.pc dd { font-size: 23px; font-weight: 800; color: var(--ink); white-space: nowrap; font-feature-settings: "tnum"; }
.pc dd.tk { font-size: 34px; color: var(--green); }
.pc.on { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--neon), 0 50px 80px -40px rgba(0,108,72,.6); }
.pc.on h3, .pc.on dd.tk { color: var(--neon); }
.pc.on .for, .pc.on .su, .pc.on .pr small { color: var(--on-dark-3); }
.pc.on .pr, .pc.on dd { color: var(--on-dark); } .pc.on dt { color: var(--on-dark-2); }
.pc.on dl, .pc.on dl div { border-color: rgba(242,251,247,.14); }
.pc .tag { position:absolute; right: 24px; top: -17px; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .06em; padding: 6px 10px; border-radius: 8px; background: var(--neon); color: var(--ink); white-space: nowrap; }
.note { margin-top: auto; font-size: 21px; color: var(--ink-3); }
''', '''
<div class="kicker r" style="--d:.05s">Plan details</div>
<h1 class="h1 r" style="--d:.15s">What each plan <em>includes</em></h1>
<p class="sub r" style="--d:.3s">Billed yearly. Every plan links free to SQL Account, on web and mobile.</p>
<div class="pl"><div class="pc glass r" style="--d:0.45s"><h3>Basic</h3><p class="for">AI Sales Agent: quotes, orders and invoices</p><div class="pr">RM<span data-count="850" data-delay="0.9" data-dur="1.2">0</span><small>/month</small></div><p class="su">+ RM9,500 setup, 1x</p><dl><div><dt>AI tokens / month</dt><dd class="tk"><span data-count="2000" data-delay="1.1" data-dur="1.4">0</span></dd></div><div><dt>Tasks / month</dt><dd>&asymp; 2,000 &ndash; 3,000</dd></div><div><dt>AI system users</dt><dd>5</dd></div><div><dt>WhatsApp numbers</dt><dd>1</dd></div></dl></div><div class="pc on r" style="--d:0.60s"><span class="tag">Most start here</span><h3>Standard</h3><p class="for">Sales, stock and reports, automated</p><div class="pr">RM<span data-count="1200" data-delay="1.1" data-dur="1.2">0</span><small>/month</small></div><p class="su">+ RM12,000 setup, 1x</p><dl><div><dt>AI tokens / month</dt><dd class="tk"><span data-count="3000" data-delay="1.3" data-dur="1.4">0</span></dd></div><div><dt>Tasks / month</dt><dd>&asymp; 3,000 &ndash; 4,000</dd></div><div><dt>AI system users</dt><dd>10</dd></div><div><dt>WhatsApp numbers</dt><dd>1</dd></div></dl></div><div class="pc glass r" style="--d:0.75s"><h3>Pro</h3><p class="for">Adds payment receipt, credit notes and approvals</p><div class="pr">RM<span data-count="2000" data-delay="1.2" data-dur="1.2">0</span><small>/month</small></div><p class="su">+ RM19,000 setup, 1x</p><dl><div><dt>AI tokens / month</dt><dd class="tk"><span data-count="5000" data-delay="1.4" data-dur="1.4">0</span></dd></div><div><dt>Tasks / month</dt><dd>&asymp; 5,000 &ndash; 6,000</dd></div><div><dt>AI system users</dt><dd>20</dd></div><div><dt>WhatsApp numbers</dt><dd>3</dd></div></dl></div><div class="pc glass r" style="--d:0.90s"><h3>Enterprise</h3><p class="for">Full operations: procurement, reorder and BOM</p><div class="pr">RM<span data-count="3500" data-delay="1.4" data-dur="1.2">0</span><small>/month</small></div><p class="su">+ RM35,000 setup, 1x</p><dl><div><dt>AI tokens / month</dt><dd class="tk"><span data-count="10000" data-delay="1.6" data-dur="1.4">0</span></dd></div><div><dt>Tasks / month</dt><dd>&asymp; 10,000 &ndash; 12,000</dd></div><div><dt>AI system users</dt><dd>30</dd></div><div><dt>WhatsApp numbers</dt><dd>5</dd></div></dl></div></div>
<p class="note f" style="--d:1.6s">Task counts are estimates: heavier jobs, like a full order chat, use more tokens.</p>
''',
"\"Here is what each plan includes. Every plan gives you a monthly allowance of AI tokens; 1 token covers 1 task or a little more, depending on the job.\n\nBasic, RM850 a month: 2,000 tokens, about 2,000 to 3,000 tasks, 5 AI system users and 1 WhatsApp number.\n\nStandard, where most companies start: RM1,200 a month, 3,000 tokens, 10 users, 1 WhatsApp number. Pro: RM2,000, 5,000 tokens, 20 users and 3 WhatsApp numbers. Enterprise: RM3,500, 10,000 tokens, 30 users and 5 WhatsApp numbers.\n\nAll plans are billed yearly with a one-off setup fee, and every plan links to SQL Account for free.\"\n\nNext: \"And if a busy month uses up your tokens?\"")

slide('29-flexi-tokens', 'Flexi token top-ups', SEC[6], 'light', 'data-sparks="9,0" style="--gx:80%;--gy:25%;--mx:80%;--my:30%"', '''
.slide { padding-top: 88px; }
.h1 { font-size: 76px; margin-top: 12px; }
.h1 em { font-style: normal; color: var(--green); }
.sub { font-size: 29px; color: var(--ink-2); margin-top: 14px; }
.wrap { display:grid; grid-template-columns: 1fr 560px; gap: 40px; margin-top: 42px; }
.packs { display:grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.pk { padding: 34px 20px 30px; border-radius: 28px; text-align:center; }
.pk .am { font-size: 74px; font-weight: 800; letter-spacing: -.04em; line-height: 1; font-feature-settings: "tnum"; }
.pk .ts { font-size: 26px; font-weight: 750; color: var(--green); margin-top: 16px; white-space: nowrap; }
.pk .ot { font-size: 20px; color: var(--ink-3); margin-top: 6px; }
.pk.on { background: var(--ink); color: var(--on-dark); box-shadow: 0 0 0 3px var(--neon), 0 50px 80px -40px rgba(0,108,72,.6); }
.pk.on .ts { color: var(--neon); } .pk.on .ot { color: var(--on-dark-3); }
.lv { margin-top: 30px; }
.lv h4 { font-family: var(--mono); font-size: 18px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--green); }
.lv .row { display:grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-top: 14px; }
.lv .row div { padding: 18px 22px; border-radius: 20px; background: #fff; box-shadow: 0 0 0 1px var(--line); }
.lv .row i { display:flex; gap: 6px; margin-bottom: 10px; }
.lv .row s { width: 14px; height: 14px; border-radius: 50%; background: var(--emerald); } .lv .row s.o { background: var(--mint); }
.lv b { display:block; font-size: 26px; font-weight: 800; }
.lv span { display:block; font-size: 20px; line-height: 1.3; color: var(--ink-3); margin-top: 4px; }
.cb { display:flex; gap: 18px; align-items:center; margin-top: 26px; padding: 20px 26px; border-radius: 22px; background: var(--mint); font-size: 23px; line-height: 1.4; color: var(--ink-2); }
.cb i { flex:none; width: 46px; height: 46px; border-radius: 50%; background: var(--ink); color: var(--neon); display:grid; place-items:center; font-style: normal; font-weight: 800; font-size: 26px; }
.cb b { color: var(--ink); }
.hw { padding: 32px 34px 30px; border-radius: 30px; display:flex; flex-direction:column; }
.hw h3 { font-size: 32px; font-weight: 800; letter-spacing: -.02em; }
.hw dl { margin-top: 12px; }
.hw dl div { display:flex; justify-content:space-between; align-items:baseline; gap: 16px; padding: 17px 0; border-bottom: 1px solid var(--line); }
.hw dt { font-size: 22px; color: var(--ink-2); }
.hw dd { font-size: 22px; font-weight: 800; text-align:right; }
.hw dd.g { color: var(--green); }
.hw p { font-size: 21px; line-height: 1.42; color: var(--ink-3); margin-top: auto; padding-top: 20px; }
''', '''
<div class="kicker r" style="--d:.05s">If tokens run out</div>
<h1 class="h1 r" style="--d:.15s">Busy month? <em>Top up</em> with Flexi</h1>
<p class="sub r" style="--d:.3s">Every plan includes monthly tokens. Top up only in the months that run hot.</p>
<div class="wrap">
<div>
<div class="packs"><div class="pk glass pop" style="--d:0.45s"><div class="am">RM<span data-count="100" data-delay="0.8" data-dur="1">0</span></div><div class="ts">&asymp; 220 &ndash; 330 tasks</div><div class="ot">one-time top-up</div></div><div class="pk on pop" style="--d:0.60s"><div class="am">RM<span data-count="300" data-delay="0.9" data-dur="1">0</span></div><div class="ts">&asymp; 660 &ndash; 1,000 tasks</div><div class="ot">one-time top-up</div></div><div class="pk glass pop" style="--d:0.75s"><div class="am">RM<span data-count="500" data-delay="1.1" data-dur="1">0</span></div><div class="ts">&asymp; 1,100 &ndash; 1,650 tasks</div><div class="ot">one-time top-up</div></div></div>
<div class="lv r" style="--d:1s"><h4>What counts as a task</h4><div class="row"><div><i><s></s><s class="o"></s><s class="o"></s></i><b>Light</b><span>Quick answer or reminder</span></div><div><i><s></s><s></s><s class="o"></s></i><b>Medium</b><span>Create a document or report</span></div><div><i><s></s><s></s><s></s></i><b>Heavy</b><span>A full order chat, from enquiry to Sales Order</span></div></div></div>
<div class="cb r" style="--d:1.3s"><i>!</i><span><b>No surprise bills.</b> You get an alert before your tokens run low. Nothing is charged automatically.</span></div>
</div>
<div class="hw glass r" style="--d:.8s"><h3>How top-ups work</h3><dl><div><dt>Unused monthly tokens</dt><dd>Reset next month</dd></div><div><dt>Flexi pack</dt><dd>One-time, on demand</dd></div><div><dt>Auto-charge</dt><dd class="g">Never</dd></div><div><dt>Low-balance alert</dt><dd class="g">Included</dd></div></dl><p>If usage stays high every month, moving up a plan costs less than buying packs.</p></div>
</div>
''',
"\"Peak season, a promotion, a big collections push: some months use more. Then you buy a Flexi top-up. RM100 gives about 220 to 330 tasks, RM300 about 660 to 1,000, RM500 about 1,100 to 1,650. It is one-time, only when you need it.\n\nA light task is a quick answer or a reminder. A heavy one is a full order chat, from enquiry to Sales Order. That is why the counts are a range.\n\nNo surprise bills: you get an alert before your tokens run low, and nothing is charged automatically. Unused monthly tokens reset next month. And if you top up every month, moving up a plan costs less.\"\n\nNext: \"So what does manual work really cost you today?\"")

slide('29-hrdf', 'HRDF Claimable', SEC[6], 'light', 'data-sparks="9,0 1,5" style="--gx:80%;--gy:25%;--mx:80%;--my:30%"', '''
.slide { padding-top: 96px; }
.h1 { font-size: 104px; line-height: 1; letter-spacing: -.04em; margin-top: 18px; }
.sub { font-size: 40px; font-weight: 650; color: var(--ink-2); margin-top: 22px; }
.sub em { font-style: normal; color: var(--green); }
.row { flex:1; display:grid; grid-template-columns: 1fr 210px 1fr 96px 1fr; align-items: stretch; margin-top: 52px; margin-bottom: 10px; }
.cd { padding: 40px 38px 42px; border-radius: 34px; display:flex; flex-direction:column; align-items:flex-start; }
.cd .lg { width: 220px; height: 220px; border-radius: 50%; background: #fff; display:grid; place-items:center; box-shadow: 0 0 0 1px var(--line), 0 24px 40px -26px rgba(2,34,31,.45); }
.cd .lg img { width: 192px; height: 192px; object-fit: contain; }
.cd small { font-family: var(--mono); font-size: 20px; font-weight: 700; letter-spacing: .14em; color: var(--green); margin-top: auto; }
.cd b { display:block; font-size: 44px; font-weight: 750; letter-spacing: -.025em; line-height: 1.15; margin-top: 10px; }
.cd p { font-size: 26px; line-height: 1.4; color: var(--ink-2); margin-top: 10px; }
/* connectors between cards */
.go { display:flex; flex-direction:column; align-items:center; justify-content:center; gap: 14px; text-align:center; }
.go span { font-size: 25px; font-weight: 750; line-height: 1.3; color: var(--green); padding: 10px 14px; border-radius: 14px; background: var(--mint); }
.go svg { width: 150px; height: 40px; color: var(--green); overflow: visible; }
.go svg path { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw .9s var(--ease) forwards; animation-delay: var(--d, 0s); }
.plus { display:grid; place-items:center; }
.plus i { font-style: normal; width: 60px; height: 60px; border-radius: 50%; background: var(--ink); color: var(--neon); display:grid; place-items:center; font-size: 40px; font-weight: 700; line-height: 1; }
/* the deal: dark card, neon accent */
.cd.hi .ic { width: 112px; height: 112px; border-radius: 30px; display:grid; place-items:center; background: rgba(0,245,169,.14); color: var(--neon); }
.cd.hi .ic svg { width: 60px; height: 60px; }
.cd.hi .es { width: 100%; height: 220px; border-radius: 28px; background: #fff; display:grid; place-items:center; box-shadow: 0 0 0 1px var(--line), 0 24px 40px -26px rgba(2,34,31,.45); }
.cd.hi .es img { width: 86%; height: 170px; object-fit: contain; }
.cd.hi .es .wm { display:flex; flex-direction:column; align-items:center; gap: 6px; }
.cd.hi .es .wm b { margin: 0; font-size: 64px; font-weight: 800; letter-spacing: .02em; color: var(--ink); }
.cd.hi .es .wm small { margin: 0; font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .2em; color: var(--green); }
.cd.hi .ph { color: var(--neon); }
''', '''
<div class="kicker r" style="--d:.05s">Training grant</div>
<h1 class="h1 r" style="--d:.15s">HRDF Claimable</h1>
<p class="sub r" style="--d:.3s"><em>ESTREAM (SQL HQ)</em> exclusive offer, HRDF claimable</p>
<div class="row">
  <div class="glass cd r" style="--d:.55s">
    <span class="lg pop" style="--d:.9s"><img src="../assets/logos/hrdcorp-registered-tp.png" alt="HRD Corp Registered Training Provider logo"></span>
    <small>ESTREAM (SQL HQ)</small><b>Authorised Training Provider</b><p>A training provider registered with HRD Corp.</p></div>
  <div class="go f" style="--d:1.1s"><span>ESTREAM helps you<br>claim HRDF</span>
    <svg viewBox="0 0 150 40" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path pathLength="1" style="--d:1.2s" d="M8 20 H140 M124 6 L140 20 L124 34"/></svg></div>
  <div class="glass cd r" style="--d:.75s">
    <span class="lg pop" style="--d:1.1s"><img src="../assets/logos/hrdcorp-claimable.png" alt="HRD Corp Claimable logo"></span>
    <small>HRDF</small><b>HRDF Claimable</b><p>Eligible companies can claim the HRD Corp grant.</p></div>
  <div class="plus f" style="--d:1.4s"><i>+</i></div>
  <div class="glass cd hi r" style="--d:.95s">
    <span class="es pop" style="--d:1.3s"><span class="wm"><b>ESTREAM</b><small>SQL HQ</small></span></span>
    <b style="margin-top:auto">ESTREAM exclusive offer</b><p>ESTREAM customers get extra discounts!</p></div>
</div>
''', "\"One more piece of good news: an ESTREAM exclusive offer, and it is HRDF claimable. ESTREAM, SQL HQ, is an Authorised Training Provider registered with HRD Corp. ESTREAM helps you apply, and eligible companies can claim HRDF. On top of that, there is an ESTREAM exclusive offer today.\"\n\nTO CONFIRM: which fees can be claimed under HRDF.\nNext: \"So here is your next step.\"")

slide('30-live-in-30-days', 'Onboarding', SEC[6], 'light', 'data-sparks="9,0" style="--gx:78%;--gy:40%;--mx:70%;--my:40%"', '''
.slide { padding-top: 96px; }
.h1 { font-size: 80px; margin-top: 14px; }
.h1 em { font-style: normal; color: var(--green); }
.steps { flex:1; display:grid; grid-template-columns: 1fr 64px 1fr 64px 1fr; align-items: stretch; margin-top: 50px; margin-bottom: 6px; }
.st { position:relative; padding: 40px 40px 38px; border-radius: 34px; display:flex; flex-direction:column; overflow:hidden; }
.st .big { position:absolute; right: 22px; top: -30px; font-size: 250px; font-weight: 800; letter-spacing: -.06em; line-height: 1; color: rgba(2,34,31,.045); pointer-events:none; }
.st .tp { display:flex; align-items:center; gap: 18px; }
.st .ic { flex:none; width: 92px; height: 92px; border-radius: 26px; display:grid; place-items:center; background: var(--mint); color: var(--green); }
.st .ic svg { width: 50px; height: 50px; }
.st .k { font-family: var(--mono); font-size: 22px; font-weight: 700; letter-spacing: .14em; color: var(--green); }
.st h3 { font-size: 52px; font-weight: 750; letter-spacing: -.03em; line-height: 1.1; margin-top: 26px; }
.st .en { align-self:flex-start; display:inline-block; margin-top: 12px; font-size: 24px; font-weight: 700; padding: 6px 14px; border-radius: 10px; background: var(--mint); color: var(--green); }
.st p { font-size: 27px; line-height: 1.45; color: var(--ink-2); margin-top: 20px; }
.st ul { list-style:none; margin-top: auto; padding-top: 22px; border-top: 1px solid var(--line); display:grid; gap: 12px; }
.st li { display:flex; align-items:center; gap: 12px; font-size: 26px; font-weight: 650; color: var(--ink); }
.st li svg { flex:none; color: var(--emerald); }
.ar { display:grid; place-items:center; color: var(--green); }
.ar svg { width: 46px; height: 46px; }
/* step 3: the payoff, dark */
.st.go { background: var(--ink); color: var(--on-dark); box-shadow: 0 40px 80px -40px rgba(2,34,31,.7), 0 0 100px rgba(0,245,169,.18); }
.st.go .big { color: rgba(0,245,169,.08); }
.st.go .ic { background: rgba(0,245,169,.14); color: var(--neon); }
.st.go .k { color: var(--neon); }
.st.go .en { background: rgba(0,245,169,.14); color: var(--neon); }
.st.go p { color: var(--on-dark-2); }
.st.go ul { border-color: rgba(242,251,247,.14); }
.st.go li { color: var(--on-dark); } .st.go li svg { color: var(--neon); }
''', '''
<div class="kicker r" style="--d:.05s">Onboarding</div>
<h1 class="h1 r" style="--d:.1s"><em>3</em> steps to start using your AI</h1>
<div class="steps">
  <div class="glass st r" style="--d:.35s"><span class="big">1</span>
    <div class="tp"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 7V3M15 7V3M7 7h10v4a5 5 0 01-10 0z"/><path d="M12 16v5"/></svg></span><span class="k">STEP 1</span></div>
    <h3>AI setup</h3><span class="en">SQL Integration</span>
    <p>The SuDu sync tool connects SQL Account safely. Customers, items, prices, stock and credit limits sync on their own, and nothing writes straight into your database.</p>
    <ul><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Connect SQL Account</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Sync customers, items and prices</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Set permissions and approvers</li></ul>
  </div>
  <div class="ar f" style="--d:.9s"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div>
  <div class="glass st r" style="--d:.6s"><span class="big">2</span>
    <div class="tp"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 012-2h12v16H6a2 2 0 00-2 2z"/><path d="M4 19V5M8 7h6M8 11h6"/></svg></span><span class="k">STEP 2</span></div>
    <h3>Train the AI</h3><span class="en">Skill / SOP · Item Code</span>
    <p>Like teaching a new staff member: write your way of working as Skills and SOPs. Then teach it your customers&rsquo; words: which item code in your system is &ldquo;bwg besar&rdquo;.</p>
    <ul><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Write down Skills and SOPs</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Match item codes</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Test with last month&rsquo;s orders</li></ul>
  </div>
  <div class="ar f" style="--d:1.1s"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div>
  <div class="st go r" style="--d:.85s"><span class="big">3</span>
    <div class="tp"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2"/><path d="M9 15l-3-3c1-4 4-8 9-9 2 0 3 0 3 0s0 1 0 3c-1 5-5 8-9 9z"/><circle cx="14.5" cy="9.5" r="1.5"/></svg></span><span class="k">STEP 3</span></div>
    <h3>Start using your AI</h3><span class="en">Go Live</span>
    <p>The AI takes orders, chases payments, checks stock and makes reports. At first it only drafts, and nothing is saved until you approve. Once you trust it, add jobs 1 at a time.</p>
    <ul><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Drafts first, you approve</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Every action is logged</li><li><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>Add 1 job at a time</li></ul>
  </div>
</div>
''', "\"Starting takes just 3 steps.\n\nStep 1, AI setup: we connect your SQL Account safely with the SuDu sync tool. Customers, items, prices, stock and credit limits sync across on their own, and nothing writes straight into your database. We also set permissions: who can approve what.\n\nStep 2, train the AI: just like teaching a new staff member. Write your way of working as Skills and SOPs, for example when to chase a payment, and who to ask when an order is over the credit limit. Then match the item codes: when a customer writes “bwg besar”, the AI has to know which item code that is in your system. We test it first with your orders from last month.\n\nStep 3, start using your AI: it takes orders, chases payments, checks stock and makes reports. At first it only drafts, nothing is saved until you approve, and every action is logged. Once you trust it, add jobs 1 at a time.\n\nWe need 3 things from you: your data, 1 approver and 1 daily user.\"\n\nNext: \"So what does manual work really cost you?\"")

slide('31-next-step', 'Your next step', SEC[6], 'light', 'data-sparks="9,1 1,5" style="--gx:35%;--gy:55%;--mx:40%;--my:55%"', '''
.cards { flex:1; display:grid; grid-template-columns: 1.45fr 1fr; gap: 32px; margin-top: 46px; }
.big { background: var(--ink); color: var(--on-dark); border-radius: 34px; padding: 52px 56px; display:flex; flex-direction:column; box-shadow: 0 0 120px rgba(0,245,169,.22); position:relative; overflow:hidden; }
.big h3 { font-size: 54px; font-weight: 650; letter-spacing: -.03em; line-height: 1.08; }
.big h3 span { color: var(--neon); }
.big p { font-size: 32px; line-height: 1.42; color: var(--on-dark-2); margin-top: 26px; max-width: 820px; }
.big .av { position:absolute; right: 44px; bottom: 40px; width: 200px; height: 200px; }
.sm { padding: 52px 50px; display:flex; flex-direction:column; }
.sm h3 { font-size: 40px; font-weight: 650; letter-spacing: -.02em; }
.sm p { font-size: 30px; line-height: 1.42; color: var(--ink-2); margin-top: 22px; }
.sm .deal { margin-top: auto; padding-top: 28px; border-top: 1px solid var(--line); }
.sm .deal small { display:block; font-size: 32px; font-weight: 650; color: var(--ink); }
.sm .deal b { display:flex; align-items:baseline; gap: 16px; font-size: 150px; font-weight: 800; letter-spacing: -.05em; line-height: 1; color: var(--green); margin-top: 8px; }
.sm .deal b span { font-size: 56px; letter-spacing: -.02em; color: var(--ink); }
.band { margin-top: 32px; }
''', '''
<h1 class="h1 r" style="--d:.1s">Book your free AI Workflow Assessment</h1>
<div class="cards">
  <div class="big r" style="--d:.3s"><h3><span>Free, 45 minutes</span><br>Online Demo</h3><p>Online, we run your first AI job on your own data, then recommend 1 plan.</p><img class="av pop" style="--d:1s" src="../assets/av/agent-thumbs.svg" alt=""></div>
  <div class="glass sm r" style="--d:.5s"><h3>Ready to start now?</h3><div class="deal"><small>Sign within 14 days and get</small><b>20%<span>off</span></b></div></div>
</div>
''', "\"You already did the hard part today. You have your number, your score and your first AI job. The next step is free: a 45-minute Online Demo, where we run your first AI job on your own data. If you already know you want to start, sign within 14 days and get 20% off.\"\n\nNote: do not go back over the problem here. People who hesitate are afraid of choosing wrong: stress free, short, and a person approves everything.\nNext: \"And if you want to go deeper, 3 courses are coming.\"")

# ---------------- upcoming courses ----------------
UC_COURSES = [  # icon, tag, name, tagline, for, 3 things you learn
    ('<path d="M3 21V8l9-5 9 5v13"/><path d="M7 21v-8h10v8M7 17h10"/>', 'WAREHOUSE', 'Smart Warehouse Bootcamp', 'Right stock, right shelf, every time',
     'Storekeepers and warehouse managers',
     ['Set up bins, batches and expiry dates', 'Scan in, pick and pack with WMS', 'Stock counts that match the system']),
    ('<path d="M3 21V11l6 4v-4l6 4V5h6v16z"/><path d="M7 18h2M12 18h2M17 18h2"/>', 'FACTORY', 'Smart Factory Bootcamp', 'Plan, track and cost every batch',
     'Factory owners and production managers',
     ['BOM and work orders, done right', 'Track every job on the floor', 'Real cost and waste for each batch']),
    ('<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M12 3v4M9 12h.01M15 12h.01M9 16h6"/>', 'ADVANCED', 'AI Agent Masterclass', 'Build and run your own AI team',
     'Owners and managers ready for the next step',
     ['Write rules and skills for your agents', 'Set approvals and permissions', 'Measure the time and money it saves']),
]
UC_DETAIL = [  # module title, what you do  (card 01, opened on Next)
    ('Map your warehouse', 'Zones, racks and bins, with batch and expiry for every item.'),
    ('Scan, don&rsquo;t type', 'Receive, put away, pick and pack with the WMS scanner.'),
    ('Count without stopping', 'Cycle counts that match SQL Account, no shutdown day.'),
    ('Let AI watch the stock', 'Inventory AI warns you before stock runs out or expires.'),
]
UC_PRICE = {0: 'RM399'}   # price per person, by card index
UC_TAKE = ['Your own bin map', 'A scanning flow for your team', 'A stock count plan']
slide('31-courses', 'Upcoming courses', SEC[6], 'dark bare', 'data-sparks="none"', MIN_CSS + '''
body { background: #010F0D; overflow: hidden; }
.aur { position:absolute; inset: -20%; z-index: 0; pointer-events:none; filter: blur(60px); opacity: .9;
  background: radial-gradient(35% 30% at 20% 30%, rgba(0,245,169,.22), transparent 70%), radial-gradient(30% 28% at 80% 20%, rgba(77,163,255,.16), transparent 70%),
              radial-gradient(40% 30% at 60% 85%, rgba(124,92,255,.14), transparent 70%);
  animation: aur 16s ease-in-out infinite alternate; }
@keyframes aur { to { transform: translate(4%, -3%) rotate(6deg) scale(1.08); } }
.grain { position:absolute; inset: 0; z-index: 0; pointer-events:none; opacity: .5;
  background-image: linear-gradient(rgba(242,251,247,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(242,251,247,.035) 1px, transparent 1px); background-size: 80px 80px;
  -webkit-mask-image: radial-gradient(70% 60% at 50% 40%, #000, transparent); mask-image: radial-gradient(70% 60% at 50% 40%, #000, transparent); }
.top, .cs { position:relative; z-index: 1; }
.mk { color: var(--neon); }
.mt { color: var(--on-dark); font-size: 84px; }
.mt em { background: linear-gradient(90deg, #00F5A9, #7CFFD6, #4DA3FF); -webkit-background-clip: text; background-clip: text; color: transparent; }
.ml { color: var(--on-dark-2); }
.cs { display:grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 32px; margin-top: 54px; align-items: stretch; }
.cd { position:relative; border-radius: 32px; padding: 2px; overflow:hidden; opacity: 0; transform: translateY(40px) scale(.97); animation: cin 1s cubic-bezier(.2,.75,.15,1) forwards; animation-delay: var(--d); }
@keyframes cin { to { opacity: 1; transform: none; } }
.cd::before { content:""; position:absolute; inset: 0; border-radius: 32px; background: linear-gradient(160deg, rgba(242,251,247,.22), rgba(242,251,247,.04) 40%, rgba(242,251,247,.12)); }
.cd.on::before { inset: -60%; border-radius: 0; background: conic-gradient(from 0deg, transparent 0 62%, #00F5A9 74%, #7CFFD6 78%, transparent 90%); animation: spin 5s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.cd .in { position:relative; height: 100%; display:flex; flex-direction:column; padding: 36px 36px 32px; border-radius: 30px;
  background: linear-gradient(165deg, rgba(10,48,42,.96), rgba(3,26,23,.97)); box-shadow: inset 0 1px 0 rgba(242,251,247,.08); }
.cd.on .in { background: radial-gradient(120% 70% at 20% 0%, rgba(0,245,169,.16), transparent 60%), linear-gradient(165deg, rgba(8,54,46,.98), rgba(2,26,23,.98)); }
.cd .no { position:absolute; right: 26px; top: 6px; font-size: 150px; font-weight: 800; letter-spacing: -.06em; line-height: 1; color: transparent; -webkit-text-stroke: 1.5px rgba(242,251,247,.12); }
.cd.on .no { -webkit-text-stroke-color: rgba(0,245,169,.35); }
.cd .hd { display:flex; align-items:center; gap: 16px; }
.cd .ic { position:relative; width: 84px; height: 84px; border-radius: 24px; display:grid; place-items:center; color: var(--neon); background: rgba(0,245,169,.1); box-shadow: 0 0 0 1px rgba(0,245,169,.3), 0 0 40px rgba(0,245,169,.18); }
.cd .ic svg { animation: flo 4s ease-in-out infinite; } @keyframes flo { 50% { transform: translateY(-4px); } }
.cd .tg { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .18em; color: var(--on-dark-2); padding: 8px 12px; border-radius: 8px; box-shadow: inset 0 0 0 1px rgba(242,251,247,.2); }
.cd.on .tg { color: #02221F; background: var(--neon); box-shadow: 0 0 24px rgba(0,245,169,.45); }
.cd h2 { position:relative; font-size: 46px; font-weight: 800; letter-spacing: -.03em; line-height: 1.05; margin-top: 30px; color: var(--on-dark); }
.cd.on h2 { font-size: 54px; }
.cd .tl { font-size: 27px; font-weight: 650; margin-top: 10px; color: var(--neon); }
.cd .fr { font-size: 22px; color: var(--on-dark-2); margin-top: 20px; }
.cd .fr span { display:block; font-family: var(--mono); font-size: 14px; font-weight: 700; letter-spacing: .18em; color: var(--on-dark-3); margin-bottom: 4px; }
.cd ul { list-style:none; display:grid; gap: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(242,251,247,.12); }
.cd li { display:flex; align-items:flex-start; gap: 12px; font-size: 24px; line-height: 1.3; color: var(--on-dark); }
.cd li svg { flex:none; color: var(--neon); margin-top: 3px; }
.cd .pr { margin-top: auto; padding-top: 22px; display:flex; align-items:baseline; gap: 12px; }
.cd .pr b { font-size: 56px; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: var(--on-dark); text-shadow: 0 0 30px rgba(0,245,169,.35); }
.cd.on .pr b { background: linear-gradient(90deg, #FFFFFF, #7CFFD6); -webkit-background-clip: text; background-clip: text; color: transparent; }
.cd .pr span { font-size: 24px; font-weight: 600; color: var(--on-dark-2); }
.cd .pr + .dt { margin-top: 0; padding-top: 14px; }
.cd .dt { margin-top: auto; padding-top: 24px; display:flex; align-items:center; gap: 10px; font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--on-dark-3); }
.cd .dt i { width: 9px; height: 9px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 12px var(--neon); animation: blink 1.6s ease-in-out infinite; }
@keyframes blink { 50% { opacity: .25; } }
/* ---- Next: card 01 opens ---- */
.cs .cd { transition: opacity .6s ease, transform .8s cubic-bezier(.2,.75,.15,1), filter .6s ease; }
body[data-s="1"] .cs .cd:not(.on) { opacity: 0 !important; transform: translateY(30px) scale(.94) !important; filter: blur(6px); }
body[data-s="1"] .cs .cd.on { opacity: 0 !important; transform: translateY(30px) scale(.94) !important; filter: blur(6px); }
.ex.cd { position:absolute; z-index: 3; display:none; animation: none; opacity: 0; transform: translateY(26px) scale(.985); filter: blur(6px);
  transition: opacity .8s ease, transform 1s cubic-bezier(.2,.75,.15,1), filter .8s ease; }
.ex.show { opacity: 1; transform: none; filter: none; }
.ex .in { display:grid; grid-template-columns: 560px 1fr; column-gap: 56px; }
.ex .lft { display:flex; flex-direction:column; }
.ex .no { font-size: 240px; right: 36px; top: auto; bottom: -46px; }
.ex .dx, .ex .lft { z-index: 1; }
.ex .dx { opacity: 0; transform: translateX(30px); transition: opacity .5s ease, transform .7s cubic-bezier(.2,.75,.15,1); display:flex; flex-direction:column; padding-top: 8px; position:relative; }
.ex.full .dx { opacity: 1; transform: none; transition-delay: .15s; }
.ex .dx small, .ex .tk small { display:block; font-family: var(--mono); font-size: 15px; font-weight: 700; letter-spacing: .18em; color: var(--on-dark-3); }
.ex .md { display:grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 14px; }
.ex .md > div { padding: 20px 22px; border-radius: 20px; background: rgba(242,251,247,.05); box-shadow: inset 0 0 0 1px rgba(242,251,247,.1); opacity: 0; transform: translateY(16px); transition: opacity .45s ease, transform .6s cubic-bezier(.3,1.3,.5,1); }
.ex.full .md > div { opacity: 1; transform: none; }
.ex.full .md > div:nth-child(1) { transition-delay: 0.30s; }
.ex.full .md > div:nth-child(2) { transition-delay: 0.42s; }
.ex.full .md > div:nth-child(3) { transition-delay: 0.54s; }
.ex.full .md > div:nth-child(4) { transition-delay: 0.66s; }

.ex .md i { font-style: normal; font-family: var(--mono); font-size: 16px; font-weight: 700; color: var(--neon); }
.ex .md b { display:block; font-size: 28px; font-weight: 750; letter-spacing: -.01em; color: var(--on-dark); margin-top: 4px; }
.ex .md p { font-size: 22px; line-height: 1.35; color: var(--on-dark-2); margin-top: 6px; }
.ex .tk { margin-top: 22px; }
.ex .tk div { display:flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
.ex .tk span { display:flex; align-items:center; gap: 8px; font-size: 22px; font-weight: 650; color: #02221F; background: var(--neon); padding: 10px 16px; border-radius: 999px; box-shadow: 0 0 24px rgba(0,245,169,.35); }
.ex .lft ul { margin-top: 18px; }
html.static .cd { opacity: 1; transform: none; animation: none; } html.static .aur, html.static .cd.on::before, html.static .cd .ic svg, html.static .cd .dt i { animation: none; }
''', '''
<div class="aur"></div><div class="grain"></div>
<div class="top">
<div class="mk u" style="--d:.05s">What&rsquo;s next</div>
<h1 class="mt u" style="--d:.15s">Keep learning: <em>upcoming courses</em></h1>
<p class="ml u" style="--d:.3s">Today was day 1. Go deeper with your team.</p>
</div>
<div class="cs">''' + ''.join(
    '<div class="cd%s" style="--d:%.2fs"><div class="in"><span class="no">0%d</span><div class="hd"><span class="ic">%s</span><span class="tg">%s</span></div><h2>%s</h2><p class="tl">%s</p>'
    '<p class="fr"><span>FOR</span>%s</p><ul>%s</ul>%s<p class="dt"><i></i>Dates coming soon</p></div></div>'
    % (' on' if k == 0 else '', .5 + k * .2, k + 1, ic(p, 44, 1.9), tg, nm, tl, fr, ''.join('<li>%s%s</li>' % (ic(CHECK, 22, 3), x) for x in ls),
       ('<p class="pr"><b>%s</b><span>per person</span></p>' % UC_PRICE[k]) if k in UC_PRICE else '')
    for k, (p, tg, nm, tl, fr, ls) in enumerate(UC_COURSES)) + '''</div>
<div class="ex cd on" id="ex"><div class="in"><span class="no">01</span>
  <div class="lft"><div class="hd"><span class="ic">''' + ic(UC_COURSES[0][0], 44, 1.9) + '''</span><span class="tg">''' + UC_COURSES[0][1] + '''</span></div>
    <h2>''' + UC_COURSES[0][2] + '''</h2><p class="tl">''' + UC_COURSES[0][3] + '''</p>
    <p class="fr"><span>FOR</span>''' + UC_COURSES[0][4] + '''</p><ul>''' + ''.join('<li>%s%s</li>' % (ic(CHECK, 22, 3), x) for x in UC_COURSES[0][5]) + '''</ul>
    <p class="pr"><b>''' + UC_PRICE[0] + '''</b><span>per person</span></p><p class="dt"><i></i>Dates coming soon</p></div>
  <div class="dx"><small>WHAT YOU WILL DO</small><div class="md">''' + ''.join('<div><i>0%d</i><b>%s</b><p>%s</p></div>' % (k + 1, h, d_) for k, (h, d_) in enumerate(UC_DETAIL)) + '''</div>
    <div class="tk"><small>YOU LEAVE WITH</small><div>''' + ''.join('<span>%s%s</span>' % (ic(CHECK, 20, 3), x) for x in UC_TAKE) + '''</div></div></div>
</div></div>
<script>
(function () {
  var B = document.body, ex = document.getElementById('ex'), cs = document.querySelector('.cs'), timer;
  function box(el, extra) { return { l: cs.offsetLeft + (extra ? 0 : el.offsetLeft), t: cs.offsetTop + (extra ? 0 : el.offsetTop), w: el.offsetWidth, h: el.offsetHeight }; }
  function put(r) { ex.style.left = r.l + 'px'; ex.style.top = r.t + 'px'; ex.style.width = r.w + 'px'; ex.style.height = r.h + 'px'; }
  function set(n) {
    B.dataset.s = String(n); clearTimeout(timer);
    if (n >= 1) {
      put(box(cs, true)); ex.style.display = 'block'; void ex.offsetWidth;
      timer = setTimeout(function () { ex.classList.add('show'); setTimeout(function () { ex.classList.add('full'); }, 300); }, 250);
    } else if (ex.style.display === 'block') {
      ex.classList.remove('show', 'full');
      timer = setTimeout(function () { ex.style.display = 'none'; }, 800);
    }
  }
  set(0);
  addEventListener('message', function (e) { if (e.data && typeof e.data.deckStep === 'number') set(e.data.deckStep); });
})();
</script>
''',
"\"Today was day 1. If you want to go deeper with your team, we have 3 courses coming.\n\n"
"The Smart Warehouse Bootcamp is for storekeepers and warehouse managers: bins, batches and expiry dates, scanning in, picking and packing with WMS, and stock counts that finally match the system.\n\n"
"The Smart Factory Bootcamp is for factory owners and production managers: BOM and work orders done right, tracking every job on the floor, and the real cost and waste of each batch.\n\nAnd the AI Agent Masterclass is the advanced course: you learn to write rules and skills for your agents, set approvals and permissions, and measure the time and money it saves. Build and run your own AI team.\n\nDates are coming soon. Tell your coach which one you want, and we will let you know first.\"\n\n(Next: card 1 opens) \"Let me open the first one, the Smart Warehouse Bootcamp: RM399 per person. 4 things you will do: map your warehouse, zones, racks and bins, with batch and expiry for every item. Scan, don't type: receive, put away, pick and pack with the WMS scanner. Count without stopping: cycle counts that match SQL Account, no shutdown day. And let AI watch the stock: Inventory AI warns you before stock runs out or expires. You leave with your own bin map, a scanning flow for your team and a stock count plan.\"\n\nThis slide has 1 extra Next press: card 1 opens.\n\nNote: dates, fees and HRDF status to be confirmed before the seminar.\nNext: \"And 1 last thing: don't wait.\"")

slide('31-dont-wait', "Don't wait", SEC[6], 'dark', 'data-sparks="none" style="--gx:85%;--gy:30%;--mx:80%;--my:35%"', '''
body { background: #010C0A; }
.bg .tiles { opacity: .6; }
.slide { padding-top: 120px; }
.q1 { font-size: 92px; font-weight: 650; letter-spacing: -.04em; line-height: 1.1; color: var(--on-dark-2); }
.q2 { font-size: 132px; font-weight: 800; letter-spacing: -.05em; line-height: 1.04; margin-top: 10px; color: var(--on-dark); }
.q2 em { font-style: normal; color: var(--neon); }
.q3 { display:inline-flex; align-items:center; gap: 18px; margin-top: 40px; font-size: 44px; font-weight: 750; letter-spacing: -.02em; color: #FFB08F; }
.q3 i { width: 18px; height: 18px; border-radius: 50%; background: #FF8A5B; box-shadow: 0 0 0 0 rgba(255,138,91,.6); animation: ping 1.6s infinite; }
@keyframes ping { 70% { box-shadow: 0 0 0 18px rgba(255,138,91,0); } 100% { box-shadow: 0 0 0 0 rgba(255,138,91,0); } }
/* race */
.race { margin-top: auto; display:grid; gap: 20px; max-width: 1400px; }
.ln { display:grid; grid-template-columns: 220px 1fr; align-items:center; gap: 26px; }
.ln b { font-size: 30px; font-weight: 700; color: var(--on-dark); }
.ln b small { display:block; font-size: 21px; font-weight: 500; color: var(--on-dark-3); margin-top: 2px; }
.tr { position:relative; height: 22px; border-radius: 11px; background: rgba(242,251,247,.08); }
.tr i { position:absolute; left: 0; top: 0; bottom: 0; border-radius: 11px; width: var(--w); transform-origin: left; animation: run 2.4s cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--d); }
.tr i::after { content:""; position:absolute; right: -8px; top: -8px; width: 38px; height: 38px; border-radius: 50%; }
@keyframes run { from { transform: scaleX(0); } }
html.static .tr i, html.static .q3 i { animation: none; }
.them .tr i { background: linear-gradient(90deg, var(--emerald), var(--neon)); box-shadow: 0 0 30px rgba(0,245,169,.45); }
.them .tr i::after { background: var(--neon); box-shadow: 0 0 0 8px rgba(0,245,169,.2); }
.you .tr i { background: rgba(242,251,247,.35); }
.you .tr i::after { background: #F2FBF7; }
.cta { display:flex; align-items:center; gap: 24px; margin-top: 54px; }
.cta .bt { display:inline-flex; align-items:center; gap: 16px; font-size: 34px; font-weight: 750; padding: 22px 34px; border-radius: 999px; background: var(--neon); color: var(--ink); box-shadow: 0 0 60px rgba(0,245,169,.4); }
.cta span { font-size: 28px; color: var(--on-dark-2); }
.cta span b { color: var(--neon); }
.av { position:absolute; right: 128px; top: 150px; width: 330px; height: 330px; }
''', '''
<img class="av pop" style="--d:1.2s" src="../assets/av/agent-liftoff.svg" alt="The SuDu agent lifting off">
<p class="q1 r" style="--d:.15s">You can wait a little longer,</p>
<h1 class="q2 r" style="--d:.5s">but your competitors<br><em>won&rsquo;t wait for you!</em></h1>
<div class="q3 r" style="--d:1.1s"><i></i>They already use AI.</div>
<div class="race">
  <div class="ln them r" style="--d:1.5s"><b>Competitors<small>already using AI</small></b><div class="tr"><i style="--w:88%;--d:1.8s"></i></div></div>
  <div class="ln you r" style="--d:1.6s"><b>You<small>still keying in by hand</small></b><div class="tr"><i style="--w:26%;--d:1.9s"></i></div></div>
</div>
<div class="cta r" style="--d:2.6s"><span class="bt"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>Book a 45-minute Online Demo today</span><span>Sign within 14 days and get <b>20% off</b></span></div>
''', "(Pause. Let the first line land.) \"You can wait a little longer. But your competitors won't wait for you!\n\nThey already use AI: orders come in by themselves, payments are chased faster, stock figures are right. In every industrial revolution, the ones who moved first took the customers. The gap grows every month.\n\nBook your 45-minute Online Demo today, and see AI work on your own data. Sign within 14 days and get 20% off.\"\n\nNext: questions.")

# ============================================================ 7 · Q&A + SPARES
slide('32-questions', 'Questions', SEC[7], 'dark', 'data-sparks="2,1 8,1 5,5" style="--gx:50%;--gy:42%;--mx:50%;--my:45%"', '''
.c { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.av { width: 380px; height: 380px; margin-bottom: 56px; }
.display { font-size: 128px; }
.small { font-size: 30px; margin-top: 30px; }
''', '''
<div class="c">
  <img class="av pop" style="--d:.2s" src="../assets/av/agent-typing.svg" alt="The agent with a headset">
  <h1 class="display r" style="--d:.4s">What would you like to ask?</h1>
  <p class="small r" style="--d:.7s">The seminar ends at 3:30 pm. The SuDu team is here until 5:45 pm.</p>
</div>
''', "Take questions for about ten minutes, then the lucky draw, then the closing line (slide 33).\nIf the room is quiet: \"Let me ask the one everybody is thinking: do I have to stop using SQL Account?\"\n\nPrepared answers:\n· Stop using SQL Account? No. It stays; SuDu works around it and sends records back.\n· AutoCount? Yes, it connects to AutoCount as well.\n· Replace my staff? It takes over the typing and chasing. Staff check, approve and deal with customers.\n· Mistakes? Important steps wait for approval, everything is recorded, every new job starts draft-only.\n· Data safe / used for training? [Confirm with product team.]\n· Messy data? Yes, start anyway: the readiness check, and we clean item codes during setup.\n· Languages? [Confirm: BM, English, Chinese, mixed.]\n· Grants? [Confirm HRD Corp and digitalisation grant position.]")

slide('33-closing', 'Closing line', SEC[8], 'dark bare', 'data-sparks="2,1 8,1 9,4 5,5" style="--gx:70%;--gy:50%;--mx:70%;--my:50%"', '''
.wrap { flex:1; display:grid; grid-template-columns: 1fr 520px; align-items:center; gap: 60px; }
.display { font-size: 118px; line-height: 1.02; }
.display .dim { color: var(--on-dark-3); }
.av { width: 500px; height: 500px; }
.logo { position:absolute; left: 128px; bottom: 64px; height: 40px; }
''', '''
<div class="wrap">
  <h1 class="display"><span class="dim r" style="--d:.2s;display:block">You came in with a to-do list.</span><span class="r" style="--d:.9s;display:block">You leave with your <span class="sig" style="--sd:1.8s">first AI job.</span></span></h1>
  <div class="float"><img class="av pop" style="--d:.5s" src="../assets/av/agent-liftoff.svg" alt="The agent lifting off"></div>
</div>
<img class="logo f" style="--d:1.4s" src="../assets/logo-white.png" alt="SuDu AI">
''', "Leave this up while people talk to the team.")



# ---------------------------------------------------------------- write
def main():
    os.makedirs(os.path.join(HERE, 'slides'), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, 'slides')):
        if f.endswith('.html'):
            os.remove(os.path.join(HERE, 'slides', f))
    manifest = []
    # ---- running order: 1 list per section. Change the order here; every slide must appear once. ----
    key = lambda x: re.sub(r'^\d+-', '', x['file'])
    DROP = {'ai-history', 'what-is-llm', 'agent-loop', 'agent-quiz', 'sql-stays', 'foundation', 'intro-01', 'readiness-qr', 'readiness-check', 'closing', 'ai-team', 'meme'}   # kept in this file, left out of the deck
    S[:] = [x for x in S if key(x) not in DROP]
    keys = [key(x) for x in S]
    demo = keys[keys.index('demo-day'):keys.index('you-stay-the-boss') + 1]   # demo intros + use cases, as defined
    demo_k = [k for k in demo if k not in DROP]
    SECTIONS = [
        ('Company intro', ['cover', 'who-we-are']),
        ('Speaker intro', ['speaker', 'speaker-owen', 'today', 'takeaways', 'meme-img']),
        ('What is an AI Agent?', ['section-ai', 'ai-types', 'how-much-it-read',
                                  'why-agent', 'agent-intro', 'what-is-agent', 'good-vs-bad-agent', 'brain-to-staff']),
        ('SuDu AI', ['imagine', 'video-figure', 'vision', 'the-map', 'five-stages', 'layers-3d']),
        ('The problem', ['section-problem', 'tell-us', 'top-5-issues', 'guess-the-order', 'typed-three-times', 'problem-2', 'problem-3', 'problem-4', 'problem-5', 'count-your-number', 'ai-guru', 'new-way']),
        ('SuDu AI', ['tools-and-memory', 'wms-intro', 'wms-supply', 'wms-stock', 'video-wms']),
        ('Get started', ['courses']),   # upcoming courses, right after the WMS video
        ('SuDu AI', ['faq', 'why-sudu', 'plug-straight-in', 'plug-deep', 'the-house', 'meme-pool']),
        ('Get started', ['live-in-30-days', 'plans', 'plan-details', 'flexi-tokens', 'what-it-gives-back', 'cost-compare', 'hrdf']),   # before the live demo
        ('SuDu AI', ['section-demo'] + demo_k[:demo_k.index('you-stay-the-boss')]),
        ('Workshop', ['section-workshop']),
        ('Get started', ['dont-wait']),
        ('Questions', ['questions']),
        ('SuDu AI', demo_k[demo_k.index('you-stay-the-boss'):]),   # 4 things AI never does, after Questions
        ('Workshop', ['workshop-groups', 'need-wms-mes']),
        ('Get started', ['next-step']),
    ]
    by = {key(x): x for x in S}
    order = [k for _, ks in SECTIONS for k in ks]
    assert sorted(order) == sorted(keys), ('running order mismatch', set(keys) ^ set(order))
    for sec, ks in SECTIONS:
        for k in ks:
            by[k]['section'] = sec
    S[:] = [by[k] for k in order]
    for i, s in enumerate(S):
        s['file'] = '%02d-%s' % (i + 1, re.sub(r'^\d+-', '', s['file']))
        html = page(s['label'] + ' · Hire Your First AI Agent', s['section'], s['theme'], s['attrs'], s['css'], s['html'])
        with open(os.path.join(HERE, 'slides', s['file'] + '.html'), 'w') as fh:
            fh.write(html)
        item = {'file': 'slides/%s.html' % s['file'], 'label': s['label'], 'section': s['section'], 'notes': s['notes']}
        if s['file'].endswith('layers-3d'):
            item['steps'] = 5
        if s['file'].endswith('what-is-agent'):
            item['steps'] = 6
        if s['file'].endswith('tools-and-memory'):
            item['steps'] = 1
        if s['file'].endswith('wms-supply') or s['file'].endswith('wms-stock'):
            item['steps'] = 1
        if s['file'].endswith('ai-guru'):
            item['steps'] = 2
        if s['file'].endswith('courses'):
            item['steps'] = 1
        if s['file'].endswith('agent-quiz'):
            item['steps'] = 1
        if s['file'].endswith('good-vs-bad-agent'):
            item['steps'] = 4
        if s['file'].endswith('ai-history'):
            item['steps'] = 5
        if s['file'].endswith('ai-types'):
            item['steps'] = 5
        if s['file'].endswith('how-much-it-read'):
            item['steps'] = 2
        if s['file'].endswith('what-is-llm'):
            item['steps'] = 1
        if s['file'].endswith('guess-the-order'):
            item['steps'] = 2
        if s['file'].endswith('why-sudu'):
            item['steps'] = 1
        if os.path.exists(os.path.join(HERE, 'thumbs', s['file'] + '.jpg')):
            item['thumb'] = 'thumbs/%s.jpg' % s['file']
        manifest.append(item)

    raw_shell = open(os.path.join(HERE, 'shell.html')).read()
    shell = raw_shell.replace('/*MANIFEST*/', json.dumps(manifest, ensure_ascii=False, indent=1))
    with open(os.path.join(HERE, 'index.html'), 'w') as fh:
        fh.write(shell)
    print('built %d slides' % len(S))
    import i18n            # Mandarin deck: slides-zh/ + index-zh.html, from i18n/zh.json
    i18n.build_zh(manifest, raw_shell)

if __name__ == '__main__':
    main()
