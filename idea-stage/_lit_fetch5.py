
import os, re, sys, io, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pypdf import PdfReader
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0"})

def getpdf(url, name):
    p = os.path.join(OUT, name + ".pdf")
    if not os.path.exists(p):
        r = S.get(url, timeout=180)
        if r.content[:4] != b"%PDF":
            print("NOTPDF", name, r.status_code, len(r.content)); return None
        open(p, "wb").write(r.content)
    rd = PdfReader(p)
    txt = "\n".join((x.extract_text() or "") for x in rd.pages)
    open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8").write(txt)
    print("%-22s pages=%d chars=%d" % (name, len(rd.pages), len(txt)))
    return txt

a = getpdf("https://arxiv.org/pdf/2107.07881", "arxiv_2107_sample_size")
b = getpdf("https://arxiv.org/pdf/2603.24475", "arxiv_2603_conformal_transfer")
c = getpdf("https://arxiv.org/pdf/2502.18807", "arxiv_2502_batterylife")

# local BatteryLife KDD pdf
loc = r"E:\桌面\rul\rul_v4_20261107\docs\papers\3711896.3737372.pdf"
rd = PdfReader(loc); txt = "\n".join((x.extract_text() or "") for x in rd.pages)
open(os.path.join(OUT, "batterylife_kdd.txt"), "w", encoding="utf-8").write(txt)
print("batterylife_kdd pages=%d chars=%d" % (len(rd.pages), len(txt)))
for kw in ["few-shot", "shot", "k-shot", "label", "fine-tun", "cross-domain"]:
    print("  ", kw, len(re.findall(kw, txt, re.I)))

loc2 = r"E:\桌面\rul\rul_v4_20261107\docs\papers\s42256-024-00972-x.pdf"
rd = PdfReader(loc2); t2 = "\n".join((x.extract_text() or "") for x in rd.pages)
open(os.path.join(OUT, "batlinet.txt"), "w", encoding="utf-8").write(t2)
print("batlinet pages=%d chars=%d" % (len(rd.pages), len(t2)))
for kw in ["few-shot", "shot", "reference cell", "labeled", "label"]:
    print("  ", kw, len(re.findall(kw, t2, re.I)))
