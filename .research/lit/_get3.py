# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.environ.get('TEMP',''), 'pylit'))
from pypdf import PdfReader
p = r"E:\桌面\rul\rul_v4_20261107\.research\lit\peng_energies.pdf"
rd = PdfReader(p)
txt = "\n".join((pg.extract_text() or "") for pg in rd.pages)
open(p.replace('.pdf','.txt'),'w',encoding='utf-8').write(txt)
print("pages", len(rd.pages), "chars", len(txt))
