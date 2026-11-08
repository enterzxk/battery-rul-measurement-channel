
import os, re, requests
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
r = S.get("https://ace.ewapub.com/article/view/37070", timeout=60)
h = r.text
for m in re.finditer(r"Download PDF", h):
    print(repr(h[max(0,m.start()-400):m.start()+200]))
    print("-----")
print("any '37070/' patterns:", sorted(set(re.findall(r"37070[/\w\.-]*", h)))[:20])
print("pdf-ish:", sorted(set(re.findall(r"[\w/\.:-]*\.pdf", h)))[:20])
