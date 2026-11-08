# -*- coding: utf-8 -*-
import os, sys, urllib.request
sys.path.insert(0, os.path.join(os.environ.get('TEMP',''), 'pylit'))
from pypdf import PdfReader
outdir = r"E:\桌面\rul\rul_v4_20261107\.research\lit"
os.makedirs(outdir, exist_ok=True)
p = os.path.join(outdir, "scirep_ref.pdf")
if not (os.path.exists(p) and os.path.getsize(p) > 100000):
    req = urllib.request.Request("https://www.nature.com/articles/s41598-026-73878-w_reference.pdf", headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(p,'wb') as f:
        f.write(r.read())
rd = PdfReader(p)
txt = "\n".join((pg.extract_text() or "") for pg in rd.pages)
open(p.replace('.pdf','.txt'),'w',encoding='utf-8').write(txt)
print("pages", len(rd.pages), "chars", len(txt))
