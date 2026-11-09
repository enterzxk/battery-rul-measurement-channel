import numpy as np, collections
exec(open("c3_kill.py", encoding="utf-8").read().split("res = {a: collections")[0])

def maximin(Z, start):
    n=len(Z); order=[start]; dmin=np.linalg.norm(Z-Z[start],axis=1)
    for _ in range(n-1):
        dmin[order]=-1.0; nxt=int(np.argmax(dmin)); order.append(nxt)
        dmin=np.minimum(dmin, np.linalg.norm(Z-Z[nxt],axis=1))
    return order

tgt = sorted(cond_cells)[0]
src = [g for g in ELIG if g != tgt]
Z = np.array([DESC[g] for g in src]); Z = (Z-Z.mean(0))/(Z.std(0)+1e-12)
sets12, sets24 = [], []
for d in range(20):
    rng = np.random.default_rng(BASE_SEED+d)
    o = maximin(Z, int(rng.integers(len(Z))))
    ranked=[src[i] for i in o]
    sets12.append(set(ranked[:12])); sets24.append(set(ranked[:24]))
def jac(a,b): return len(a&b)/len(a|b)
J12=[jac(sets12[i],sets12[j]) for i in range(20) for j in range(i+1,20)]
J24=[jac(sets24[i],sets24[j]) for i in range(20) for j in range(i+1,20)]
print("overlap between draws (Jaccard), 190 pairs:")
print("  first-12 sets: mean %.3f  min %.3f  max %.3f" % (np.mean(J12), min(J12), max(J12)))
print("  first-24 sets: mean %.3f  min %.3f  max %.3f" % (np.mean(J24), min(J24), max(J24)))
print("\ndistinct first-12 sets across 20 draws: %d" % len(set(frozenset(s) for s in sets12)))
print("distinct first-24 sets across 20 draws: %d" % len(set(frozenset(s) for s in sets24)))
