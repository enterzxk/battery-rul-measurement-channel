import re
raw = open("zhao_view.html", encoding="utf-8", errors="ignore").read()
print("LEN", len(raw))
for m in re.finditer(r'(download|galley|pdf)', raw, re.I):
    s=max(0,m.start()-150); e=min(len(raw), m.end()+150)
    print("...", re.sub(r"\s+"," ",raw[s:e]), "...")
    print("-"*50)
