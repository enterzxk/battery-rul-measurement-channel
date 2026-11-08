
import os, sys, re, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
def strip(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    import html as H
    h = H.unescape(h); return re.sub(r"\s+", " ", h)
for u in ["https://ouci.dntb.gov.ua/en/?s=10.1016%2Fj.jechem.2023.10.056",
          "https://www.semanticscholar.org/search?q=limited%20labels%20domain%20adaptation%20battery"]:
    try:
        r = S.get(u, timeout=60)
        t = strip(r.text)
        print(u, r.status_code, len(t))
        i = t.lower().find("abstract")
        print(t[max(0,i-200):i+900] if i > 0 else t[:700])
        print("-----")
    except Exception as e:
        print("ERR", u, str(e)[:100])
