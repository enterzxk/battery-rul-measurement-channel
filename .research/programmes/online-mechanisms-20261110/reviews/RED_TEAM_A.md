# RED_TEAM_A — Hostile methods review

**Target**: online exposure-clock degradation predictor with interval-censored EOL (draft, pre-implementation)
**Reviewer role**: adversarial methods review. No new modules proposed; attacks only.
**Date**: 2026-11-10
**Status of target**: draft, not yet defended.

---

## 0. What was actually measured before objecting

Every number below was computed from the local archives, not assumed. Scripts are in
`data/external/isu_raw/` and `data/external/uconn/`; provenance is given per claim so any
objection can be re-run or refuted.

| Measurement | Value | Script / source |
|---|---|---|
| UConn cells / conditions | 64 / 11 | `uconn_clock_audit2.py` |
| UConn `num_cycles` semantics | **per-segment length, not cumulative** (confirms F-005) | `uconn_clock_audit2.py` |
| UConn within-cell CV of cycles-per-RPT | **0.027** (2.7 %) | `uconn_clock_audit2.py` |
| UConn R²(exposure clock vs RPT index), within cell | median **0.9994**, min 0.9977 | `uconn_clock_audit2.py` |
| UConn cycles/RPT across cells | 67.7 – 134.7 (1.99×), cross-cell CV **0.203** | `uconn_clock_audit2.py` |
| UConn per-condition median cycles/RPT | 67.8 (g9) – 132.4 (g6) | `uconn_clock_audit2.py` |
| UConn within-condition spread of cycles/RPT | 0.7 % – 7.0 % | inline check |
| UConn RPTs per cell | 22 – 77, median 43 | `uconn_clock_audit2.py` |
| UConn right-censored cells | **0 / 64** | `uconn_clock_audit2.py` |
| UConn EOL interval width | always exactly **1 RPT**; 75–176 cycles, median 132 | `uconn_clock_audit2.py` |
| ISU cells / conditions | 251 / 63 (4 per condition; G61C1 absent) | `Valid_cells.csv` |
| ISU RPT JSON fields | capacity (C/5, C/2), QV traces, `start_stop_time` — **no cycle counter** | `cadence_audit3.py` |
| ISU RPTs per cell | **2 – 80**, median 19; 6 cells ≤ 4 | `isu_capacity_audit.py` |
| ISU calendar cadence | 7.32 – 9.43 days/RPT; between-condition CV **0.066** | `isu_cadence_stats.py` |
| ISU within-condition spread of days/RPT | median **1.8 %**, max 10.1 % | `isu_cadence_stats.py` |
| ISU `efc_day` (exposure rate) | 6.0 – 27.6 (4.6×), CV 0.437 | `B_condition_summary.csv` |
| `efc_day` formula recovered | **= 24/(1/C_chg + 1/C_dis) exactly, 53/53 conditions, max rel. err 0.00e+00** | `attack_quant.py` + verification |
| corr(`efc_day`, discharge C-rate) | **+0.863** | `attack_quant.py` |
| R²(`efc_day` ~ DoD, C_chg, C_dis) | **0.884** | `attack_quant.py` |
| ISU missing RPT slots | 50 / 5503 = **0.91 %** | `attack_quant2.py` |
| ISU right-censored (SOH = Q/Q_first) | **0 / 250** | `isu_capacity_audit.py` |
| ISU relative EOL interval width | 2.3 % – **203.8 %** of lifetime, median **8.8 %**; 7 % of cells > 20 % | `attack_quant.py` |
| corr(absolute interval width, EOL_EFC) | **+0.489** | `attack_quant2.py` |
| corr(RPT count, EOL in days) | **+0.780** | `attack_quant.py` |
| ISU cells with single-step SOH drop > 20 pts | **29 / 250**, max 52.4 pts | `isu_capacity_audit.py` |
| ISU implausible EOL labels | g14: 3.97 d / 40.9 EFC; g11: 11.96 d / 119.6 EFC | `B_condition_summary.csv` |
| EOL label-table coverage | **53 / 63 conditions, 210 / 250 cells**; conditions 20–29 silently absent | reconciliation check |
| Condition-level n_eff (ICC 0.2 / 0.414 / 0.5) | 39.4 / 28.1 / 25.2 nominal; **33.1 / 23.6 / 21.2** on the usable 53 | computed |
| Condition-level MDE | **9.0 – 12.3 % of baseline MAE** | computed from project anchor |

Project anchors used (from `rul_v4_20261107/AGENTS.md` §4.3): ICC = 0.414, deff = 2.99,
effective n = 21.4 for 64 cells, MDE = 17.1 % of baseline MAE at n = 11 conditions.

---

## 1. Identification attacks

### 1.1 The headline comparison is a reparameterisation, not a hypothesis

Let `e_k` be cumulative exposure at RPT `k`, strictly increasing. The two models are

- **A (exposure clock)**: `y_k = h(e_k) + ε`
- **B (per-RPT step)**: `y_k = g(k) + ε`

For *any* `h`, setting `g(k) := h(e_k)` makes B reproduce A **exactly** on the observation
grid. Conversely, if `e_k` is strictly monotone, A reproduces B. The two models are
observationally equivalent at RPT times whenever the clock is a monotone function of RPT
index **within a cell**. This is not "hard to distinguish"; it is a bijection between
parameterisations, with no testable content.

They can differ only through three channels:

1. **Between RPT times** — predictions strictly inside an interval.
2. **Off-grid cadence** — evaluating at an `e` that is not a monotone relabeling of `k`.
3. **Parameter sharing** across cells with different cadence ratios.

Channel 3 is the actual claim. But channel 3 is *exactly* reproduced by giving B a single
covariate equal to the cadence ratio. So the honest null is **not** "B", it is
"**B + cadence-rate covariate**". Section 5 makes this the decisive baseline.

### 1.2 Measured answer: on ISU, the clocks are *exactly* collinear within condition

The draft requires "ACTUAL operating exposure (Ah-throughput, equivalent full cycles, or
calendar time)". For ISU this variable does not exist in the archive:

- The RPT JSON contains only capacity, QV traces and `start_stop_time`. **There is no cycle
  counter**; true cycle counts need `Cycling_json.zip` (10.2 GB), which is **not present
  locally**.
- The only exposure-rate variable in play, `B_condition_summary.csv::efc_day`, is **nominal
  C-rate arithmetic**: `efc_day = 24/(1/C_chg + 1/C_dis)`, recovered with *zero* error on
  53/53 conditions. It **ignores DoD entirely** (a 25.9 % DoD cycle counts the same as a
  97.5 % DoD cycle), so it is not equivalent-full-cycles at all — it is nominal cycles/day.
- Because it is a function of the condition's C-rates only, it is **identical for all four
  cells of a condition**. Therefore within every ISU condition, exposure is **exactly
  proportional** to RPT index. Correlation is 1 by construction, not 0.999.

**Consequence**: on ISU, model A and model B are the same model up to a per-condition
rescaling. There is *zero* within-condition identification. And `eol_efc` is likewise
derived (`eol_efc = efc_day × eol_day`, max rel. err 3.2e-16), not measured.

### 1.3 Measured answer: on UConn, the clocks differ by 2.7 %

UConn *does* carry measured exposure (`num_cycles` per segment). But:

- Within-cell CV of cycles-per-RPT is **2.7 %** (p90 = 3.0 %, max 3.2 %).
- Within-cell R²(exposure clock, RPT index) is **0.9994** median.

So within a cell the two clocks differ by a ~2.7 % perturbation. To detect that, the
capacity–clock curve would need curvature sharp enough that a 2.7 % clock distortion moves
predicted SOH by more than observation noise. Across the whole UConn cohort that is a
very thin reed, and it is the *only* place the claim can live.

### 1.4 Where the real variation is — and why it does not rescue the claim

Cross-condition cadence variation is large: UConn cycles/RPT spans 67.7–134.7 (2×);
ISU nominal `efc_day` spans 6.0–27.6 (4.6×). But this variation is **nested in the
condition**:

- UConn: within-condition spread of cycles/RPT is 0.7–7.0 %, while the between-condition
  range is 2×.
- ISU: within-condition spread of days/RPT is 1.8 % median, while between-condition
  `efc_day` CV is 0.437.

Cadence is therefore a **condition-level variable**, and a condition fixed effect absorbs it
completely. Any apparent gain from the exposure clock is arithmetically identical to a
condition-specific rate, which a stratified model already has.

### 1.5 The discriminating test (feasible on existing data)

**Uniform thinning will not work** — retaining every s-th RPT rescales exposure uniformly
within a cell, which model B absorbs by refitting its step. The test must make the exposure
gaps **non-uniform**.

**Design — random-subset thinning, UConn only (measured exposure required):**

1. For each cell, draw `M = 200` random subsets of RPT indices retaining ~50 % of visits,
   stratified so that at least 4 visits and both a pre- and post-threshold visit remain.
2. For each subset, the retained exposure gaps are unequal (e.g. 100, 200, 300 cycles).
   Model A consumes the true gaps; model B consumes one average step, or the gap as a
   covariate.
3. Fit both on the retained subset, then score both on the **full unthinned** sequence.
4. Primary statistic: paired difference in condition-macro MAE between A and
   B+cadence-covariate, aggregated over the 11 conditions.

**Pass/fail**: A must beat B+cadence-covariate by at least the MDE in §4 (≈ 12 % of
baseline MAE) with a condition-level paired test. If the paired difference is < 5 % of
baseline MAE, the exposure clock is not established — and given §1.1, "not established"
here means "the hypothesis has no observational content", not "the effect is small".

**Honest caveat the review insists on**: this test validates the clock only under
**synthetic** cadence perturbation. It is evidence about the estimator's reparameterisation
invariance, not evidence that real-world cadence changes are handled. No natural cadence
manipulation exists in either cohort (§2.1).

### 1.6 The one asset that could rescue identification

UConn's archive reportedly includes some raw 1 Hz operating records. **If** per-cycle
discharge capacity is reconstructible from those records, channel 1 (between-RPT
observations) opens and the equivalence in §1.1 is broken empirically rather than
synthetically. This should be checked **before** any modelling: it is the difference
between a testable mechanism and an unfalsifiable one. If it is not reconstructible,
channel 1 is closed and only synthetic thinning remains.

---

## 2. Confounding attacks

Each item names the assumption it breaks and the test that would expose it.

### 2.1 Cadence is a deterministic function of the protocol
**Broken assumption**: that inspection cadence is an independent manipulation.
**Measured**: R²(`efc_day` ~ DoD, C_chg, C_dis) = **0.884**; corr(`efc_day`,
discharge C-rate) = **+0.863**. On UConn, within-condition cadence spread is 0.7–7 % while
the between-condition range is 2×.
**Test**: regress cadence on the design factors and report the residual variance. With 88 %
explained, there is no cadence variation left that is not also a condition change.

### 2.2 Condition is tied to cadence (the same coin, other face)
**Broken assumption**: that "condition" and "cadence" are separable regressors.
They are not: cadence is *computed from* the C-rates that define the condition. A model
"with exposure" and a model "with condition" carry the same information.
**Test**: fit both and check variance inflation; the design matrix is near-singular by
construction on ISU (§1.2), exactly collinear within condition.

### 2.3 Cell-to-condition nesting
**Broken assumption**: that cells provide independent replication of cadence.
Four cells per ISU condition, six per UConn condition, and **no cell ever changes
condition**. Cadence is constant within cell, so the cell is not a replication of cadence —
only the condition is. Effective replication for any cadence claim is therefore 63 (ISU) or
11 (UConn) *conditions*, not 251 or 64 cells.

### 2.4 Different total observation counts — and they leak the label
**Broken assumption**: that observation count is a nuisance.
**Measured**: ISU RPT counts span **2–80** (median 19; six cells ≤ 4). UConn spans 22–77.
**corr(RPT count, EOL in days) = +0.780.** Cells that live longer are inspected more times.
So "number of observations", "history length", and anything derived from them (including
interval width, §3.3) is a **proxy for the label**. A model that consumes observation
history gets outcome information for free and will look better than it is.
**Test**: predict EOL from `n_rpt` alone. If that trivial model already achieves a
non-trivial share of the claimed performance, the mechanism claim is contaminated.

### 2.5 Capacity baseline anchoring follows cadence
**Broken assumption**: that SOH is normalised to a cadence-independent baseline.
With `SOH = Q/Q_first`, a cell whose first RPT is late is normalised to an already-degraded
capacity and therefore looks healthier and dies later. Cadence → baseline → label.
**Test**: recompute SOH against a fixed nominal/formation capacity and check whether the
condition ranking of EOL changes. If it does, part of the "cadence effect" is baseline
anchoring. (Note: this normalisation also *defines away* left-censoring — see §3.4.)

### 2.6 Vintage / chamber effects
Many UConn cells start within seconds of each other (e.g. `2021-06-11T16:41:5x`); ISU
cells likewise cluster on shared start dates. Start time is a shared chamber, temperature
and batch factor. The project already has history here (the "vintage" probes).
**Test**: add start-date as a random effect; if the cadence coefficient moves materially,
cadence was proxying vintage.

### 2.7 Missingness is small but unverified
**Measured**: 50 empty RPT slots out of 5503 = **0.91 %**; 40/250 cells affected.
**Broken assumption**: that missingness is ignorable. 0.91 % is small, so the "no
zero-filling" advantage addresses a ~1 % phenomenon — it cannot be the source of a
headline gain.
**Test**: MCAR vs MAR check against condition and `n_rpt`. If missingness correlates with
condition, deletion is informative.

### 2.8 Label contamination concentrated in fast conditions
**Measured**: **29/250** ISU cells show a single-step SOH drop > 20 points (max **52.4**).
Condition-level EOL as low as **3.97 days / 40.9 EFC** (g14) and 11.96 days / 119.6 EFC
(g11) — physically implausible for LFP. These are almost certainly failed RPTs or cell
faults, not degradation.
**Test**: recompute EOL after excluding cells whose `[L,U]` bracket contains a > 20-point
drop; if hazard/rate parameters move by more than 1 SD, the model is fitting artefacts.

---

## 3. Interval-censoring attacks

### 3.1 The censoring machinery and the exposure clock are one contribution, not two
If the clock is the RPT index, the interval is always `[k−1, k]` — **width exactly 1, in
every cell, in both cohorts** (measured: UConn always 1 RPT; ISU always 1 RPT). The
interval-censored likelihood then *is* the ordinary discrete-time (grouped) hazard model.
It adds nothing.
The interval likelihood only acquires content **because** the clock is continuous. So
"exposure clock" and "interval censoring" cannot be counted as two contributions: the second
is a corollary of the first, and §1 shows the first is not identified on ISU and is a 2.7 %
perturbation on UConn.

### 3.2 Where it does buy something — and the size of the prize
It buys **consistency**, not variance. Midpoint and last-observed-time estimators are biased
when the hazard is non-linear; a correct interval likelihood is consistent. That is a real
but second-order gain.

**Bound on the gain**: the correction can be at most about **half the interval width**.
Measured relative width is median **8.8 %** of lifetime (p25 6.2 %, p75 12.3 %). So the
typical maximum correction is **≈ 4.4 % of lifetime**. Any claimed improvement larger than
that on EOL accuracy is not attributable to the censoring treatment.

### 3.3 The interval width is informative — and it is a design variable
**Broken assumption**: that interval width is a nuisance to be marginalised.
**Measured**: corr(absolute interval width in EFC, EOL_EFC) = **+0.489**; relative width
spans **2.3 % to 203.8 %** of lifetime. Because width = (exposure rate) × (RPT gap), and the
exposure rate is nominal C-rate arithmetic (§1.2), the width is a **deterministic function
of the condition and the schedule**. It is therefore a confounder, not a nuisance: the
likelihood silently conditions on design information. That is acceptable for a generative
model over the design, but it means the model is partly learning the schedule, not
degradation.

### 3.4 Degeneration conditions (when the model becomes trivial)
The interval model collapses to something with no content under any of:

- **(a) RPT-index clock** — width is identically 1 → grouped discrete hazard (§3.1).
- **(b) Zero right-censoring** — measured **0/64** UConn and **0/250** ISU cells never cross
  the threshold. The right-censoring term contributes exactly nothing, so the draft's
  "cells that never crossed are right-censored" is **unfalsifiable on this data**. The
  censoring code path cannot be validated, only asserted.
- **(c) Left-censoring is hidden, not absent** — normalising to the first RPT forces
  `SOH(first) = 100 %`, which makes a first-visit-below-threshold case *impossible by
  construction*. The draft's event model specifies only `[L,U]` and right-censoring; the
  left-censored case is not specified, and the normalisation conceals whether it occurs.
  With 6 ISU cells having ≤ 4 RPTs, this is not hypothetical.
- **(d) Artefact brackets** — for the 29 cells in §2.8, `[L,U]` brackets a measurement
  artefact, so the likelihood is fitting faults.

### 3.5 Test that separates the censoring claim from the clock claim
On UConn (where width is always 1 RPT but exposure is measured): compare EOL accuracy under
(i) interval likelihood, (ii) midpoint, (iii) last-observed, holding the clock fixed.
If (i) does not beat (ii) by ≥ 4 % of lifetime, the censoring treatment is not earning its
complexity and should be narrowed to midpoint. This isolates the censoring contribution from
the clock contribution, which the draft conflates.

---

## 4. Cross-condition transfer attacks

### 4.1 Effective sample size
The unit of inference is the **condition**, not the cell. With 4 cells per condition and the
project's measured ICC = 0.414:

```
deff = 1 + (4−1) × 0.414 = 2.242
n_eff = 63 / 2.242 = 28.1
```

Sensitivity to ICC: n_eff = **33.1** (ICC 0.2), **23.6** (ICC 0.414), **21.2** (ICC 0.5).

The nominal 251 cells are worth **~24 conditions**. Quoting 251 as the sample size is
inflation by a factor of ~10.

### 4.2 MDE
Scaling the project anchor (17.1 % of baseline MAE at n = 11 conditions) as 1/√n:

| Analysis set | ICC 0.2 | ICC 0.414 | ICC 0.5 |
|---|---|---|---|
| nominal 63 conditions | 9.0 % | 10.7 % | 11.3 % |
| usable 53 conditions | 9.9 % | **11.7 %** | 12.3 % |

**So the honest detection floor is ~12 % relative MAE.** A claimed gain of 5–10 % is not
distinguishable from noise at this sample size. Note also that adding cells per condition
does not help much (deff grows): 8 cells/condition yields n_eff ≈ 16 at ICC 0.414.

### 4.3 Is a cross-condition claim testable with 4 cells per condition?
**At the condition level: yes in principle, no in this programme.** Four cells are adequate
to estimate a condition mean (SE = σ_within/2); the limiting factor is not 4 cells, it is:

- **No untouched confirmation set.** `HISTORICAL_BOUNDARIES.md` §5.1 records that *all 63
  ISU conditions were already used in development*, so no re-split yields a clean
  confirmation set. Any leave-one-condition-out number is optimistically biased by
  construction. The claim is therefore **not confirmable on this data**, regardless of the
  method.
- **The label table covers only 53 of 63 conditions.** Conditions **20–29 (40 cells, 16 % of
  the cohort) are absent** from `B_condition_summary.csv`, yet all 40 cells *do* cross 80 %
  under `SOH = Q/Q_first` (min SOH 25.7–56.1). This is a silent exclusion of a contiguous
  block. Either it is a processing defect or a deliberate filter — it must be reconciled and
  stated before any survival model is fit, because it changes both n_eff and the MDE.
- **The exposure variable is nominal.** As shown in §1.2, `efc_day` is C-rate arithmetic
  that ignores DoD. A "cross-condition transfer" claim built on it is a claim that the model
  was given the C-rates — which every baseline can also be given.

### 4.4 Test
Pre-register a condition-level paired test on the 53 usable conditions (or reconcile to 63),
unit = condition, `n_eff ≈ 24`, α = 0.05, power 0.8, MDE ≈ 12 % relative MAE. Report the
paired difference **with the ICC-based design effect applied**, not a cell-level bootstrap.
And state explicitly that the result is developmental, not confirmatory.

---

## 5. Baseline attacks

For each: what it is, what the proposal must beat, and the numeric bar. Bar = **≥ 12 %
relative improvement in condition-macro MAE**, paired at condition level (from §4.2).

### 5.1 Per-RPT model with the exposure rate as a feature — **the decisive baseline**
This is model B plus one covariate equal to exposure-per-RPT. By §1.1 it is *mathematically
the same model* as the proposal, differently parameterised. If the proposal does not beat
this, the headline claim ("advance by exposure, not per RPT") is **empty**, because the
comparison was against a deliberately handicapped baseline that withheld the cadence.
**Bar**: must beat by ≥ 12 % relative MAE. Realistically it will **tie**, and a tie must be
reported as a tie, not as "comparable performance with a more principled formulation".

### 5.2 Gamma / Wiener process with covariates and first-passage threshold
A monotone latent degradation state driven by exposure with a first-crossing threshold
**is** a gamma process (monotone increments) or a drifted Wiener process (non-monotone).
Both admit closed-form or quadrature first-passage densities and both accept interval
censoring and covariates natively. This baseline subsumes the proposal's mechanism.
**Bar**: the proposal must beat a covariate gamma process *with the same interval-censored
first-passage likelihood* by ≥ 12 % relative MAE. If it does not, the contribution is
engineering, not method — and must be written as such.

### 5.3 State-space model with Kalman / particle filter
Explicit observation noise, quality weighting, updates only when an observation arrives, and
no use of future data are *exactly* what a filter does. The proposal's measurement-update
section is a description of a filtering recursion. Irregular observation times are the
standard case for a continuous-discrete filter.
**Bar**: must beat a particle filter with the same state and observation model by ≥ 12 %.
If the proposal *is* that model, say so and cite the class rather than presenting the
update rule as a contribution.

### 5.4 Stratified survival model
Cox / AFT stratified by condition, or a discrete-time hazard on RPT index with condition
strata. This baseline tests whether the clock matters **at all**: if a stratified hazard on
RPT index matches the exposure-clock model, the clock is irrelevant and §1's equivalence is
confirmed empirically.
**Bar**: must beat by ≥ 12 %. Because cadence is nested in condition (§2.1), a stratified
model has access to the same rate information, so this is a hard baseline.

### 5.5 Gradient-boosted model with exposure and observation-history features
Cumulative exposure, exposure since last observation, `n_obs` so far, last capacity, recent
slope. Strongest for point prediction inside the observed horizon; cannot extrapolate, which
is the proposal's only structural advantage.
**Bar**: must beat by ≥ 12 % on **held-out conditions**, not held-out cells. And note
§2.4: `n_obs` alone correlates +0.780 with EOL, so this baseline is strong and partly
label-leaking — a fair test must give the proposal the same history features.
**Caution**: the project has measured that HGB is deterministic here (std = 0), so
bootstrap the comparison rather than running seeds.

### 5.6 Two trivial baselines that must also be cleared
- **Predict the training-condition median EOL** for every cell.
- **Linear extrapolation of the first-k capacity slope** to the threshold.
If the proposal cannot beat these by a wide margin, no mechanism claim survives. These cost
minutes and should be reported first.

---

## 6. Kill criteria

Five falsifiable predictions of the mechanism, each with a numeric threshold.

**K1 — Reparameterisation null (fatal if met).**
On UConn, the paired difference in condition-macro MAE between the exposure-clock model and
the per-RPT model *with a cadence covariate* is **< 5 % of baseline MAE**.
Kill: the exposure clock has no observational content beyond the covariate (§1.1, §1.5).
This is the criterion most likely to fire.

**K2 — Synthetic-cadence invariance.**
Under random-subset thinning to 50 % of visits, the exposure-clock model must retain
calibration: slope of predicted-vs-actual within **±10 %**, and MAE under thinning
**≤ 1.5 ×** its full-cadence MAE. If MAE inflates beyond 1.5×, the clock is not doing the
work — the model is memorising the schedule.

**K3 — Interval-censoring increment.**
Interval likelihood must beat the midpoint estimator on held-out conditions by **≥ 4 % of
lifetime** in EOL MAE (half the median relative width of 8.8 %, §3.2). Below that, narrow to
midpoint and drop the censoring machinery from the claims.

**K4 — Schedule leakage.**
Regress per-condition degradation rate on (`efc_day`, `n_rpt`). If `n_rpt` retains a
significant coefficient with partial R² **> 0.10** after conditioning on `efc_day`, the
observation schedule carries outcome information the exposure clock misses → the model is
misspecified. Given corr(`n_rpt`, EOL) = +0.780, this is a live risk.

**K5 — Artefact robustness.**
Exclude the 29 cells whose `[L,U]` bracket contains a > 20-point single-step SOH drop.
If the estimated hazard/rate parameters shift by **> 1 SD**, the model is fitting measurement
faults, not degradation. Additionally: if the programme cannot supply a cohort with **≥ 10 %
right-censored cells**, the right-censoring claim must be deleted from the paper — currently
0/64 and 0/250 are censored, so that claim is untestable as written.

---

## Verdict

**NEEDS-NARROWING.**

The formulation is *sound* — an exposure-driven latent state, explicit observation noise, a
causal update, and an interval-censored first-passage likelihood are all correct choices, and
the refusal to zero-fill or smooth with future data is right. But the **claimed benefit is not
identified by this data**, for three independent reasons, each measured rather than argued:

1. **The comparison is a reparameterisation.** "Advance by exposure" and "advance per RPT +
   cadence covariate" are the same model (§1.1). On ISU the two clocks are *exactly*
   collinear within condition, because the only exposure variable available is nominal
   C-rate arithmetic `24/(1/C_chg + 1/C_dis)` that ignores DoD and is identical for all four
   cells of a condition (§1.2). On UConn the clocks differ by 2.7 % within cell (§1.3).
2. **Cadence is 88 % determined by the condition** (R² = 0.884), so "robustness to changes
   in inspection frequency" has no independent manipulation to test (§2.1–2.3).
3. **The censoring claim is untestable here**: zero right-censored cells in both cohorts, and
   with an RPT-index clock the interval is always width 1, which is just a grouped hazard
   model (§3.1, §3.4).

**Required narrowing** (all four, or the paper is not defensible):

- **Drop the mechanism claim on ISU.** ISU cannot support it: no cycle counter in the RPT
  archive, and the nominal exposure variable is a function of the C-rates that define the
  condition. Use ISU for prediction/transfer only, or obtain `Cycling_json.zip` (10.2 GB)
  and build a *measured* exposure variable.
- **Reframe the comparison** against "per-RPT + cadence covariate", "covariate gamma/Wiener
  process with interval-censored first passage", and "particle filter" — not against a bare
  per-RPT step model (§5).
- **Delete or qualify the right-censoring contribution** (0 censored cells), and drop
  interval censoring as a *separate* contribution — it is a corollary of the continuous
  clock, not an independent mechanism (§3.1).
- **Reconcile the label table**: conditions 20–29 (40 cells, 16 %) are missing from
  `B_condition_summary.csv` although all 40 cross threshold; and 29 cells carry > 20-point
  single-step drops. Until both are resolved, the EOL labels are not trustworthy enough to
  fit a survival model to.

**Is it fundamentally weak?** The *method* is not — it is a competent assembly of standard
reliability components, and assembling them correctly has value. But the *claim* is
fundamentally weak: as stated it compares a mechanism against a version of itself with
information removed. If K1 fires (as I expect), the honest paper is not "exposure beats
per-RPT" but a **negative/audit result**, which this programme's own conventions
(`AGENTS.md` §11, `FALSIFIED.md`) treat as a legitimate output.

**Stronger alternative question on the same data** — both are identifiable, and neither is
occupied by the falsified lines (F-013 covers EOL *value* as an objective, not these):

1. **Inspection-budget question (recommended).** *"What is the minimum RPT cadence that
   preserves condition-level EOL ranking, and how does that budget depend on the condition's
   C-rate?"* This is answerable by thinning UConn (22–77 visits/cell) and ISU (2–80) without
   any new data; it turns the non-identifiable "is exposure the right clock" into an
   identifiable "how few inspections before ranking breaks"; it produces an actionable
   engineering result; and it uses the interval structure honestly, because interval width
   *is* the thing being varied.
2. **Label-artefact audit.** *"How much of the reported cross-condition variation in EOL is
   measurement artefact rather than degradation?"* Justified by measured facts: relative
   interval width spans 2.3 %–203.8 % of lifetime, width correlates with the outcome
   (+0.489), 29/250 cells carry implausible single-step drops, and two conditions imply
   EOL in 41 and 120 equivalent cycles. This is a rigorous negative result the data can
   actually support.

---

*Reviewer's note on scope: this review attacks the method as drafted. It does not propose
modules, and it does not assert that any objection has been tested against a fitted model —
each objection states the measurement made, the assumption broken, and the test that would
confirm or refute it.*
