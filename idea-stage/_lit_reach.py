
import os, requests, json
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
urls = [
 ("ACM_SemiJDOT_2021", "https://doi.org/10.1145/3460418.3480409"),
 ("ACE_WhenLabelsShift_2026", "https://doi.org/10.54254/2755-2721/2026.ld37070"),
 ("TTE_metalearning_2024", "https://doi.org/10.1109/tte.2024.3470551"),
 ("TPEL_MSDMLN_2025", "https://doi.org/10.1109/tpel.2025.3538469"),
 ("TII_scarceEOL_2026", "https://doi.org/10.1109/tii.2026.3658872"),
 ("arXiv_2107.07881", "https://arxiv.org/abs/2107.07881"),
 ("arXiv_2603.24475", "https://arxiv.org/abs/2603.24475"),
 ("arXiv_2502.18807", "https://arxiv.org/abs/2502.18807"),
]
for name, u in urls:
    try:
        r = S.get(u, timeout=45, allow_redirects=True)
        print("%-24s %s len=%d final=%s" % (name, r.status_code, len(r.content), r.url[:90]))
    except Exception as e:
        print("%-24s ERR %s" % (name, str(e)[:120]))
