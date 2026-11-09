import re
raw = open("zhao.html", encoding="utf-8", errors="ignore").read()
links = set(re.findall(r'href="([^"]+)"', raw))
for l in sorted(links):
    if re.search(r"pdf|download|fulltext|article", l, re.I):
        print(l)
