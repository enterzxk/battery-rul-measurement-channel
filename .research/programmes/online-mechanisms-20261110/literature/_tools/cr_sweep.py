"""Crossref discovery sweep for prior-art check A.

Crossref is used as the discovery engine because it is keyless and rate-tolerant.
Each query is a mechanism axis. Results are deduped by DOI and printed per query.
"""
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://api.crossref.org/works"
UA = "lit-review/1.0 (mailto:research-lit-check@example.org)"

QUERIES = [
    # axis: interval censoring / EOL interval
    ("ic", "interval censored end of life lithium-ion battery lifetime"),
    ("ic", "interval censored degradation threshold crossing remaining useful life"),
    ("ic", "end-of-life interval estimation lithium-ion battery Wiener process"),
    ("ic", "progressive censoring battery aging lifetime reliability"),
    # axis: first hitting time
    ("fht", "first hitting time threshold remaining useful life lithium battery"),
    ("fht", "Wiener process degradation model battery remaining useful life"),
    # axis: irregular / asynchronous observation
    ("irr", "irregular sampling remaining useful life prediction lithium battery"),
    ("irr", "asynchronous measurement state of health estimation lithium battery"),
    ("irr", "non-uniform time interval degradation modeling battery prognostics"),
    ("irr", "missing observation battery state of health estimation irregular"),
    ("irr", "sparse measurement health indicator battery online estimation"),
    # axis: exposure / throughput axis
    ("exp", "ampere-hour throughput degradation lithium-ion battery lifetime model"),
    ("exp", "equivalent full cycle aging model lithium-ion battery"),
    ("exp", "charge throughput based aging battery lifetime prediction"),
    ("exp", "physics-based aging model stress factors lithium-ion battery lifetime"),
    # axis: continuous-time state space / filtering
    ("ct", "continuous-time state space degradation model battery prognostics"),
    ("ct", "stochastic differential equation capacity fade lithium-ion battery"),
    ("ct", "particle filter remaining useful life battery online updating"),
    ("ct", "recursive Bayesian filtering state of health battery capacity"),
    # axis: multiscale adaptive / MARS
    ("mars", "multiscale adaptive filtering battery state of health"),
    ("mars", "multi-timescale adaptive observer lithium-ion battery state"),
    ("mars", "multiscale adaptive robust state estimation battery health lifetime"),
    # axis: online check-up / RPT
    ("onl", "online state of health estimation reference performance test battery"),
    ("onl", "periodic check-up capacity measurement battery remaining useful life update"),
    ("onl", "real-time updating remaining useful life battery field data"),
    # axis: cross-condition transfer
    ("xfer", "cross-condition transfer remaining useful life battery operating condition"),
    ("xfer", "domain generalization battery health estimation operating condition"),
    ("xfer", "transfer learning remaining useful life unseen operating condition"),
    # axis: evaluation protocol / sampling
    ("eval", "effect of sampling interval on battery state of health estimation accuracy"),
    ("eval", "inspection interval prognostics remaining useful life censoring"),
    ("eval", "right censoring remaining useful life estimation field battery data"),
    ("eval", "benchmark evaluation protocol leakage battery health estimation"),
]


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=50) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 + 3 * i)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    seen = {}
    blocks = []
    for tag, q in QUERIES:
        params = {
            "query.bibliographic": q,
            "rows": "10",
            "select": "DOI,title,container-title,issued,author,type,is-referenced-by-count",
            "filter": "from-pub-date:2024-01-01",
        }
        url = BASE + "?" + urllib.parse.urlencode(params)
        try:
            j = get(url)
            items = j["message"]["items"]
            err = None
        except Exception as e:
            items, err = [], str(e)
        hits = []
        for it in items:
            doi = it.get("DOI", "")
            title = " ".join(it.get("title") or [""]).strip()
            title = " ".join(title.split())
            yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            ven = " ".join(it.get("container-title") or [""])
            auth = ""
            if it.get("author"):
                a0 = it["author"][0]
                auth = (a0.get("family") or a0.get("name") or "")
            hits.append({"doi": doi, "title": title, "year": yr, "venue": ven,
                         "first_author": auth, "cites": it.get("is-referenced-by-count")})
            if doi not in seen:
                seen[doi] = hits[-1]
        blocks.append({"tag": tag, "query": q, "error": err, "hits": hits})
        print("\n## [%s] %s" % (tag, q), flush=True)
        if err:
            print("   ERROR", err, flush=True)
        for h in hits:
            print("   %s | %-30s | %-34s | %-88s | %s" % (
                h["year"], (h["venue"] or "-")[:30], h["doi"], h["title"][:88], h["first_author"]), flush=True)
        time.sleep(0.6)

    with open(os.path.join(here, "cr_sweep.json"), "w", encoding="utf-8") as f:
        json.dump({"blocks": blocks, "unique": list(seen.values())}, f, ensure_ascii=False, indent=1)
    print("\nUNIQUE DOIs:", len(seen), flush=True)


main()
