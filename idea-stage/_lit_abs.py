
import json, os
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
recs = json.load(open(os.path.join(OUT, "screened.json"), encoding="utf-8"))
want = [
 "Few-Shot Cross Domain Battery Capacity Estimation",
 "When Labels Shift",
 "A Meta-Learning Method for Few-Shot Multidomain State-of-Health",
 "Multisource Domain Metalearning Network for Battery",
 "Battery Life Prediction Under Few-Shot Conditions",
 "Early Prediction of Lithium-Ion Batteries Lifetime via Few-Shot Learning",
 "Battery State of health estimation with fewer labelled data",
 "Online state",
 "Semi-supervised battery state of health estimation for field applications",
 "Adaptive State-of-Health Estimation for Lithium-Ion Battery With Partially Unlabeled",
 "Investigating explainable transfer learning for battery lifetime prediction under state transitions",
 "Enabling Accurate Battery Remaining Useful Life Prediction and Through-Life Degradation Mapping",
 "Capacity Estimation of Cross Domain Lithium-ion Battery Based on Semi-Supervised",
 "Domain Similarity Meta-Learning for Lithium-Ion Battery",
 "PLT-GRU",
 "A novel two-stage heterogeneous transfer learning framework",
 "Multisource Weighted Domain Adaptation for Cross-Conditions Capacity Estimation",
 "Predictive Battery Health Management With Transfer Learning and Online Model Correction",
 "A Transferable Prediction Approach for the Remaining Useful Life of Lithium-Ion Batteries Based on Small Sample",
]
seen = set()
for w in want:
    for r in recs:
        if w.lower() in (r["title"] or "").lower() and r["title"] not in seen:
            seen.add(r["title"])
            print("### " + r["title"])
            print("    %s | %s | %s | cites=%s | %s" % (r["year"], r["venue"], ", ".join(r["authors"][:6]), r["cites"], r["doi"]))
            ab = (r["abstract"] or "").replace("\n", " ")
            print("    ABS: " + (ab[:1100] if ab else "(no abstract in OpenAlex)"))
            print()
            break
