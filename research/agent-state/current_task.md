# Current research task — battery-rul-donor-allocation

- Stage: **S0 Repository Audit** (visit 1)
- Status: active
- Goal: Finish submission preparation for the battery-RUL donor-allocation manuscript (docs/manuscripts/v4.0-tim.md): P0-1 verify the Peng 2026 Energies paper (doi:10.3390/en19204805) against the original text, and P0-2 re-run the integrity audit on the post-remediation manuscript. Then P1 submission form (LaTeX, figure caption).

## Active task

- **Close the remaining integrity blockers before any submission work**
- P0 complete. Peng 2026 verified from the original 29-page PDF: the manuscript's Reference 5 title was fabricated, all cited numbers are correct, but Peng already contains a 2x2 factorial so the manuscript's differentiation claim fails. Integrity re-audit returned SERIOUS-ISSUES with three new FAILs: (A) the Section 5 +274% 'fit scope' effect is a single-draw Monte-Carlo artefact (matched-draw row-budget effect is +32%), (B) the ISU Section 5 scan compared 233 vs 223 evaluated cells, (C) Section 4.5 selection is not nested leave-one-out. 16 items fixed; 7 remain blocking.

## Next actions

1. Finish the common-support ISU re-run (isu_budget_common.py) and fold the corrected numbers into Section 5
2. Re-run Section 4.5 selection with proper nesting: for each outer fold g use only the model trained without g
3. Recompute the Ridge donor-effect Holm family using training-fold-internal standardisation (utility2.py), not controls.py
4. Recompute the Section 4.3 cell-macro condition-improvement counts, or mark 2/11 and 0/11 as unverified
5. State the MDE in cycle units or label it as RPT-scale
6. Redraw Figure 1 without the withdrawn fit-scope and row-allocation labels
7. Trim the abstract to 250 words (currently 287) before LaTeX conversion
8. Record the reset, preserve the corrected donor results and falsified claims, classify v4.1 as exploratory and not submission-ready, stop manuscript polishing as the main activity
9. Time-box a 48-hour discovery cycle on the EOL-value question against full primary sources, including the most recent six months
10. Produce a four-axis comparison: problem assumptions, mechanism, required information, demonstrated result
11. Define the operational decision (which donor tests to continue, when calibration may occur, what deployment deadline) before selecting any method
12. Require independent literature and novelty review before any experiment
13. Freeze the cohort manifest, event definition, causal features, descriptor distance, randomisation, metric and stopping rule before any fitting
14. Audit event and feature construction: full-life quantities may define outcomes but must not enter predictors or procurement decisions
15. Run the complete matched experiment once on CPU and retain every arm, condition, draw and query-level prediction
16. If the gate fails, archive and stop the headline; if it passes, preregister the next budget comparison and a feasible UConn analogue
17. Correct the EXP-031 result record to downgrade it from a citable negative to an as-run exploratory record (done)
18. Complete the data-admission audit: locate the 248-cell ISU source, or mark every ISU-based conclusion as provenance-untraced
19. Do not run any further experiment on the ISU table until its source is identified
20. If reconstruction is pursued, use UConn (descriptors + timestamps recoverable) but note it has only 11 conditions, insufficient for a condition-level allocation study
21. Write the auditable closure report with a claim-to-evidence register
22. Record every failed gate, unfavourable result and implementation deviation without softening
23. Correct my own three overstated claims (consortium independence, allocation-vs-selection conflation, uncontrolled Jaccard comparison)
24. Preserve the recovered condition table and provenance bundle
25. Do not select another budget, policy, window, seed or subgroup to manufacture a publishable result

## Selected idea

_none selected yet_

## Resume

Read research/agent-state/current_task.md, verify its artifacts still exist, then continue with next action 1.

