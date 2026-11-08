
import os, sys, json, time, re, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
dois = ["10.1016/j.energy.2023.126726", "10.1016/j.joule.2024.02.020", "10.1016/j.egyai.2022.100174",
        "10.1002/batt.202100148", "10.1109/pesim67009.2026.11438910", "10.1016/j.esci.2024.100280"]
for d in dois:
    try:
        j = S.get("https://api.crossref.org/works/" + d, timeout=60).json()["message"]
    except Exception as e:
        print("ERR", d, str(e)[:100]); continue
    au = ", ".join((a.get("family","") + " " + a.get("given","")[:1]) for a in j.get("author", [])[:6])
    yr = (j.get("issued", {}).get("date-parts") or [[None]])[0][0]
    print("### %s" % d)
    print("   %s | %s" % (yr, (j.get("title") or [""])[0]))
    print("   %s | %s" % ((j.get("container-title") or [""])[0], au))
    ab = j.get("abstract") or ""
    ab = re.sub(r"<[^>]+>", " ", ab); ab = re.sub(r"\s+", " ", ab)
    print("   ABS:", ab[:1200] if ab else "(none in Crossref)")
    print()
    time.sleep(0.3)
