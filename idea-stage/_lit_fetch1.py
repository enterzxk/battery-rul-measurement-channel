
import os, re, json, io, requests
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
os.makedirs(OUT, exist_ok=True)
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def html2text(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|div|h[1-6]|li|tr)>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    import html as H
    h = H.unescape(h)
    h = re.sub(r"[ \t]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()

# 1) ACE "When Labels Shift"
r = S.get("https://ace.ewapub.com/article/view/37070", timeout=60)
t = html2text(r.text)
open(os.path.join(OUT, "when_labels_shift.txt"), "w", encoding="utf-8").write(t)
print("=== ACE len", len(t))
for kw in ["shot", "label", "MAE", "k =", "budget"]:
    ms = [m.start() for m in re.finditer(kw, t, re.I)][:6]
    print("--", kw, "hits:", len(re.findall(kw, t, re.I)))
print(t[:1500])
