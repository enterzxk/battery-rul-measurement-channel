
// _m_axis_probe.mjs — Phase 4 review probe: is the k(rows) vs m(lifetimes) axis measurable?
// Reads ONLY code/results/20261107-203233_e1_reproduce_full_table/preds.csv. No project files modified.
// Run: node review-stage/_m_axis_probe.mjs
import fs from "node:fs";

const CSV = "code/results/20261107-203233_e1_reproduce_full_table/preds.csv";
const rows = fs.readFileSync(CSV, "utf8").split(/\r?\n/).filter(l => l.trim().length > 0);
const hdr = rows[0].split(",");
const ix = Object.fromEntries(hdr.map((h, i) => [h, i]));
const data = rows.slice(1).map(l => { const a = l.split(","); return { cell: a[ix.cell_id], rpt: +a[ix.rpt], g: a[ix.group_id], y: +a[ix.y_true], p: +a[ix.pred_A_curve_logo] }; });

const cells = new Map();
for (const d of data) { if (!cells.has(d.cell)) cells.set(d.cell, { g: d.g, rows: [] }); cells.get(d.cell).rows.push(d); }
const groups = new Map();
for (const [c, v] of cells) { if (!groups.has(v.g)) groups.set(v.g, []); groups.get(v.g).push(c); }

const R = s => { let a = s; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
const sh = (arr, rng) => { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; };
function fit(pts) { let n = pts.length, sx = 0, sy = 0, sxx = 0, sxy = 0; for (const [x, y] of pts) { sx += x; sy += y; sxx += x * x; sxy += x * y; } const den = n * sxx - sx * sx; if (Math.abs(den) < 1e-9) return { a: 1, b: sy / n - sx / n }; const a = (n * sxy - sx * sy) / den; return { a, b: (sy - a * sx) / n }; }
const T975 = 2.2281, T80 = 0.8791;
function stats(ds) {
  const mean = ds.reduce((a, b) => a + b, 0) / ds.length;
  const sd = Math.sqrt(ds.reduce((s, d) => s + (d - mean) ** 2, 0) / (ds.length - 1));
  const mde = (T975 + T80) * sd / Math.sqrt(ds.length);
  const abs = ds.map(Math.abs), ord = [...abs.keys()].sort((i, j) => abs[i] - abs[j]);
  const rank = new Array(abs.length); let i = 0;
  while (i < ord.length) { let j = i; while (j + 1 < ord.length && abs[ord[j + 1]] === abs[ord[i]]) j++; const r = (i + j) / 2 + 1; for (let k = i; k <= j; k++) rank[ord[k]] = r; i = j + 1; }
  const obs = ds.reduce((s, d, i2) => s + (d > 0 ? rank[i2] : 0), 0), N = abs.length, W = [];
  for (let mask = 0; mask < (1 << N); mask++) { let w = 0; for (let k = 0; k < N; k++) if (mask >> k & 1) w += rank[k]; W.push(w); }
  const pG = W.filter(w => w >= obs - 1e-9).length / W.length, pL = W.filter(w => w <= obs + 1e-9).length / W.length;
  return { mean, sd, mde, p2: Math.min(1, 2 * Math.min(pG, pL)), pos: ds.filter(d => d > 0).length, n: N, nNeed: Math.ceil(7.849 * (sd / mean) ** 2) };
}

// ---- 0. baseline
let g0 = [];
for (const [g, cs] of groups) { const per = cs.map(c => { const r = cells.get(c).rows; return r.reduce((s, x) => s + Math.abs(x.p - x.y), 0) / r.length; }); g0.push(per.reduce((a, b) => a + b, 0) / per.length); }
console.log("== 0. k=0 anchor ==");
console.log("cell-macro MAE =", (g0.reduce((a, b) => a + b, 0) / g0.length).toFixed(4), "| per-group:", g0.map(x => x.toFixed(2)).join(" "));
console.log("cells:", cells.size, "groups:", groups.size, "rows:", data.length, "rows/cell:", (data.length / cells.size).toFixed(2));

// ---- 1. per-condition lifetime structure (censoring feasibility)
console.log("\n== 1. within-condition lifetime structure (RPT) ==");
const lifeSpread = [];
for (const [g, cs] of groups) {
  const L = cs.map(c => cells.get(c).rows.length).sort((a, b) => a - b);
  const mean = L.reduce((a, b) => a + b, 0) / L.length, sd = Math.sqrt(L.reduce((s, x) => s + (x - mean) ** 2, 0) / (L.length - 1));
  lifeSpread.push({ g, n: L.length, min: L[0], max: L[L.length - 1], mean, spread: L[L.length - 1] - L[0], cv: sd / mean });
  console.log(" g" + g, "n=" + L.length, "min=" + L[0], "max=" + L[L.length - 1], "mean=" + mean.toFixed(1), "spread=" + (L[L.length - 1] - L[0]), "CV=" + (sd / mean).toFixed(3));
}
console.log(" spread range:", Math.min(...lifeSpread.map(x => x.spread)), "-", Math.max(...lifeSpread.map(x => x.spread)), "RPT; CV range:", Math.min(...lifeSpread.map(x => x.cv)).toFixed(3), "-", Math.max(...lifeSpread.map(x => x.cv)).toFixed(3));

// ---- arms
function drawFixedK(k, m, rng, order) {
  const per = new Map();
  for (const [g, cs] of groups) {
    const ms = cs.map(t => {
      let donors = cs.filter(c => c !== t);
      if (order === "short") donors = donors.slice().sort((x, y) => cells.get(x).rows.length - cells.get(y).rows.length);
      if (order === "long") donors = donors.slice().sort((x, y) => cells.get(y).rows.length - cells.get(x).rows.length);
      const use = sh(donors.slice(), rng).slice(0, Math.min(m, donors.length));
      const base = Math.floor(k / use.length), rem = k % use.length, pts = [];
      use.forEach((c, j) => { const rs = sh(cells.get(c).rows.slice(), rng); const want = Math.min(base + (j < rem ? 1 : 0), rs.length); for (let i = 0; i < want; i++) pts.push([rs[i].p, rs[i].y]); });
      const { a, b } = fit(pts); const tr = cells.get(t).rows; let s = 0; for (const r of tr) s += Math.abs(a * r.p + b - r.y);
      return s / tr.length;
    });
    per.set(g, ms.reduce((a, b) => a + b, 0) / ms.length);
  }
  return per;
}
function drawFull(m, rng, G) {
  const per = new Map();
  for (const [g, cs] of groups) {
    let cset = cs.slice(); if (G && cset.length > G) cset = sh(cset.slice(), rng).slice(0, G);
    const ms = cset.map(t => {
      const use = sh(cset.filter(c => c !== t).slice(), rng).slice(0, Math.min(m, cset.length - 1));
      if (!use.length) return null;
      const pts = []; for (const c of use) for (const r of cells.get(c).rows) pts.push([r.p, r.y]);
      const { a, b } = fit(pts); const tr = cells.get(t).rows; let s = 0; for (const r of tr) s += Math.abs(a * r.p + b - r.y);
      return s / tr.length;
    }).filter(v => v !== null);
    per.set(g, ms.reduce((a, b) => a + b, 0) / ms.length);
  }
  return per;
}
function avg(fn, D, seed) { const rng = R(seed), acc = new Map(); for (const g of groups.keys()) acc.set(g, 0); for (let d = 0; d < D; d++) { const pd = fn(rng); for (const [g, v] of pd) acc.set(g, acc.get(g) + v / D); } return acc; }
const macro = a => { const v = [...a.values()]; return v.reduce((x, y) => x + y, 0) / v.length; };

// ---- 2. MAE(k,m) grid at fixed k
console.log("\n== 2. MAE(k,m) at fixed k (D=60) ==");
const KS = [4, 8, 16, 32, 64], MS = [1, 2, 3, 5], grid = {};
for (const k of KS) for (const m of MS) grid[k + "_" + m] = avg(r => drawFixedK(k, m, r, null), 60, 900 + k * 31 + m);
console.log(" k\\m " + MS.map(m => "m=" + m).join("  "));
for (const k of KS) console.log(" " + k + "  " + MS.map(m => grid[k + "_" + m] ? macro(grid[k + "_" + m]).toFixed(3) : "-").join("  "));

// ---- 3. cost-correct arm: m lifetimes, all rows
console.log("\n== 3. cost-correct arm: MAE(m completed lifetimes, ALL rows) ==");
const full = {}; for (const m of [1, 2, 3, 4, 5]) full[m] = avg(r => drawFull(m, r), 80, 9100 + m);
for (const m of [1, 2, 3, 4, 5]) console.log(" m=" + m + ": " + macro(full[m]).toFixed(3));
const gs = [...full[1].keys()];
console.log(" increments (paired over 11 conditions):");
for (const m of [2, 3, 4, 5]) { const d = gs.map(g => full[m - 1].get(g) - full[m].get(g)); const s = stats(d); console.log("  m=" + (m - 1) + "->" + m + ": d=" + s.mean.toFixed(4) + " sd=" + s.sd.toFixed(4) + " MDE=" + s.mde.toFixed(4) + " p=" + s.p2.toFixed(4) + " pos=" + s.pos + "/" + s.n + " n_needed=" + s.nNeed); }
const m5 = macro(full[5]), base = 6.5157;
console.log(" share of the 5-lifetime gain reached at m=1,2,3:", [1, 2, 3].map(m => (((base - macro(full[m])) / (base - m5)) * 100).toFixed(0) + "%").join(" "));

// ---- 4. k-axis at fixed m=1
console.log("\n== 4. row axis at fixed m=1 (free given one paid lifetime) ==");
const k4 = avg(r => drawFixedK(4, 1, r, null), 80, 6242), k16 = avg(r => drawFixedK(16, 1, r, null), 80, 6343);
const dk = gs.map(g => k4.get(g) - k16.get(g)); const sk = stats(dk);
console.log(" k=4 -> k=16 @m=1: d=" + sk.mean.toFixed(3) + " sd=" + sk.sd.toFixed(3) + " MDE=" + sk.mde.toFixed(3) + " p=" + sk.p2.toFixed(5) + " pos=" + sk.pos + "/11 n_needed=" + sk.nNeed);

// ---- 5. m-axis at fixed k (confounded arm)
const A = avg(r => drawFixedK(16, 1, r, null), 80, 4242), B = avg(r => drawFixedK(16, 5, r, null), 80, 4343);
const dm = gs.map(g => A.get(g) - B.get(g)); const sm = stats(dm);
console.log("\n== 5. m-axis at fixed k=16 (confounded with rows/donor) ==");
console.log(" m=1 -> m=5: d=" + sm.mean.toFixed(3) + " sd=" + sm.sd.toFixed(3) + " MDE=" + sm.mde.toFixed(3) + " p=" + sm.p2.toFixed(4) + " pos=" + sm.pos + "/11");

// ---- 6. censoring proxy: shortest vs longest lived donor
const S = avg(r => drawFixedK(16, 1, r, "short"), 80, 7242), Lg = avg(r => drawFixedK(16, 1, r, "long"), 80, 7343);
const dc = gs.map(g => S.get(g) - Lg.get(g)); const sc = stats(dc);
const half = 2.2281 * sc.sd / Math.sqrt(11);
console.log("\n== 6. censoring proxy: calibrate on shortest- vs longest-lived donor (k=16,m=1) ==");
console.log(" d=" + sc.mean.toFixed(4) + " sd=" + sc.sd.toFixed(4) + " MDE=" + sc.mde.toFixed(4) + " p=" + sc.p2.toFixed(4) + " 95%CI=[" + (sc.mean - half).toFixed(4) + "," + (sc.mean + half).toFixed(4) + "]");
console.log(" => |effect| bounded below " + Math.max(Math.abs(sc.mean - half), Math.abs(sc.mean + half)).toFixed(4) + " MAE = " + (100 * Math.max(Math.abs(sc.mean - half), Math.abs(sc.mean + half)) / base).toFixed(2) + "% of baseline");

// ---- 7. group-size stress test (is the knee a fraction-of-group artifact?)
console.log("\n== 7. group-size stress test: subsample G cells/condition, all-rows arm ==");
for (const G of [4, 5, 6]) {
  const out = [];
  for (const m of [1, 2, 3]) { if (m > G - 1) continue; out.push("m=" + m + ":" + macro(avg(r => drawFull(m, r, G), 50, 7700 + G * 13 + m)).toFixed(3)); }
  console.log(" G=" + G + " -> " + out.join("  "));
}

// ---- 8. cost-model sensitivity: same data, three cost functions
console.log("\n== 8. cost-model sensitivity (the falsifiability gate) ==");
const dRows = sk.mean;                 // k=4->k=16 at m=1: 12 extra rows, zero extra lifetimes
const dLife = macro(full[1]) - macro(full[5]);  // m=1->m=5: 4 extra lifetimes, rows free
console.log(" cost = labelled rows   -> 12 extra rows (0 extra lifetimes) buys " + dRows.toFixed(3) + " MAE");
console.log(" cost = donor lifetimes -> 4 extra lifetimes (all rows free) buys " + dLife.toFixed(3) + " MAE");
console.log(" under cost=rows the lifetime purchase is not even expressible (its row cost is already paid);");
console.log(" under cost=lifetimes the row purchase is free. The ranking follows the cost function, not the data.");
console.log(" ratio rows/lifetimes (per unit of its own cost) is undefined under cost=rows for lifetimes and vice versa ->");
console.log(" the ranking is a property of the cost function, not of the data.");
