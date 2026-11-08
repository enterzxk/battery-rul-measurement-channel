# -*- coding: utf-8 -*-
import os, sys, re, io, urllib.request
sys.path.insert(0, os.path.join(os.environ.get('TEMP',''), 'pylit'))
from pypdf import PdfReader

outdir = r"E:\桌面\rul\rul_v4_20261107\.research\lit"
os.makedirs(outdir, exist_ok=True)

def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r, open(path,'wb') as f:
        f.write(r.read())
    return path

targets = [
    ("cai_review.pdf", "https://journals.zeuspress.org/index.php/CAI/article/download/1752/1662"),
    ("scirep_2026.pdf", "https://www.nature.com/articles/s41598-026-73878-w.pdf"),
]
for name, url in targets:
    p = os.path.join(outdir, name)
    try:
        get(url, p)
        rd = PdfReader(p)
        txt = "\n".join((pg.extract_text() or "") for pg in rd.pages)
        tp = p.replace('.pdf', '.txt')
        open(tp,'w',encoding='utf-8').write(txt)
        print(f"OK {name}: pages={len(rd.pages)} chars={len(txt)}")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")
