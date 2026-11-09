import re
txt = open("batlinet_arxiv.txt", encoding="utf-8").read()
for kw in ["size of 32","32 as the final","Figure 6 b","from 1 to","reference size","group of size"]:
    print("\n#####", kw, txt.count(kw))
    for m in list(re.finditer(re.escape(kw), txt))[:4]:
        s=max(0,m.start()-300); e=min(len(txt), m.end()+300)
        print("  ...", txt[s:e], "...")
