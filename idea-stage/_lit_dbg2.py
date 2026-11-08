
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
r = S.get("https://api.crossref.org/works", params={"query.bibliographic": "few-shot battery state of health estimation", "rows": 10}, timeout=60)
print("status", r.status_code, "len", len(r.text))
j = r.json()
print("total", j["message"]["total-results"])
for it in j["message"]["items"][:10]:
    print(" ", (it.get("issued", {}).get("date-parts") or [[None]])[0][0], "|", (it.get("title") or [""])[0][:90], "|", it.get("DOI"))
