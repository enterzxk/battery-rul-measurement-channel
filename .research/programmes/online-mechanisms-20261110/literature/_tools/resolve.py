"""Resolve DOIs across Crossref / OpenAlex / Semantic Scholar. Print what each returns.

No fabrication: only prints fields the APIs actually returned.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; lit-check/1.0; mailto:research@example.org)"


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def inv_to_text(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def openalex(doi):
    try:
        d = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    except Exception as e:
        return {"error": str(e)}
    out = {
        "title": d.get("title"),
        "year": d.get("publication_year"),
        "venue": (d.get("primary_location") or {}).get("source", {}) and
                 ((d.get("primary_location") or {}).get("source") or {}).get("display_name"),
        "type": d.get("type"),
        "cited_by": d.get("cited_by_count"),
        "oa": (d.get("open_access") or {}).get("oa_url"),
        "is_oa": (d.get("open_access") or {}).get("is_oa"),
        "abstract": inv_to_text(d.get("abstract_inverted_index")),
        "concepts": [c.get("display_name") for c in (d.get("concepts") or [])][:12],
    }
    return out


def s2(doi):
    url = ("https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi) +
           "?fields=title,abstract,year,venue,openAccessPdf,externalIds,citationCount,publicationVenue,tldr")
    for attempt in range(4):
        try:
            return get(url)
        except Exception as e:
            err = str(e)
            if "429" in err or "timed out" in err.lower():
                time.sleep(4 + 4 * attempt)
                continue
            return {"error": err}
    return {"error": "retries exhausted"}


def main():
    dois = sys.argv[1:]
    for doi in dois:
        print("=" * 100)
        print("DOI:", doi)
        print("-" * 40, "OPENALEX")
        oa = openalex(doi)
        for k in ("title", "year", "venue", "type", "cited_by", "is_oa", "oa"):
            print("  %-9s %s" % (k + ":", oa.get(k)))
        ab = oa.get("abstract") or ""
        print("  abstract_len:", len(ab))
        if ab:
            print("  ABSTRACT:", ab)
        print("-" * 40, "SEMANTIC SCHOLAR")
        s = s2(doi)
        if "error" in s:
            print("  ERROR:", s["error"])
        else:
            print("  title:", s.get("title"))
            print("  year:", s.get("year"), "| venue:", s.get("venue"), "| cites:", s.get("citationCount"))
            print("  oaPdf:", (s.get("openAccessPdf") or {}).get("url"))
            t = s.get("tldr") or {}
            print("  tldr:", t.get("text"))
            sab = s.get("abstract") or ""
            print("  abstract_len:", len(sab))
            if sab and sab != ab:
                print("  ABSTRACT:", sab)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
