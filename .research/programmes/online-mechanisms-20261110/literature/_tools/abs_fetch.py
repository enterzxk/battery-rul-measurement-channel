"""Batch abstract/metadata fetch via Semantic Scholar, with OpenAlex fallback.

Usage: python abs_fetch.py dois.txt out.json
Prints per-DOI: title, year, venue, abstract (truncated), OA pdf url.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "lit-review/1.0 (mailto:research-lit-check@example.org)"
FIELDS = "title,abstract,year,venue,publicationVenue,openAccessPdf,externalIds,citationCount,tldr,authors"


def get(url, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(5 * (i + 1))
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def inv(x):
    if not x:
        return ""
    p = {}
    for w, ii in x.items():
        for i in ii:
            p[i] = w
    return " ".join(p[i] for i in sorted(p))


def s2_doi(doi):
    u = "https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi) + "?fields=" + FIELDS
    return get(u)


def s2_title(title):
    u = ("https://api.semanticscholar.org/graph/v1/paper/search?" +
         urllib.parse.urlencode({"query": title, "limit": "3", "fields": FIELDS}))
    return get(u)


def oa_doi(doi):
    u = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) + "?mailto=research-lit-check@example.org"
    return get(u)


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    items = [l.strip() for l in open(src, encoding="utf-8") if l.strip() and not l.startswith("#")]
    recs = []
    for key in items:
        rec = {"key": key}
        if key.startswith("10."):
            rec["doi"] = key
            try:
                s = s2_doi(key)
                rec["s2"] = {k: s.get(k) for k in ("title", "year", "venue", "abstract", "citationCount")}
                rec["s2"]["oaPdf"] = (s.get("openAccessPdf") or {}).get("url")
                rec["s2"]["tldr"] = (s.get("tldr") or {}).get("text")
            except Exception as e:
                rec["s2_error"] = str(e)
            try:
                o = oa_doi(key)
                rec["oa"] = {"title": o.get("title"), "year": o.get("publication_year"),
                             "abstract": inv(o.get("abstract_inverted_index")),
                             "oa": (o.get("open_access") or {}).get("oa_url")}
            except Exception as e:
                rec["oa_error"] = str(e)
        else:
            rec["title_query"] = key
            try:
                r = s2_title(key)
                rec["s2_search"] = [{"title": p.get("title"), "year": p.get("year"),
                                     "venue": p.get("venue"), "doi": (p.get("externalIds") or {}).get("DOI"),
                                     "abstract": p.get("abstract")} for p in r.get("data", [])]
            except Exception as e:
                rec["s2_error"] = str(e)
        recs.append(rec)
        s = rec.get("s2") or {}
        print("\n" + "=" * 96)
        print("KEY:", key)
        print("  title:", s.get("title") or (rec.get("oa") or {}).get("title"))
        print("  year:", s.get("year"), "| venue:", s.get("venue"), "| cites:", s.get("citationCount"))
        print("  oaPdf:", s.get("oaPdf"))
        ab = s.get("abstract") or (rec.get("oa") or {}).get("abstract") or ""
        print("  abs_len:", len(ab))
        if ab:
            print("  ABSTRACT:", " ".join(ab.split())[:1800])
        for p in rec.get("s2_search", []) or []:
            print("  HIT:", p.get("year"), "|", p.get("venue"), "|", p.get("doi"), "|", (p.get("title") or "")[:100])
            if p.get("abstract"):
                print("     ABS:", " ".join(p["abstract"].split())[:1500])
        time.sleep(1.6)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print("\nsaved", dst)


main()
