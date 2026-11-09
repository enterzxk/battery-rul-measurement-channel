"""OpenAlex discovery sweep for prior-art check A (rate-limit tolerant).

Writes incrementally to sweep.log so progress is visible; dumps sweep_out.json.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.openalex.org/works"
SEL = "id,doi,title,publication_year,authorships,primary_location,type,cited_by_count,open_access"
MAIL = "research-lit-check@example.org"

QUERIES = [
    dict(q="interval censored end of life lithium-ion battery lifetime", tag="ic"),
    dict(q="interval-censored degradation threshold crossing battery", tag="ic"),
    dict(q="first hitting time lithium-ion battery remaining useful life", tag="fht"),
    dict(q="threshold crossing Wiener process battery remaining useful life", tag="fht"),
    dict(q="irregular sampling remaining useful life prediction lithium battery", tag="irr"),
    dict(q="asynchronous measurement state of health estimation battery", tag="irr"),
    dict(q="non-uniform time interval degradation modeling battery prognostics", tag="irr"),
    dict(q="missing data imputation battery state of health random interval", tag="irr"),
    dict(q="ampere-hour throughput degradation model lithium-ion battery lifetime", tag="exp"),
    dict(q="equivalent full cycle lifetime model battery aging", tag="exp"),
    dict(q="continuous-time degradation state space model battery prognostics", tag="ct"),
    dict(q="stochastic differential equation capacity fade lithium-ion battery", tag="ct"),
    dict(q="nonlinear state space particle filter battery remaining useful life", tag="pf"),
    dict(q="multiscale adaptive filtering battery state of health", tag="mars"),
    dict(q="multiscale adaptive recursive smoothing battery", tag="mars"),
    dict(q="MARS multivariate adaptive regression splines battery", tag="mars"),
    dict(q="multi-timescale adaptive observer lithium-ion battery", tag="mars"),
    dict(q="online recursive state of health estimation periodic check-up battery", tag="onl"),
    dict(q="Bayesian online updating remaining useful life battery check-up", tag="onl"),
    dict(q="recursive latent health state estimation battery capacity", tag="onl"),
    dict(q="cross-condition transfer remaining useful life battery operating condition", tag="xfer"),
    dict(q="domain generalization battery health prognostics operating condition shift", tag="xfer"),
    dict(q="transfer learning remaining useful life unseen operating condition lithium", tag="xfer"),
    dict(q="effect of sampling frequency on battery state of health estimation accuracy", tag="eval"),
    dict(q="inspection interval maintenance prognostics remaining useful life censoring", tag="eval"),
    dict(q="right censoring remaining useful life estimation field data battery", tag="eval"),
]


def get(url, tries=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (mailto:%s)" % MAIL})
            with urllib.request.urlopen(req, timeout=50) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(6 * (i + 1))
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def compact(it):
    pl = it.get("primary_location") or {}
    src = (pl.get("source") or {}).get("display_name") or ""
    auths = [a.get("author", {}).get("display_name", "") for a in (it.get("authorships") or [])]
    return {
        "year": it.get("publication_year"),
        "title": it.get("title") or "",
        "doi": (it.get("doi") or "").replace("https://doi.org/", ""),
        "venue": src,
        "authors": auths,
        "cites": it.get("cited_by_count"),
        "oa": (it.get("open_access") or {}).get("oa_url") or "",
        "type": it.get("type"),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for q in QUERIES:
        params = {"search": q["q"], "per-page": "12", "select": SEL,
                  "filter": "from_publication_date:2024-01-01", "mailto": MAIL}
        url = BASE + "?" + urllib.parse.urlencode(params)
        try:
            j = get(url)
            hits, err = [compact(x) for x in j.get("results", [])], None
        except Exception as e:
            hits, err = [], str(e)
        out.append({"query": q["q"], "tag": q["tag"], "error": err, "hits": hits})
        print("\n## [%s] %s" % (q["tag"], q["q"]), flush=True)
        if err:
            print("   ERROR", err, flush=True)
        for h in hits:
            a = h["authors"][0].split()[-1] if h["authors"] else "?"
            print("   %s | %-32s | %-32s | %-88s | %s | c=%s%s" % (
                h["year"], (h["venue"] or "-")[:32], h["doi"], h["title"][:88], a, h["cites"],
                " |OA" if h["oa"] else ""), flush=True)
        time.sleep(1.2)
    with open(os.path.join(here, "sweep_out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nsaved sweep_out.json", flush=True)


main()
