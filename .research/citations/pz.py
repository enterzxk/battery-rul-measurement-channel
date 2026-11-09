import re, html
raw = open("zhao.html", encoding="utf-8", errors="ignore").read()
print("LEN", len(raw))
# title
for pat in [r"<title>(.*?)</title>", r'citation_title" content="(.*?)"', r'citation_doi" content="(.*?)"']:
    m = re.search(pat, raw, re.S|re.I)
    print(pat, "->", html.unescape(m.group(1)).strip() if m else None)
# abstract
m = re.search(r'citation_abstract" content="(.*?)"', raw, re.S|re.I)
if not m:
    m = re.search(r'name="description" content="(.*?)"', raw, re.S|re.I)
print("\nABSTRACT:", html.unescape(m.group(1))[:2000] if m else "NONE")
txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S|re.I)
txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
txt = re.sub(r"\s+", " ", txt)
print("\n--- looking for 5/10/20 / budget ---")
for kw in ["five", "ten", "twenty", "budget", "domain adaptation", "cycle life", "target cell"]:
    for mm in re.finditer(kw, txt, re.I):
        s=max(0,mm.start()-180); e=min(len(txt), mm.end()+180)
        print(f"[{kw}] ...{txt[s:e]}...")
        break
open("zhao_text.txt","w",encoding="utf-8").write(txt)
print("\nSAVED zhao_text.txt chars:", len(txt))
