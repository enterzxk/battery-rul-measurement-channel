
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
def cr(q, rows=2):
    try:
        j = S.get("https://api.crossref.org/works", params={"query.bibliographic": q, "rows": rows,
              "select": "title,author,issued,container-title,DOI,type"}, timeout=60).json()
    except Exception as e:
        print("ERR", q, str(e)[:100]); return
    print("Q:", q)
    for it in j["message"]["items"][:rows]:
        au = ", ".join((a.get("family","") + " " + a.get("given","")[:1]) for a in it.get("author", [])[:5])
        yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print("   %s | %s | %s | %s | %s" % (yr, (it.get("title") or [""])[0][:95],
              (it.get("container-title") or [""])[0][:40], it.get("DOI"), au))
    time.sleep(0.4)

for q in ["A theory of learning from different domains Ben-David Blitzer",
          "Frustratingly easy domain adaptation Daume",
          "Accurate uncertainties for deep learning using calibrated regression Kuleshov",
          "Deep learning scaling is predictable empirically Hestness",
          "Revisiting the unreasonable effectiveness of data Sun",
          "Machine learning pipeline for battery state-of-health estimation Roman",
          "Data-driven prediction of battery cycle life before capacity degradation Severson",
          "Closed-loop optimization of fast-charging protocols for batteries Attia",
          "Estimation of Li-ion degradation test sample sizes required to understand cell-to-cell variability Dechent",
          "Few-Shot Cross Domain Battery Capacity Estimation Zhou",
          "A Meta-Learning Method for Few-Shot Multidomain State-of-Health Estimation of Lithium-Ion Batteries",
          "Multisource Domain Metalearning Network for Battery State-of-Health Estimation Under Multitarget Working Conditions",
          "Domain Similarity Meta-Learning for Lithium-Ion Battery State-of-Health Estimation of Spacecraft Systems",
          "Enabling Accurate Battery Remaining Useful Life Prediction and Through-Life Degradation Mapping With Scarce End-of-Life Samples",
          "Multisource Weighted Domain Adaptation for Cross-Conditions Capacity Estimation of Lithium-Ion Batteries",
          "Investigating explainable transfer learning for battery lifetime prediction under state transitions",
          "Semi-supervised battery state of health estimation for field applications",
          "BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction",
          "Battery lifetime prediction across diverse ageing conditions with inter-cell deep learning",
          "Increasing generalization capability of battery health estimation using continual learning"]:
    cr(q)
