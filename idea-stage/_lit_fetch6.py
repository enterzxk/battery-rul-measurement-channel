
import os, sys, io, re, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pypdf import PdfReader
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
targets = [
 ("eth_batteries_2022", "https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/582225/batteries-08-00204.pdf?isAllowed=y&sequence=3"),
 ("chalmers_thesis", "https://odr.chalmers.se/bitstreams/04a5c071-9950-4f5c-ab89-9be5e7ad5564/download"),
 ("dtu_data_efficient", "https://backend.orbit.dtu.dk/ws/files/309700211/d2dd00067a_1_.pdf"),
]
for name, u in targets:
    try:
        r = S.get(u, timeout=180)
        print(name, r.status_code, len(r.content), r.headers.get("content-type"))
        if r.content[:4] != b"%PDF":
            print("  not pdf"); continue
        open(os.path.join(OUT, name + ".pdf"), "wb").write(r.content)
        rd = PdfReader(io.BytesIO(r.content))
        txt = "\n".join((p.extract_text() or "") for p in rd.pages)
        open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8").write(txt)
        print("  pages=%d chars=%d" % (len(rd.pages), len(txt)))
        print("  head:", re.sub(r"\s+", " ", txt[:400]))
    except Exception as e:
        print(name, "ERR", str(e)[:150])
