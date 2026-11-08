
import os, re, requests, io
from pypdf import PdfReader
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
u = "https://ace.ewapub.com/article/view/37070.pdf"
r = S.get(u, timeout=120)
print(r.status_code, len(r.content), r.headers.get("content-type"))
if r.content[:4] == b"%PDF":
    open(os.path.join(OUT, "when_labels_shift.pdf"), "wb").write(r.content)
    rd = PdfReader(io.BytesIO(r.content))
    txt = "\n".join((p.extract_text() or "") for p in rd.pages)
    open(os.path.join(OUT, "when_labels_shift.txt"), "w", encoding="utf-8").write(txt)
    print("pages", len(rd.pages), "chars", len(txt))
    for kw in ["shot", "label", "budget", "MAE", "Table"]:
        print(kw, len(re.findall(kw, txt, re.I)))
