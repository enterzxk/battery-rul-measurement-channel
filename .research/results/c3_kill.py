# -*- coding: utf-8 -*-
"""EXP-031 v2: C3 kill experiment.

PARTIALLY conforming to the frozen preregistration
(.research/exp/EXP-031-c3-preregistration.md). Two KNOWN DEVIATIONS, disclosed in
.research/exp/EXP-031-c3-result.md:
  (a) NO equal-total-weight per training cell - arm_mae fits without sample_weight,
      so longer trajectories receive more total fitting weight;
  (b) intervals are MARGINAL, not simultaneous (two separate percentile bands).
Do not describe this script's output as a clean preregistered confirmatory run.

v1 was stopped before completion because it deviated: it fixed the maximin start
and applied the 20 procurement draws only to arm D. The preregistration says
"20 fixed draws, shared cell orderings, maximin starting points randomised".
v2 implements that: within each draw all four arms share one maximin ordering
computed from a randomly chosen starting condition; D is a uniform random draw
of 24 conditions from the same source pool in the same draw.

Arms (N=24 completed cells):
  A 24 conditions x 1 cell   (maximin)
  B 12 conditions x 2 cells  (first 12 of the same ordering)
  C  6 conditions x 4 cells  (first 6; diagnostic only)
  D 24 conditions x 1 cell   (uniform random)

Kill gate: G_A >= 0.05 AND G_D >= 0.05, both simultaneous 95% lower bounds > 0.
"""
import numpy as np, json, os, collections
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
z = np.load(os.path.join(HERE, "isu_table.npz"), allow_pickle=True)
X = z["X"]; cells = z["cells"]
grp = X[:, 0].astype(int); rpt = X[:, 1]; feat = X[:, 2:6]; soh = X[:, 6]

N_BUDGET = 24; NDRAW = 20; K_MAX = 4; BASE_SEED = 20261109

per_cell = collections.defaultdict(list)
for g, r, f, s, c in zip(grp, rpt, feat, soh, cells):
    per_cell[c].append((float(r), np.asarray(f, float), float(s)))
cell_cond = {c: int(g) for c, g in zip(cells, grp)}
cond_cells = collections.defaultdict(list)
for c, g in cell_cond.items():
    cond_cells[g].append(c)
for g in cond_cells:
    cond_cells[g] = sorted(cond_cells[g])           # frozen lexicographic ordering

eol = {}
for c in np.unique(cells):
    rr = np.array([t[0] for t in per_cell[c]]); ss = np.array([t[2] for t in per_cell[c]])
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    hit = np.where(ss <= 0.80)[0]
    if len(hit): eol[c] = int(rr[hit[0]])
usable = {c: [(r, f) for r, f, s in sorted(per_cell[c], key=lambda t: t[0])
              if c in eol and r <= eol[c]] for c in per_cell}

def scout_desc(g):
    """Causal prefix descriptor: first cell (lexicographic), first 3 distinct RPTs.
    No stored soh (full-trajectory normalisation = leakage), no EOL dependence."""
    scout = cond_cells[g][0]
    rr, ff, seen = [], [], set()
    for r, f, s in sorted(per_cell[scout], key=lambda t: t[0]):
        if int(r) in seen: continue
        seen.add(int(r)); rr.append(r); ff.append(np.asarray(f, float))
        if len(rr) == 3: break
    if len(rr) < 3 or not np.isfinite(ff[0][0]) or ff[0][0] <= 0: return None
    h = [ff[j][0] / ff[0][0] for j in range(3)]
    if not np.all(np.isfinite(h)): return None
    fade = (h[0] - h[2]) / (rr[2] - rr[0])
    d = np.concatenate([[fade], np.mean(np.array(ff), axis=0)])
    return d if np.all(np.isfinite(d)) else None

DESC = {g: scout_desc(g) for g in cond_cells}
ELIG = [g for g in sorted(cond_cells)
        if DESC[g] is not None and sum(1 for c in cond_cells[g] if len(usable[c]) >= 4) >= K_MAX]
print("eligible source conditions: %d / %d" % (len(ELIG), len(cond_cells)), flush=True)

def maximin(Z, start):
    n = len(Z); order = [start]
    dmin = np.linalg.norm(Z - Z[start], axis=1)
    for _ in range(n - 1):
        dmin[order] = -1.0
        nxt = int(np.argmax(dmin))
        order.append(nxt)
        dmin = np.minimum(dmin, np.linalg.norm(Z - Z[nxt], axis=1))
    return order

def arm_mae(train_cells, te_cells):
    tr_f, tr_y = [], []
    for c in train_cells:
        for r, f in usable[c]:
            tr_f.append(f); tr_y.append(eol[c] - r)
    if len(tr_y) < 20: return None
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    m.fit(np.array(tr_f), np.array(tr_y, float))
    vals = []
    for c in te_cells:
        rows = usable[c]
        if not rows: continue
        p = m.predict(np.array([f for _, f in rows]))
        y = np.array([eol[c] - r for r, _ in rows], float)
        vals.append(float(np.mean(np.abs(y - p))))
    return float(np.mean(vals)) if vals else None

res = {a: collections.defaultdict(list) for a in "ABCD"}
folds = 0
for tgt in sorted(cond_cells):
    src = [g for g in ELIG if g != tgt]
    if len(src) < 24: continue
    te = [c for c in cond_cells[tgt] if usable[c]]
    if not te: continue
    Z = np.array([DESC[g] for g in src])
    Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-12)        # source-only standardisation
    for d in range(NDRAW):
        rng = np.random.default_rng(BASE_SEED + d)
        order = maximin(Z, int(rng.integers(len(Z))))   # randomised maximin start
        ranked = [src[i] for i in order]
        plans = {"A": [(g, 1) for g in ranked[:24]],
                 "B": [(g, 2) for g in ranked[:12]],
                 "C": [(g, 4) for g in ranked[:6]]}
        for arm, plan in plans.items():
            tc = [cond_cells[g][k] for g, n in plan for k in range(min(n, len(cond_cells[g])))][:N_BUDGET]
            v = arm_mae(tc, te)
            if v is not None: res[arm][tgt].append(v)
        pick = rng.choice(src, size=24, replace=False)
        v = arm_mae([cond_cells[g][0] for g in pick], te)
        if v is not None: res["D"][tgt].append(v)
    folds += 1
    if folds % 5 == 0: print("  folds %d/%d" % (folds, len([g for g in sorted(cond_cells)])), flush=True)

gs = [g for g in sorted(cond_cells) if all(res[a][g] for a in "ABCD")]
R = {a: np.array([np.mean(res[a][g]) for g in gs]) for a in "ABCD"}
print("\nfolds %d | conditions with all four arms: %d" % (folds, len(gs)))
for a in "ABCD":
    print("  arm %s  condition-macro MAE  mean %8.4f  median %8.4f" % (a, R[a].mean(), np.median(R[a])))
G_A = 1 - R["B"].mean() / R["A"].mean()
G_D = 1 - R["B"].mean() / R["D"].mean()
print("\nG_A (B vs maximin coverage) = %+.4f" % G_A)
print("G_D (B vs random coverage)  = %+.4f" % G_D)
boot = []
n = len(gs)
brng = np.random.default_rng(777)
for _ in range(5000):
    idx = brng.integers(0, n, n)
    b = R["B"][idx].mean()
    boot.append([1 - b / R["A"][idx].mean(), 1 - b / R["D"][idx].mean()])
boot = np.array(boot)
lo = np.percentile(boot, 2.5, axis=0); hi = np.percentile(boot, 97.5, axis=0)
print("  95%% CI G_A [%+.4f, %+.4f]" % (lo[0], hi[0]))
print("  95%% CI G_D [%+.4f, %+.4f]" % (lo[1], hi[1]))
gate = bool(G_A >= 0.05 and G_D >= 0.05 and lo[0] > 0 and lo[1] > 0)
print("\nKILL GATE: %s" % ("PASS - continue C3" if gate else "FAIL - stop C3 as headline"))
json.dump({"n_conditions": n, "folds": folds, "ndraw": NDRAW,
           "arms": {a: {"mean": float(R[a].mean()), "per_condition": [float(v) for v in R[a]]} for a in "ABCD"},
           "G_A": float(G_A), "G_D": float(G_D),
           "ci_A": [float(lo[0]), float(hi[0])], "ci_D": [float(lo[1]), float(hi[1])],
           "gate_pass": gate},
          open(os.path.join(HERE, "c3_kill.json"), "w"), indent=1)
