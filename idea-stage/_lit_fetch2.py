
import os, re, requests, io
from pypdf import PdfReader
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

# find pdf link on ACE page
r = S.get("https://ace.ewapub.com/article/view/37070", timeout=60)
links = re.findall(r'href="([^"]*)"', r.text)
cand = [l for l in links if "pdf" in l.lower() or "download" in l.lower()]
print("PDF candidates:", cand[:10])
for l in cand:
    if "pdf" in l.lower():
        url = l if l.startswith("http") else "https://ace.ewapub.com" + l
        try:
            pr = S.get(url, timeout=90)
            print("try", url, pr.status_code, len(pr.content), pr.headers.get("content-type"))
            if pr.content[:4] == b"%PDF":
                open(os.path.join(OUT, "when_labels_shift.pdf"), "wb").write(pr.content)
                rd = PdfReader(io.BytesIO(pr.content))
                txt = "\n".join((p.extract_text() or "") for p in rd.pages)
                open(os.path.join(OUT, "when_labels_shift.txt"), "w", encoding="utf-8").write(txt)
                print("pages", len(rd.pages), "chars", len(txt))
                break
        except Exception as e:
            print("ERR", url, str(e)[:100])
