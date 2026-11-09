import re, html
raw = open("batlinet_arxiv.html", encoding="utf-8", errors="ignore").read()
txt = re.sub(r"<script.*?</script>|<style.*?</style>"," ",raw,flags=re.S|re.I)
txt = html.unescape(re.sub(r"<[^>]+>"," ",txt))
txt = re.sub(r"\s+"," ",txt)
open("batlinet_arxiv.txt","w",encoding="utf-8").write(txt)
print("CHARS", len(txt))
for kw in ["64", "sixty-four", "reference cell", "median prediction", "inference", "source-side", "number of reference"]:
    print("\n#####", kw, txt.count(kw))
    for m in list(re.finditer(re.escape(kw), txt))[:6]:
        s=max(0,m.start()-260); e=min(len(txt), m.end()+260)
        print("  ...", txt[s:e], "...")
