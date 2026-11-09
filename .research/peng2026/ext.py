import fitz, re, sys, json
doc = fitz.open("peng2026.pdf")
print("PAGES:", doc.page_count)
full = []
for i, p in enumerate(doc):
    full.append(f"\n===== PAGE {i+1} =====\n" + p.get_text())
txt = "".join(full)
open("peng2026.txt","w",encoding="utf-8").write(txt)
print("CHARS:", len(txt))
print("META:", json.dumps(doc.metadata, ensure_ascii=False)[:400])
