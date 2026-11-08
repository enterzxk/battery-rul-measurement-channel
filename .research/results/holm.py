# -*- coding: utf-8 -*-
"""Corrected Holm: cumulative maximum over sorted p-values (CD-013 fix)."""
import numpy as np

def holm(pvals):
    p = np.asarray(pvals, float); n = len(p)
    order = np.argsort(p); adj = np.empty(n); running = 0.0
    for i, idx in enumerate(order):
        running = max(running, p[idx] * (n - i))
        adj[idx] = min(1.0, running)
    return adj
