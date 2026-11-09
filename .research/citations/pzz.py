import fitz, re
d = fitz.open("zhao.pdf")
t = "".join(p.get_text() for p in d)
open("zhao_pdf.txt","w",encoding="utf-8").write(t)
print("PAGES", d.page_count, "CHARS", len(t))
flat = re.sub(r"\s+"," ",t)
for kw in ["five","ten","twenty","budget","target cell"]:
    print("\n#####", kw, flat.lower().count(kw.lower()))
    for m in list(re.finditer(kw, flat, re.I))[:5]:
        s=max(0,m.start()-230); e=min(len(flat), m.end()+230)
        print("  ...", flat[s:e], "...")
