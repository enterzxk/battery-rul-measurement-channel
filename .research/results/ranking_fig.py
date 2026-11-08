# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, os

data = {
    "UConn (11 conditions)": {
        "fit scope": 274.0, "evaluation population": -208.0,
        "aggregation order": 12.0, "row allocation": -10.0, "draw aggregation": -6.0,
    },
    "ISU-ILCC (57 conditions)": {
        "fit scope": 140.0, "evaluation population": -332.0,
        "aggregation order": -26.0, "row allocation": 28.0, "draw aggregation": -43.0,
    },
}
order_keys = ["fit scope", "evaluation population", "draw aggregation",
              "aggregation order", "row allocation"]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), sharex=True)
for ax, (ds, d) in zip(axes, data.items()):
    vals = [d[k] for k in order_keys]
    colors = ["#c0392b" if v > 0 else "#2471a3" for v in vals]
    y = np.arange(len(order_keys))[::-1]
    ax.barh(y, vals, color=colors, height=0.6)
    ax.set_yticks(y); ax.set_yticklabels(order_keys, fontsize=9)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title(ds, fontsize=10)
    ax.set_xlabel("change in the reported contrast (%)", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    for yy, v in zip(y, vals):
        off = 12 if v >= 0 else -12
        ax.text(v + off, yy, "%+.0f%%" % v, va="center",
                ha="left" if v >= 0 else "right", fontsize=8)
    ax.grid(axis="x", ls=":", lw=0.5, alpha=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axes[0].set_xlim(-520, 520)
fig.tight_layout()
out = r"E:\桌面\rul\rul_v4_20261107\docs\figures\sensitivity_budget.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=300, bbox_inches="tight")
print("saved", out)
