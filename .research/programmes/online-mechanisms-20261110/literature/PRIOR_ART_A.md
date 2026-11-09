# PRIOR_ART_A — novelty check for question A (online, exposure-advanced, interval-censored RUL)

**Programme:** `online-mechanisms-20261110`
**Reviewer:** delegated novelty-check agent (independent context)
**Date:** 2026-11-10
**Scope:** question A as stated in the brief, plus a fast addendum on the pivot to question B (§7) requested mid-review.
**Access:** no institutional access from this session. Elsevier (ScienceDirect) returns HTTP 403; IEEE Xplore returns HTTP 202 with an empty body; Unpaywall reports Johnen 2020 as `closed` with no repository copy; `r.jina.ai` now requires an API key (401). Bibliographic APIs used: Crossref, Semantic Scholar Graph, OpenAlex (rate-limited, HTTP 429 for much of the session).

## Verification legend — read this before trusting any row

| Tag | Meaning |
|---|---|
| **[ABS]** | Abstract read verbatim from a bibliographic API (Semantic Scholar / OpenAlex). Content claims are limited to what the abstract states. |
| **[ABS+SNIP]** | Abstract plus publisher "Highlights" seen only through a search-result snippet (second-hand). |
| **[SNIP]** | Partial abstract seen only through a search-result snippet. |
| **[META]** | Metadata only (title, authors, venue, DOI). **I did not read the content.** Content claims in this row are *not* verified. |
| **[UNVERIFIED]** | Not obtained at all. |

**No full text of any Elsevier or IEEE item was obtained.** Every equation-level statement below is therefore either (a) quoted from an abstract, or (b) explicitly marked unverified. I have not read Johnen's likelihood, MARS's filter equations, or the Measurement/Applied Energy methods.

---

## 0. Bottom line

**A is NO-GO as a novelty claim, on two independent grounds.**

1. **Occupied.** Every constituent of A is individually published, and the composite is covered by two papers taken together: Johnen 2020 (interval-censored EOL likelihood) + BatteryCDE 2025 (irregular sampling / missing observations) + Tao 2026 (measurement-availability-aware sequential updating with explicit uncertainty). No single paper does all five, but the assembly is a routine composition, not a mechanism.
2. **Not identifiable in the available data.** The parent agent reports that on the UConn cohort the within-cell inspection-cadence CV is 0.091 and `cum_cycles ~ rpt` gives R² = 0.999. Under that design "advance by exposure" and "advance per RPT" are algebraically the same model. A paper claiming the exposure axis matters cannot be falsified on this cohort, and a reviewer who asks for the falsification test will end the paper.

**What survives is a negative/measurement result, not a predictor** — see §3, claim **R1**.

---

## 1. Six-axis prior-art matrix

Columns follow the brief: (1) available observations, (2) prediction target, (3) mechanism, (4) loss / likelihood, (5) assumptions, (6) evaluation protocol.

| # | Paper | Available observations | Prediction target | Mechanism | Loss / likelihood | Assumptions | Evaluation protocol | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | **Johnen, Schmitz, Kateri, Kamps 2020**, *Comput. Ind. Eng.* 143:106418, [10.1016/j.cie.2020.106418](https://doi.org/10.1016/j.cie.2020.106418) | Capacity sampled only at pre-defined inspection points in long-term cyclic-ageing experiments; no current/voltage/temperature records used | **Population lifetime distribution** parameters, mean life, quantiles, for several EoL criteria | MLE of Weibull / lognormal / inverse-Gaussian first-passage times from **interval-censored** data | Interval-censored likelihood (exact form not read) | Cells i.i.d. from one parametric family; one stress condition; **no covariate, no per-cell state, no online update** | Simulation study: CI quality under full vs interval-censored information; two inspection designs — equal-length intervals and equal-failure-probability intervals; model-misspecification simulation | [ABS+SNIP] |
| 2 | **Wang, Chang, Fan, Ren, Chen, Li, Dong 2026**, *Measurement* 285:122347, [10.1016/j.measurement.2026.122347](https://doi.org/10.1016/j.measurement.2026.122347) | **UNKNOWN** — no abstract deposited in Crossref, OpenAlex or Semantic Scholar | Title says RUL prediction | Title says "uncertainty-aware adaptive feedback ensemble framework" | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **[META]** |
| 3 | **MARS 2026**, *IEEE Trans. Transport. Electrific.*, [10.1109/tte.2026.3734031](https://doi.org/10.1109/tte.2026.3734031) (Xplore doc 11692676) | Operating data + equivalent-circuit model; dual-branch temporal encoder features | SOH **and** RUL, real-time | Multi-scale adaptive robust state estimation: dual-branch temporal encoder + **ECM-constrained differentiable generalized-correntropy adaptive Kalman filter** | Correntropy-based robust cost + physics (ECM) constraint — *inferred from the abstract wording, not read* | ECM structure valid; non-Gaussian measurement disturbance; operating variability | **UNVERIFIED** (no results read) | [SNIP] |
| 4 | **Oyewole, Hassanieh, Chelbi, Chehade 2025/2026**, *Applied Energy* 402:126880, [10.1016/j.apenergy.2025.126880](https://doi.org/10.1016/j.apenergy.2025.126880) | **UNKNOWN** — no abstract deposited | Title says battery prognostics (RUL) with uncertainty | Title says "physics-informed Bayesian sampling" + deep learning | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **[META]** |
| 5 | **Zhang, Diallo, Delpha, Benbouzid 2026**, *Energy and AI* 25:100771, [10.1016/j.egyai.2026.100771](https://doi.org/10.1016/j.egyai.2026.100771) (OA) | Capacity trajectories from 4 public benchmarks; first 30 % of each target life as history | Capacity forecast → RUL | TimesFM time-series foundation model; zero-shot, source-adapted, target-prefix-adapted | Standard forecasting loss (not specified in abstract) | Regular per-cycle capacity series; **no observation model; no censoring** | 6 pipelines spanning within-dataset and cross-dataset transfer, ± adaptation; prefix-ratio sensitivity 30/20/10 %; recursive prediction of the remaining 70 % | [ABS] |
| 6 | **Shi et al. 2025/2026**, *Sci. Sin. Informationis*, [10.1360/ssi-2025-0356](https://doi.org/10.1360/ssi-2025-0356) | Multi-degradation feature sequences (NASA) | **EOL interval** + dynamic RUL interval "with incomplete degradation data" | Wiener stochastic degradation fused with LSTM | Wiener first-passage + NN (not read) | Brownian degradation; NASA cell set | NASA dataset; EOL-interval accuracy; claimed "consistent across diverse conditions" | [ABS] |
| 7 | **Xiao et al. 2026**, *Entropy* 28(10):1108, [10.3390/e28101108](https://doi.org/10.3390/e28101108) (OA) | Accelerated-ageing lifetimes under **adaptive progressive Type-II censoring**; NASA 4 °C cycling | Lifetime distribution / reliability (population), not per-cell online RUL | Power-Rayleigh lifetime + APT-II censoring; MLE (multi-start L-BFGS) and Metropolis–Hastings MCMC | Censored likelihood (MLE and Bayesian) | Homogeneous cell subpopulation, uniform conditions | Monte-Carlo simulation; HPD vs asymptotic coverage (HPD ~12 % narrower at nominal coverage); sensitivity to one extreme cell | [ABS] |
| 8 | **BatteryCDE 2025**, *IEEE Trans. Transport. Electrific.*, [10.1109/tte.2025.3547740](https://doi.org/10.1109/tte.2025.3547740) | Capacity series with **irregular sampling and missing data (up to 50 %)** | Capacity (→SOH), long-horizon (100 cycles) | Neural **controlled differential equations** + feature-wise/cycle-wise attention; cubic-spline continuous data path | Regression loss (not specified) | Continuous latent path; spline interpolation valid | 3 scenarios: estimation horizon, missing data, cross-battery transfer; error < 0.05 throughout | [ABS] |
| 9 | **Tao et al. 2026**, *Meas. Sci. Technol.*, [10.1088/1361-6501/aeb0bc](https://doi.org/10.1088/1361-6501/aeb0bc) (OA) | **Sparse-frequency EIS** (3–6 frequencies); archived full spectra masked so that revealing one frequency simulates a prospective measurement | SOH + 90 % prediction intervals | Uncertainty-aware, **offline-calibrated sequential measurement protocol**; frequency selection by expected error reduction vs interval width vs modelled acquisition cost | Expected SOH-error reduction vs cost with weights λ_w, λ_t; conformal intervals | Archived spectra representative; exchangeability for conformal | 3 datasets; MAE, empirical coverage, modelled relative acquisition cost; **explicitly reports failure of uncertainty transfer under domain shift (coverage 0.57)** | [ABS] |
| 10 | **Xia et al. 2026**, *Applied Energy*, [10.1016/j.apenergy.2025.127026](https://doi.org/10.1016/j.apenergy.2025.127026) | **UNKNOWN** — no abstract deposited | Title: RUL, "from a probabilistic view" | "Life-decomposition-based" | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **[META]** — flagged, unread |

Rows 2, 4 and 10 are the mandatory-competitor set the brief asked me to clear. **I could not clear them**: three of the five named competitors have no deposited abstract, and neither publisher page is reachable from this session. That is a hard limitation of this review, not a judgement that they are irrelevant.

---

## 2. Per-paper: what it does / what it does NOT do

**1. Johnen et al. 2020 — the single most dangerous paper for A.**
*Does:* takes exactly A's observation model seriously — capacity is measured only at inspection points, so the EOL crossing time is known only up to an interval — and derives MLEs for Weibull, lognormal and inverse-Gaussian lifetime distributions under that interval censoring, then quantifies how much CI quality is lost relative to full information. It even studies **inspection-interval design** (equal-length vs equal-failure-probability intervals), which is the design question A implies.
*Does not:* model a per-cell degradation **state** or a stress/exposure process; there is no current/voltage/temperature input, no covariate, no recursive update, no per-cell RUL, and no cross-condition transfer. It is a **population reliability** paper: one parametric family, one stress condition, i.i.d. cells, offline batch estimation. It also does not address **right**-censoring of still-alive cells as a prediction target — the deliverable is a fitted lifetime distribution.
*Why it still hurts A:* A's most distinctive likelihood — `P(L < T_EOL ≤ U | H_t)` — is Johnen's likelihood. A would have to argue that adding a per-cell state and covariates changes the inferential object, which is true but is an application, not a mechanism.

**2. Wang et al. 2026 (Measurement 285:122347) — cannot be assessed.**
*Does:* per the title, an uncertainty-aware adaptive feedback **ensemble** framework for RUL.
*Does not:* unknown. **Note a discrepancy worth resolving before it enters any related-work section:** the brief describes this paper as "latent health recursive estimation", but the registered title contains no such phrase and describes an ensemble. Either the brief's characterisation is wrong, or it refers to a different paper. I could not resolve which.
*Action:* obtain the PDF through institutional access before citing it at all.

**3. MARS 2026 (IEEE TTE) — adjacent, not overlapping.**
*Does:* couples a dual-branch temporal encoder with an ECM-constrained, differentiable, generalized-correntropy **adaptive Kalman filter** to get SOH and RUL in real time under non-Gaussian measurement disturbance and operating variability. "Multi-scale" here means multi-scale **signal/feature** processing, plus robust adaptation of the filter.
*Does not (per the abstract):* nothing about inspection cadence, nothing about interval-censored EOL, nothing about an exposure/Ah-throughput lifetime axis, no cross-condition transfer claim, no censoring. Its "adaptive" is noise-covariance/robust-cost adaptation, not observation-schedule adaptation.
*Assessment:* MARS occupies "robust adaptive filtering for battery health" — a component A would use, not the claim A makes.

**4. Oyewole et al. 2025/2026 (Applied Energy 402:126880) — cannot be assessed.**
*Does:* per the title, uncertainty-aware deep learning with physics-informed Bayesian sampling for prognostics.
*Does not:* unknown. On title alone this is "uncertainty-aware RUL", which is a crowded and largely occupied framing; it does not appear to touch inspection cadence or interval censoring.

**5. Zhang et al. 2026 (Energy and AI 25:100771) — occupies the transfer claim.**
*Does:* a clean, honest measurement of whether a time-series foundation model transfers. Six pipelines, four benchmarks, first 30 % of life as history, recursive forecast of the remaining 70 %, plus prefix-ratio sensitivity. Its headline is that **cross-dataset transfer degrades accuracy** while source-adapted transfer within a dataset is best.
*Does not:* model the observation process at all — the input is a regular per-cycle capacity series with no missingness, no cadence variation, no censoring, and no distinction between RPT-derived and cycle-derived capacity.
*Why it matters:* A's transfer claim ("transfers better across operating conditions") lands in the same evaluation space, and this paper already reports the negative direction. A would need a materially different transfer protocol, not a different model.

**6. Shi et al. 2026 (Sci. Sin. Inf.) — occupies "EOL interval", but with a different meaning.**
*Does:* produces an **interval** for EOL and for dynamic RUL by fusing a Wiener degradation process with an LSTM, explicitly to quantify uncertainty and to work "with incomplete degradation data".
*Does not:* treat the *observation* as interval-censored. The interval here is **output uncertainty** (a confidence interval on a predicted EOL), not the epistemic interval `(L, U]` induced by discrete inspections. This distinction is the one genuine crack in the "interval EOL is occupied" wall — but it is a narrow crack, and a reviewer will read the title and stop there.
*Also:* NASA-only, no cross-condition transfer.

**7. Xiao et al. 2026 (Entropy) — censoring, but a different censoring.**
*Does:* adaptive **progressive Type-II** censoring, where samples are withdrawn early once failure capacity crosses the EOL threshold; censored MLE and Bayesian estimation; coverage comparisons; sensitivity analysis.
*Does not:* this is **test-design** censoring (a decision about which cells to keep running), not **inspection-interval** censoring of a threshold crossing on a continuously-operating asset. No online state, no covariates, no RUL for a live unit.
*Assessment:* relevant to A's "right-censoring" bullet, but only as generic survival analysis. Low threat, high citation value (it is the cleanest recent statement that censoring biases lifetime estimates).

**8. BatteryCDE 2025 (IEEE TTE) — the strongest single threat to A's "irregular intervals" claim.**
*Does:* models capacity from **irregularly sampled, up-to-50 %-missing** data using neural controlled differential equations over a cubic-spline continuous path, and evaluates explicitly on missing-data and cross-battery-transfer scenarios. It even provides a theoretical argument for why continuous-time models beat discrete ones under irregular sampling.
*Does not:* the irregularity is in the **cycle index of the capacity series**, not in the **wall-clock/physical-time spacing of inspections**; there is no censoring, no first-hitting-time, no explicit measurement-quality term, no operating-exposure axis, and no probabilistic EOL.
*Why it hurts:* "advance the state over irregular intervals instead of one fixed step per observation" is, as a modelling primitive, exactly what a neural CDE does. A would be re-deriving a known primitive in a battery-specific notation.

**9. Tao et al. 2026 (MST) — the strongest single threat to A's "explicit observation process" claim.**
*Does:* makes the **measurement act itself** the object of modelling: which frequencies to acquire, at what cost, with what effect on SOH error and interval width, updating only when a measurement is actually taken, and reporting empirical coverage. It is retrospective-but-prospective: archives are masked so that revealing one frequency *is* a prospective measurement.
*Does not:* EIS rather than RPT/capacity; no EOL, no censoring, no exposure axis, no cross-condition transfer (in fact it reports that uncertainty transfer **fails** under domain shift, coverage 0.57).
*Why it hurts:* A's bullet "measurement update only at times when a real measurement truly exists, with explicit observation noise and quality" is this paper's thesis, transplanted from EIS to capacity.

**10. Xia et al. 2026 (Applied Energy) — flagged, unread.** Title suggests probabilistic life-decomposition RUL. Could not verify. Must be read before any related-work claim of novelty in probabilistic RUL.

---

## 3. Verdict

### **NO-GO** for A as a novelty claim.

Two sufficient reasons, either of which alone would sink it:

- **Composition, not mechanism.** The five bullets of A map onto four published papers (Johnen → interval-censored EOL likelihood; BatteryCDE → irregular-interval propagation; Tao → measurement-availability-aware updating with explicit quality/uncertainty; Shi/Wiener line → first-hitting-time EOL intervals). "Combine four known components" is an engineering paper, not a novelty claim, and the reviewer will name these papers.
- **Unidentifiable on the available cohort.** With within-cell inspection-cadence CV = 0.091 and `cum_cycles ~ rpt` R² = 0.999 on UConn, the exposure-axis model and the per-RPT model are the *same* model up to reparameterisation. There is no experiment on that cohort that can distinguish them. Any robustness-to-cadence-change result would be an artefact of a design that has no cadence variation to be robust to.

### The one residual claim that survives — **R1 (identifiability diagnostic), not a predictor**

> **R1.** For a given cohort, the claim "advance by physical exposure rather than per inspection" is *identifiable* only if the within-unit dispersion of inspection cadence exceeds a threshold computable from the cohort itself. Below that threshold, exposure-axis and per-inspection models are observationally equivalent, and any reported robustness to inspection-frequency change is not evidence for the mechanism. We give the diagnostic (cadence CV; R² of cumulative throughput regressed on inspection index; the induced design effect) and demonstrate it on a public cohort where the diagnostic *fails* (CV = 0.091, R² = 0.999) and on one where it passes.

Why this is a real gap rather than a consolation prize:
- It is a **negative/measurement** result of exactly the kind the field is short of, and it is the kind of result that is *strengthened*, not weakened, by the fact that the model comparison came out null.
- It is **cheap**: it needs no new training runs, only the cadence statistics of cohorts already in hand plus a re-analysis of one published result.
- It cannot be scooped by a modelling paper, because its content is a *precondition for modelling claims*, and modelling papers do not publish their preconditions.
- It composes with the programme's existing evaluation-protocol line (the C-MAPSS normalisation audit, [10.31224/8145](https://doi.org/10.31224/8145), and the leakage-aware benchmark [10.2139/ssrn.7661699](https://doi.org/10.2139/ssrn.7661699)) rather than competing with it.

**Residual claim R2 (weaker, only if R1 is rejected):** an *audited* comparison of per-inspection vs per-exposure advancement on cohorts with genuinely high cadence dispersion — i.e. a dataset-construction contribution ("what a cohort must look like for this question to be answerable"), plus the null result on UConn. This is publishable as a benchmark/protocol paper, not as a method paper.

**Do not attempt:** "online predictor with explicit observation process + irregular exposure advancement + interval-censored EOL" as a method contribution. It is the composition of rows 1, 8 and 9 of the matrix.

---

## 4. Every claim in A that is already occupied

| # | Claim in A | Occupied by | Location | Residual room |
|---|---|---|---|---|
| A1 | "EOL is only known between the last above-threshold check and the first below-threshold check" | Johnen et al. 2020 | Whole paper; abstract explicitly: "since data of capacity decline are commonly interval-censored, comparisons of resulting CIs under full and interval-censored information are made by means of simulations" | Essentially none. This is the paper's premise. |
| A2 | Interval-censored likelihood for EOL | Johnen et al. 2020; Xiao et al. 2026 | Johnen: MLE section (not read); Xiao: censored MLE + MH-MCMC | None at the likelihood level. |
| A3 | First-hitting-time of 80 % SOH | Shi et al. 2026 (Wiener first-passage + LSTM); also the standard Wiener-process RUL line, e.g. [10.23919/ccc64809.2025.11179136](https://doi.org/10.23919/ccc64809.2025.11179136), [10.1016/j.psep.2025.106974](https://doi.org/10.1016/j.psep.2025.106974) | Shi: abstract ("confidence interval estimation for EOL", "dynamic remaining-useful-life interval estimation") | None. Standard since at least 2019. |
| A4 | "State propagated over irregular intervals, not one fixed step per RPT" | BatteryCDE 2025 | Abstract + theoretical-analysis section (not read) | Small: wall-clock/physical-time irregularity as opposed to cycle-index irregularity. Too thin to carry a paper. |
| A5 | "Measurement update only when a real measurement arrives, with explicit observation noise and quality" | Tao et al. 2026 (sparse-frequency EIS, offline-calibrated sequential, cost- and uncertainty-aware); MARS 2026 (robust adaptive KF under non-Gaussian measurement disturbance); Measurement 2026 122434 "signal-quality-aware adaptive prediction" [META] | Tao: abstract, whole protocol; MARS: abstract | Small. The *transfer* of this idea from EIS to capacity RPT is an application, not a mechanism. |
| A6 | "No zero-filling for missing inspections, no smoother looking at future data" | BatteryCDE 2025 (missing-data scenario, up to 50 %) | Abstract, missing-data experiments | None. Also a hygiene property, not a contribution. |
| A7 | Right-censoring of not-yet-failed units | Xiao et al. 2026; generic survival analysis | Xiao: censoring scheme + likelihood | None. |
| A8 | "Transfers better across operating conditions" | Zhang et al. 2026 (Energy and AI) reports the opposite direction as a finding — cross-dataset transfer *degrades* | Abstract | Only if the transfer protocol differs materially, which the UConn design does not support. |
| A9 | "Uncertainty-aware RUL" as a framing | Oyewole et al. 2026; Wang et al. 2026; Xia et al. 2026 (all [META]) | Titles only | None — this framing is saturated. |
| A10 | "Advance by Ah-throughput / equivalent full cycles" as a lifetime coordinate | Standard in ageing models since at least 2011: Wang et al. 2011 [10.1016/j.jpowsour.2010.11.134](https://doi.org/10.1016/j.jpowsour.2010.11.134); Ecker et al. 2014 [10.1016/j.jpowsour.2013.09.143](https://doi.org/10.1016/j.jpowsour.2013.09.143); Schmalstieg et al. 2014 [10.1016/j.jpowsour.2014.02.012](https://doi.org/10.1016/j.jpowsour.2014.02.012) [all META — see §5] | — | None. This is the field's default lifetime coordinate, not a proposal. |

**Not occupied (the honest short list):** an explicit *identifiability/precondition* statement of the kind in R1, and — separately — the empirical fact that a given public cohort fails that precondition. I found no paper that publishes a diagnostic of when the exposure axis is distinguishable from the inspection index.

---

## 5. What I could not verify

This section is deliberately blunt. Treat every unlisted-but-unquoted number in this document as non-existent.

1. **No full text of any Elsevier or IEEE paper was obtained.** ScienceDirect → HTTP 403 to this host; IEEE Xplore → HTTP 202 with empty body; Unpaywall: Johnen 2020 `is_oa: false`, `has_repository_copy: false`, no OA locations; `r.jina.ai` now returns 401 (API key required). No institutional credentials in this session.
2. **Measurement 285:122347 (mandatory competitor #2): content entirely unverified.** No abstract in Crossref, OpenAlex or Semantic Scholar. The brief's description ("latent health recursive estimation") is **not supported by the registered title** ("An uncertainty-aware adaptive feedback ensemble framework for remaining useful life prediction of lithium-ion batteries"). One of the two is wrong. This must be resolved from the PDF before the paper is cited.
3. **Applied Energy 402:126880 (mandatory competitor #4): content entirely unverified.** No abstract deposited anywhere reachable.
4. **MARS (mandatory competitor #3): only a truncated abstract seen, and only through an IEEE metrics-page search snippet.** I did **not** read its equations, its ECM formulation, its correntropy cost, or any result. Its DOI [10.1109/tte.2026.3734031](https://doi.org/10.1109/tte.2026.3734031) was resolved through Crossref (IEEE TTE, 2026); the Xplore document number seen in search was 11692676 — I did not confirm that the two identify the same record.
5. **Energy and AI 25:100771 (mandatory competitor #5): abstract only**, though it is gold OA; the ScienceDirect PDF was unreachable.
6. **Johnen 2020: abstract + publisher Highlights only.** I did not read the interval-censored likelihood, the simulation design, or the CI results. My statement that it is a *population* reliability paper and not a per-cell online method is an inference from the abstract, and is strong but not read from the method section.
7. **Equation-level claims about the DoD/stress-factor ageing literature (§7) are NOT verified.** Wang 2011, Ecker 2014 and Schmalstieg 2014 returned **no abstracts** through Semantic Scholar; I read only their titles, venues and DOIs. Anything I say about the functional form of their cycle-ageing terms rests on secondary knowledge and must be checked against the actual equations before it appears in a paper.
8. **Two potentially close items seen by title only, unread:** "Endpoint definitions and censoring in battery lifetime prediction across sources" (Research Square preprint, [10.21203/rs.3.rs-11508938/v1](https://doi.org/10.21203/rs.3.rs-11508938/v1)) — by title this is the closest thing to A's framing that I saw, and it is unread; and "A Probabilistic Estimation of Remaining Useful Life from Censored Time-to-Event Data" (SSRN, [10.2139/ssrn.4814236](https://doi.org/10.2139/ssrn.4814236)) — unread.
9. **Search recall is not exhaustive.** Discovery was Crossref `query.bibliographic` only (32 queries, 268 unique DOIs, 2024-01-01 onward). No Scopus, no Web of Science, no IEEE Xplore full-text search, no Google Scholar, no patent search. OpenAlex was HTTP 429 for most of the session and contributed little. **Absence of a hit in this document is not evidence of absence.**
10. **No forward-citation search was run** on Johnen 2020 (28–30 citations) — the set of papers that cite it is the most likely place for A's exact composition to already exist, and it was not enumerated.

---

## 6. Search log (for reproduction)

Tools: `literature/_tools/cr_sweep.py` (32 Crossref queries), `abs_fetch.py` (S2 + OpenAlex abstract retrieval), `resolve.py` (per-DOI resolution), `cr_b.py` (question-B lookups). Raw outputs: `cr_sweep.json`, `batch1.json`, `batch2.json`.

Query axes and representative strings: interval censoring (`interval censored end of life lithium-ion battery lifetime`, `end-of-life interval estimation lithium-ion battery Wiener process`, `progressive censoring battery aging lifetime reliability`); first-hitting-time (`first hitting time threshold remaining useful life lithium battery`, `Wiener process degradation model battery remaining useful life`); irregular observation (`irregular sampling remaining useful life prediction lithium battery`, `asynchronous measurement state of health estimation lithium battery`, `missing observation battery state of health estimation irregular`); exposure axis (`ampere-hour throughput degradation lithium-ion battery lifetime model`, `equivalent full cycle aging model lithium-ion battery`); continuous-time filtering (`continuous-time state space degradation model battery prognostics`, `particle filter remaining useful life battery online updating`); multiscale/MARS (`multiscale adaptive filtering battery state of health`, `multi-timescale adaptive observer lithium-ion battery state`); online check-up (`online state of health estimation reference performance test battery`, `periodic check-up capacity measurement battery remaining useful life update`); transfer (`cross-condition transfer remaining useful life battery operating condition`, `domain generalization battery health estimation operating condition`); evaluation protocol (`effect of sampling interval on battery state of health estimation accuracy`, `inspection interval prognostics remaining useful life censoring`, `benchmark evaluation protocol leakage battery health estimation`).

---

## 7. Addendum — question B (stress-conditioned damage law on ISU-ILCC), as requested mid-review

Two questions were put to me. Answers below are graded by what I actually verified.

### 7.1 "Is the DoD-exponent damage law already published as a functional form?"

**Almost certainly yes, and this is the highest-risk item in B.** The functional form — cycle life or capacity fade as a power law in depth of discharge, i.e. `N_f ∝ DoD^(−k)` (equivalently `log N_f = a − k·log DoD`), usually multiplied by Arrhenius temperature and C-rate factors — is the standard "stress-factor" ageing model, and it long predates 2024. The canonical references are:

- **Wang, Liu, Hicks-Garner, Sherman, Soukiazian, Verbrugge, Tataria, Musser, Finamore 2011**, *J. Power Sources* 196:3942–3948, "Cycle-life model for graphite-LiFePO4 cells", [10.1016/j.jpowsour.2010.11.134](https://doi.org/10.1016/j.jpowsour.2010.11.134). **[META — DOI and title verified via Crossref; equations NOT read.]**
- **Ecker, Nieto, Käbitz, Schmalstieg, Blank, Warnecke, Sauer 2014**, *J. Power Sources* 248:839–851, "Calendar and cycle life study of Li(NiMnCo)O2-based 18650 lithium-ion batteries", [10.1016/j.jpowsour.2013.09.143](https://doi.org/10.1016/j.jpowsour.2013.09.143). **[META — 762 citations, no abstract retrieved.]**
- **Schmalstieg, Käbitz, Ecker, Sauer 2014**, *J. Power Sources* 257:325–334, "A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries", [10.1016/j.jpowsour.2014.02.012](https://doi.org/10.1016/j.jpowsour.2014.02.012). **[META — no abstract retrieved. This is the paper most likely to already contain the exact law.]**

**Consequence for B:** the *form* `log(life) = a + b·DoD + c·log(C_chg) + d·log(C_dis)` cannot be claimed as new. What can be claimed is a **specific parameterisation fitted to a cohort where throughput normalisation demonstrably fails**, plus the failure statistic itself.

**One genuinely distinguishing detail worth checking.** The classical law is a power law in DoD, i.e. **linear in `log DoD`**. The programme's law is **linear in `DoD`** (`b·DoD`, not `b·log DoD`). Those are different models, and a reviewer will ask which one the data support. If the programme has not fitted the `log DoD` variant, it should — both to defend the choice and because the classical form is the natural null. If `log DoD` fits as well or better, B's law is a reparameterisation of Schmalstieg-type models and the novelty reduces to the *cohort* and the *failure demonstration*.

### 7.2 "Does the literature already contain a quantified demonstration that charge-throughput / equivalent-full-cycle normalisation fails to collapse DoD effects?"

**The phenomenon: known and published qualitatively and semi-quantitatively. The specific statistic: not found, but the search was shallow.**

- **Preger, Barkholtz, Fresquez, Campbell, Juba, Romàn-Kustas, Ferreira, Chalamala 2020**, *J. Electrochem. Soc.* 167:120532, "Degradation of Commercial Lithium-Ion Cells as a Function of Chemistry and Cycling Conditions", [10.1149/1945-7111/abae37](https://doi.org/10.1149/1945-7111/abae37). **[ABS read — 551 citations.]** Abstract, verbatim: they vary discharge rate, DoD and temperature for LFP/NCA/NMC commercial cells and report that "the range of cycling conditions had a profound effect on cell degradation, **with time to reach 80% capacity varying by thousands of hours and cycle counts** among cells of each chemistry." Data public at batteryarchive.org.
  *What it establishes:* that per-cycle life and per-time life are not interchangeable across DoD/rate/temperature, measured across three chemistries.
  *What it does NOT establish (per the abstract):* an explicit **throughput/EFC normalisation failure** statistic. It reports the spread in hours and cycles; it does not (in the abstract) normalise by Ah-throughput and report a residual rank correlation with DoD. **I did not read the results section, so I cannot say the paper lacks this — only that the abstract does not state it.**
  *Threat level:* **high**. If Preger's per-EFC curves are in the paper, B's headline demonstration is a re-analysis of a 2020 result.
- **10.1109/eleco60389.2023.10415967**, "Effect of the Depth of Discharge and C-Rate on Battery Degradation and Cycle Life" (2023). **[ABS read.]** Simulation study; states the DoD×C-rate interaction qualitatively ("elevated DoD and C-rate can expedite battery degradation"). No normalisation test. Low threat, useful citation.
- **10.4028/www.scientific.net/amm.319.373**, "Experimental Study on Depth of Discharge and Cycle Life of Lithium-Ion Battery" (2013). **[META.]** Title-level relevance only.

**Assessment for B:** the *claim* "throughput normalisation does not absorb DoD" is close to folk knowledge and will not survive as a novelty claim on its own. What is defensible is narrower and better: **a quantified, rank-based demonstration on a cohort with enough DoD contrast to measure it, with the normalised and un-normalised rankings reported side by side, and a stress-conditioned law that recovers the ranking.** The numbers the parent quoted (Spearman −0.636 → −0.815 after normalisation; +0.87 for the law vs +0.28 for throughput normalisation) are, as *numbers*, almost certainly new — I found no paper reporting them. But the *narrative* is old.

**Two statistical cautions before this becomes a claim:**
- `n` conditions matters more than ρ. Spearman +0.87 on a handful of conditions has a wide interval; the programme's own power rule (AGENTS.md §4.3: effective n after design effect) should be applied to the condition-level comparison *before* the +0.87 is written down as a result.
- The comparison "+0.87 law vs +0.28 throughput" is a comparison of two models on the *same* conditions; it needs a paired test, not two separate correlations.

### 7.3 Recommended next branch for B (one line)

Read Schmalstieg 2014 §cycle-ageing and Preger 2020 §results **first** (both are the likely occupants), then frame B as: *a DoD-contrast cohort + a rank-based failure-of-normalisation statistic + a stress law whose DoD term is tested against the classical `log DoD` power law*. Do not frame it as "we propose a stress-conditioned damage law" — that law exists since 2011–2014.

---

## 8. Status of this review

- **Independent?** Yes — separate context, no access to the parent's reasoning beyond the brief.
- **Complete?** No. Three of five mandatory competitors are unread; no full text of any paywalled item; no forward-citation search on Johnen 2020; discovery limited to Crossref.
- **Recommendation:** treat the NO-GO on A as **provisional but well-supported on the identifiability ground alone** (which does not depend on any unread paper), and treat the literature ground as **strengthened but not closed** until Johnen 2020's forward citations and the Measurement 285:122347 PDF are read.
