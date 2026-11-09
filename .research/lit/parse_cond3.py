import re, csv
import numpy as np
t = open("isu_readme.txt", encoding="utf-8").read()
seg = t[t.find("A1."):]
toks = [x.strip() for x in seg.split("\n") if x.strip()]
pg = re.compile(r"^\d{1,2}$"); pc = re.compile(r"^\d\.\d{3}$"); pd = re.compile(r"^\d{1,3}\.\d{2}%$")
rows, k = [], 0
while k < len(toks) - 3:
    if pg.match(toks[k]) and pc.match(toks[k+1]) and pc.match(toks[k+2]) and pd.match(toks[k+3]):
        rows.append((int(toks[k]), float(toks[k+1]), float(toks[k+2]), float(toks[k+3].rstrip("%"))))
        k += 4
    else: k += 1
seen=set(); uniq=[]
for r in rows:
    if r[0] not in seen: seen.add(r[0]); uniq.append(r)
uniq.sort()
print("parsed groups:", len(uniq), "range", uniq[0][0], "-", uniq[-1][0], "| missing:", [g for g in range(1,65) if g not in seen])
print("document order ascending?", all(rows[i][0] < rows[i+1][0] for i in range(len(rows)-1)))
print("DoD pct range: {:.2f} - {:.2f}".format(min(r[3] for r in uniq), max(r[3] for r in uniq)))
print("charge C-rate range: {:.3f} - {:.3f}  distinct {}".format(min(r[1] for r in uniq), max(r[1] for r in uniq), len(set(r[1] for r in uniq))))
print("discharge C-rate range: {:.3f} - {:.3f}  distinct {}".format(min(r[2] for r in uniq), max(r[2] for r in uniq), len(set(r[2] for r in uniq))))
print("\nfirst 6:", uniq[:6])
print("last 6:", uniq[-6:])
with open("isu_conditions.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["group","charge_C","discharge_C","mean_DoD_pct"])
    for r in uniq: w.writerow(r)
z = np.load("E:/桌面/rul/rul_v4_20261107/.research/results/isu_table.npz", allow_pickle=True)
gs = sorted(set(z["X"][:,0].astype(int).tolist()))
print("\ndata groups:", len(gs), "| table groups:", len(uniq))
print("in data not table:", sorted(set(gs)-seen), "| in table not data:", sorted(seen-set(gs)))
# correlation sanity: does DoD or rate predict mean lifetime?
eol = {}
cells = z["cells"]; rpt = z["X"][:,1]; soh = z["X"][:,6]; grp = z["X"][:,0].astype(int)
for c in np.unique(cells):
    m = cells == c; rr, ss = rpt[m], soh[m]
    o = np.argsort(rr); rr, ss = rr[o], ss[o]
    h = np.where(ss <= 0.80)[0]
    if len(h): eol[c] = int(rr[h[0]])
cg = {c: g for c, g in zip(cells, grp)}
per = {}
for c, g in cg.items():
    if c in eol: per.setdefault(g, []).append(eol[c])
d = {r[0]: r for r in uniq}
gg = [g for g in sorted(per) if g in d]
y = np.array([np.mean(per[g]) for g in gg])
for idx, name in [(1,"charge_C"),(2,"discharge_C"),(3,"DoD")]:
    x = np.array([d[g][idx] for g in gg])
    from scipy import stats
    rho, p = stats.spearmanr(x, y)
    print("  Spearman(%-12s, mean EOL RPT) = %+.3f  p=%.4f" % (name, rho, p))
