# Independent novelty & prior-art audit — DROCT (Dual-Rate Observation-Corrected Transformer)

Auditor: independent literature subagent. Date: 2026-11-10.
Scope: literature only. No experiments run, no project data touched.
Verification rule: every bibliographic item below was resolved against Crossref, OpenAlex, Semantic Scholar,
a publisher page, or an arXiv/figshare record. `FULL` = method+experiment read; `ABS` = abstract read;
`META` = title/venue/DOI only (abstract not obtainable). Anything not resolved is marked UNVERIFIED.

---

## 0. Bottom line (blunt)

**M5 as written is a Kalman filter.** The two equations are the textbook predict/update pair with a learned
gain `K` and a learned observation operator `H`. Calling it "Observation-Corrected Degradation State" does
not change that. The only non-Kalman element is that `K` and `H` are neural — which is precisely KalmanNet
(Revach et al., IEEE TSP 2022), and precisely what KalmanFormer does with a Transformer (Shen et al., 2025).
The battery-specific version of exactly this has already been published: Sayed & Mahmoud, *Hybrid
Neural-Kalman Filtering for Robust Battery Health Estimation*, IEEE ECCE 2025, whose abstract states it is
"the first to apply neural network aided Kalman filter (KalmanNet) for battery SOH estimation."

A hostile IEEE TIM reviewer will therefore write: *"The proposed 'observation-corrected state' is a Kalman
filter with a learned gain. KalmanNet and KalmanFormer already do this; the authors' own closest citation
applies KalmanNet to battery SOH. The patch encoder and the time positional encoding are also standard
(IIP-Mixer, CyclePatch, ConvTrans+tAPE). The contribution reduces to an application composition, and the
paper provides no new identifiable mechanism. Reject."*

The three novelty claims are, in order: **OCCUPIED / PARTIALLY OCCUPIED / OCCUPIED (as a mechanism)**.
The conjunction is not found as a single paper, but a conjunction of occupied parts is not a mechanism.

**Important context found in the repo.** `.control/paper/FULL_DRAFT_V1.md` no longer proposes DROCT. It
proposes a mechanistic `(D, ℓ, R)` rate-state filter with Joseph-form updates, and frames the contribution
empirically ("what does a mechanistic state-space filter add over strong same-input learners?"), with
sample-efficiency and scheduling results. That framing is *much* more defensible than the DROCT framing,
because it does not claim the filter equation as novelty. This audit judges DROCT as specified; the
recommendation in §7 is to keep the empirical framing and never present M5 as the contribution.

---

## 1. The 12 closest papers

### P1 — Degradation State–Space Transformer (DSST)
- **Title**: Degradation state–space transformer: Physics-consistent self-supervised model for robust
  remaining useful life prediction under domain shift
- **DOI**: 10.1016/j.ress.2026.113686 — *Reliability Engineering & System Safety* (online 2026-10-28;
  Crossref issue 2027-02). Authors: Faizanbasha A., Almakayeel, Hussainy, Rizwan, Asif, Aksam V.K.
- **Read level**: ABS + full Introduction + contribution list (ScienceDirect landing page). **VERIFIED.**
- **Research question**: can RUL be inferred as a latent monotone damage state crossing a failure boundary,
  rather than regressed directly, and stay physical under domain shift?
- **Core mechanism**: latent monotone damage state with non-negative increments enforced *by construction*;
  stochastic degradation dynamics; differentiable first-passage-time (FPT) mapping to an RUL distribution;
  masked + contrastive self-supervised pretraining; post-hoc calibration.
- **Structure**: condition-aware Transformer encoder → monotone stochastic state-space → FPT head.
- **Data**: NASA C-MAPSS (turbofan) + NASA Ames battery B0005/B0006/B0007/B0018.
- **Protocol**: C-MAPSS standard subsets; battery = **within-cell chronological holdout** (early window
  train, late window test). The authors explicitly state this "does not establish cell-disjoint transfer".
- **Demonstrated**: competitive point accuracy, repeated-initialisation statistics, ablations, uncertainty,
  latent threshold crossing, compute. No cross-cell battery generalisation.
- **Limitations (authors' own + visible)**: battery evidence is 4 cells, within-cell only; no irregular
  observation process; no measurement-update/correction step at all — the latent state evolves
  stochastically and is never corrected by an observation.
- **Overlap with DROCT**: M5's *framing* (latent degradation state + Transformer + RUL as state inference)
  is occupied almost verbatim. It does **not** occupy M5's correction step, because DSST has none.
- **Why it matters**: it is the paper a reviewer will cite to say "degradation state-space transformer is
  not new". The saving grace for DROCT is that DSST's battery evaluation is weak (4 cells, within-cell).

### P2 — KalmanNet
- **Title**: KalmanNet: Neural Network Aided Kalman Filtering for Partially Known Dynamics
- **DOI**: 10.1109/TSP.2022.3158588 — *IEEE Trans. Signal Processing* 70:1532–1547, 2022.
  Revach, Shlezinger, Ni, Escoriza, van Sloun, Eldar.
- **Read level**: ABS. **VERIFIED** (DOI resolved via ACM DL record + Revach publication list).
- **Question**: can a network learn the Kalman gain when the state-space model is only partially known?
- **Mechanism**: keep the KF predict step; replace the analytic gain with an RNN that maps innovation and
  covariance features to `K_t`; train end-to-end on state/measurement loss.
- **Structure**: KF recursion + GRU gain network.
- **Data/protocol**: synthetic linear/nonlinear tracking, real Lorenz/quadrotor-type state estimation.
- **Demonstrated**: learned gain recovers KF performance with mismatched/noisy models, beats EKF under
  model mismatch.
- **Limitations**: no battery; no irregular observation arrival; gain network is data-hungry.
- **Overlap**: **M5's `K` is KalmanNet's `K`.** This is the mechanism's origin.

### P3 — KalmanFormer
- **Title**: KalmanFormer: using transformer to model the Kalman Gain in Kalman Filters
- **DOI**: 10.3389/fnbot.2024.1460255 — *Frontiers in Neurorobotics* 18:1460255, published 2025-01-07.
  Shen, Chen, Yu, Zhai, Han.
- **Read level**: **FULL** (Frontiers HTML). **VERIFIED.**
- **Question**: can a Transformer learn the Kalman gain directly from data without noise covariances?
- **Mechanism**: standard KF predict/update; Transformer maps a window of innovations/state features to
  `K_k`; no `Q`/`R` needed.
- **Structure**: Transformer encoder → gain head → KF recursion.
- **Data/protocol**: synthetic nonlinear tracking + a real dataset; compared against EKF in identical
  settings.
- **Demonstrated**: better hidden-state tracking than EKF under nonlinearity and model mismatch.
- **Limitations**: no battery, no RUL, no irregular sampling; small-scale.
- **Overlap**: **M2 + M5 combined.** "Transformer outputs the gain of a Kalman filter" is exactly the
  architectural idea a reviewer will read into DROCT. This is the single most damaging *architectural*
  precedent for the claim that "transformer + learned gain" is new.

### P4 — Hybrid Neural-Kalman Filtering for Robust Battery Health Estimation
- **Title**: Hybrid Neural-Kalman Filtering for Robust Battery Health Estimation
- **DOI**: 10.1109/ECCE58356.2025.11259867 — *2025 IEEE Energy Conversion Congress and Exposition (ECCE)*,
  issued 2025-10-19. Sayed & Mahmoud (Kennesaw State University).
- **Read level**: ABS (IEEE Xplore landing + Crossref metadata). **VERIFIED.**
- **Question**: can KalmanNet be applied to battery SOH estimation to trade accuracy against compute?
- **Mechanism**: KalmanNet — KF recursion with a learned gain — applied to a battery SOH state.
- **Data/protocol**: not visible at abstract level (UNVERIFIED).
- **Demonstrated (authors' claim)**: "first to apply KalmanNet for battery SOH"; better accuracy/compute
  trade-off than plain KF and than deep learning alone.
- **Limitations**: conference paper, SOH not RUL, regular cycling assumed (UNVERIFIED), no dual-rate/RPT
  arrival semantics visible.
- **Overlap**: **the closest single prior art to M5.** Same mechanism (learned-gain KF), same domain
  (battery health), different target (SOH vs RUL). If DROCT's novelty is M5, this paper is the rebuttal.

### P5 — Multi-Observation Fusion Method for RUL of Li-ion Batteries
- **Title**: Multi-Observation Fusion Method for Predicting the Remaining Useful Life of Lithium-Ion Batteries
- **DOI**: 10.23919/CJEE.2025.000151 — *Chinese Journal of Electrical Engineering*, issue 2026-03.
  Chen, Peng, Sun, Wang, Yang (CSG Energy Storage Research Institute; BIT).
- **Read level**: ABS (IEEE Xplore + Crossref). **VERIFIED.**
- **Question**: can an EKF fuse *different kinds of capacity observations* for battery RUL?
- **Mechanism**: EKF over an aging state; replaces conventional aging-capacity-test values with
  operational capacity data and fuses multiple observation sources.
- **Demonstrated**: improved long-term RUL accuracy over a history-only EKF; reduced dependence on
  dedicated aging tests.
- **Limitations**: EKF (not learned gain); journal is not TIM/TTE; details of the fusion operator not
  visible at abstract level (UNVERIFIED).
- **Overlap**: **M5 + M4 in a battery RUL filter.** "Correction from a different-rate / operational
  capacity observation instead of only the reference test" is already published. This kills the argument
  that "correcting a latent aging state with non-RPT-rate observations" is new.

### P6 — ConvTrans + tAPE
- **Title**: A Lithium-Ion Battery RUL Prediction Method Based on ConvTrans and tAPE Under Capacity
  Regeneration Noise and Low-Dimensional Time Series Data
- **DOI**: 10.1109/TIM.2025.3564016 — *IEEE Trans. Instrumentation and Measurement* 74:1–14, 2025.
  Chen, Lu, Wang, Ge, Xie.
- **Read level**: ABS (Semantic Scholar record + IEEE metadata). **VERIFIED.**
- **Question**: RUL under capacity-regeneration noise with low-dimensional long sequences.
- **Mechanism**: CEEMDAN decomposition of the capacity sequence; random-forest/Gini weighting of
  components; convolutional Transformer; **time absolute position encoding (tAPE)** instead of integer
  positional indices.
- **Data/protocol**: battery capacity sequences (dataset not specified at abstract level — UNVERIFIED).
- **Demonstrated**: improved RUL accuracy vs compared baselines under regeneration noise.
- **Limitations**: position encoding is a single time axis; no multi-clock bias; no observation process.
- **Overlap**: **claim (b)'s core ingredient, in the target venue.** "Use real time, not integer index, in
  the Transformer's positional encoding for battery RUL" is already an IEEE TIM paper. DROCT's Δt term is
  a strict subset of this idea.

### P7 — IIP-Mixer
- **Title**: IIP-Mixer: Intra–Inter-Patch Mixing Architecture for Battery Remaining Useful Life Prediction
- **DOI**: 10.3390/en17143553 — *Energies* 17(14):3553, 2024. Ye, Feng, Guo, Chen.
- **Read level**: **FULL** (MDPI HTML, methods + experiments + all tables). **VERIFIED.**
- **Question**: can an all-MLP patch-mixing architecture beat Transformers/Informer/DLinear for RUL?
- **Mechanism**: split the cycle-level multivariate series into patches; parallel dual-head MLP mixing
  along the intra-patch (time-within-patch) and inter-patch (same position across patches) axes; weighted
  MSE; linear projection to the forecast horizon.
- **Structure**: patchify → 2-D patch matrix + transpose → intra/inter MLP → add → flatten → linear head.
- **Data**: NASA PCoE, **4 cells** (B0005/B0006/B0007/B0018); train on 2, validate on 1, test on 1.
- **Protocol**: single cell-held-out test; 16-step input, 4-step output; grid search on the validation cell;
  3 seeds (per the repo's earlier read).
- **Demonstrated**: MAE 0.037 Ah vs DLinear 0.041, Transformer 0.055, Informer 0.049; ablations for
  dual-head, parallel vs serial, weighted loss, feature selection.
- **Limitations**: 4 cells, one test cell, no condition diversity, no RPT, no irregular observation;
  the "patch" is over a univariate/multivariate cycle series, not over grouped raw per-cycle records.
- **Overlap**: **claim (a).** Patch-over-cycle-series for battery RUL is published and is the paper's
  entire title. It is MLP not Transformer, but the patching mechanism is identical in spirit; the
  Transformer version exists in CyclePatch (P8) and PatchTST-MKAN (P13).

### P8 — BatteryLife / CyclePatch
- **Title**: BatteryLife: A Comprehensive Dataset and Benchmark for Battery Life Prediction
- **URL**: arXiv:2502.18807 (v7, 2025-11-12); **KDD 2025**. Tan et al.
- **Read level**: ABS (arXiv). **VERIFIED.**
- **Question**: is there a large, diverse, standardised benchmark for battery life prediction, and which
  time-series architectures actually work on it?
- **Mechanism**: 16 datasets, 2.5× the prior largest sample; 8 formats, 59 chemical systems, 9 temperatures,
  421 protocols. **CyclePatch**: a plug-in that treats cycles as tokens and models intra-cycle and
  inter-cycle information; instantiated as CPMLP and **CPTransformer**.
- **Protocol**: 18 methods benchmarked; seen vs unseen aging conditions; cross-domain transferability.
- **Demonstrated**: models popular in general time-series can be unsuitable for battery life; CyclePatch
  improves performance across backbones and establishes SOTA benchmarks.
- **Limitations**: life prediction (one-shot), not online RUL; no RPT arrival process; CyclePatch is a
  representation plug-in, not a state-space filter.
- **Overlap**: **M1 + M2.** "Cycle as token / group cycles into patches / transformer over cycles" is
  occupied at KDD 2025 with a much larger benchmark than DROCT will have.

### P9 — BatteryCDE
- **Title**: BatteryCDE: A Transferable Future Capacity Estimation Method for Battery Degradation With
  Irregular Sampling and Missing Data
- **DOI**: 10.1109/TTE.2025.3547740 — *IEEE Trans. Transportation Electrification*, 2025-08.
  Wang, Ren, Xiong, Song, Dong.
- **Read level**: ABS (TRID + CityU record). **VERIFIED.**
- **Question**: capacity estimation under irregular sampling, missing data, and cross-chemistry transfer.
- **Mechanism**: build a continuous data path by cubic-spline interpolation; neural controlled differential
  equation (CDE) produces feature-wise and cycle-wise attention; a second neural CDE models the dynamics;
  transferable across battery types.
- **Demonstrated**: handles irregular sampling and missing data; transfers across battery types; long-term
  estimation.
- **Limitations**: continuous-time interpolation of the *input path*, not an observation-correction state;
  no RPT-specific arrival semantics; no learned Kalman gain.
- **Overlap**: **M3 + the irregular-observation motivation.** "Irregular sampling / missing observations"
  as the problem is occupied in IEEE TTE 2025.

### P10 — Physics-augmented neural CDE for SOH under missing cycling data
- **Title**: Physics-augmented neural controlled differential equations for lithium-ion battery
  state-of-health prediction under missing cycling data
- **DOI**: 10.1016/j.jpowsour.2026.239987 — *Journal of Power Sources*, 2026-06.
  Toom, Perinpanayagam, Hosseinzadeh.
- **Read level**: **META** (DOI + venue + title via Crossref; abstract not obtainable — Elsevier closed).
  **VERIFIED metadata, UNVERIFIED content.**
- **What the title establishes**: "physics-augmented neural CDE" + "SOH prediction" + "missing cycling
  data" is published in JPS 2026. That is the same problem statement as DROCT's M3/M5 motivation.
- **Overlap**: irregular/missing observation modelling for battery SOH.
- **Caveat**: I did not read the method. Do not cite its internals; cite it only as evidence that the
  problem is occupied.

### P11 — SambaMixer
- **Title**: SambaMixer: State of Health Prediction of Li-Ion Batteries Using Mamba State Space Models
- **DOI**: 10.1109/ACCESS.2024.3524321 — *IEEE Access* 13:2313–2327, 2025. Olalde-Verano et al.
- **Read level**: ABS (IEEE Access PDF + Scopus record). **VERIFIED.**
- **Question**: can a selective state-space model (Mamba) predict SOH from multivariate cycle signals?
- **Mechanism**: Mamba S6 blocks over resampled cycle signals; anchor-based resampling to a fixed length;
  **time-based positional encoding to handle sample jitter, variable-length signals, and recovery effects**.
- **Data**: NASA PCoE discharge cycles.
- **Demonstrated**: beats SOTA deep models on NASA; code released.
- **Limitations**: SOH not RUL; single small dataset; no RPT/irregular observation process; the model is
  per-cycle independent (authors note prediction for cycle k does not depend on k−1).
- **Overlap**: **M2's time-aware encoding** and the "state space model for battery" framing. Also a warning:
  a Mamba SSM is a stronger "state space" claim than DROCT's, and it is already in IEEE Access.

### P12 — RPT-reduced SOH estimation
- **Title**: Data-Driven State of Health Estimation of Li-Ion Batteries with RPT-Reduced Experimental Data
- **DOI**: 10.1109/ACCESS.2019.2932719 — *IEEE Access* 7:106987–106997, 2019. Kim et al.
- **Read level**: ABS (Scopus + IEEE PDF header). **VERIFIED.**
- **Question**: can SOH be estimated when reference performance tests are deliberately reduced?
- **Mechanism**: data-driven SOH regression trained on cycling data with fewer RPT labels.
- **Demonstrated**: reduced-RPT training remains viable; motivates replacing frequent RPTs with models.
- **Limitations**: 2019, no transformer, no state-space, no arrival process.
- **Overlap**: **the sparse-RPT problem statement** that M3 assumes is new. It is not new; it is 2019.

### Also close, not in the top 12 (metadata verified, method not read)
- **PatchTST-MKAN** — Ma, Zhou, Wu, Liu, *Engineering Research Express* 8:015312, 2025/2026.
  PatchTST (patch transformer) + MKAN for battery RUL. Direct occupancy of claim (a); DOI UNVERIFIED.
- **MambaLithium** — Shi, arXiv:2403.05430, 2024. Mamba for RUL/SOH/SOC.
- **DeepSOH** — arXiv:2405.12028, 2024. Path dependency for RUL; argues sparse measurements without
  dynamics are error-prone. Conceptual support for a state-space view, not a mechanism precedent.
- **EvoNAS4Battery** — Chen, Mao, Chen, Shen, *IEEE TIM* 2025, DOI 10.1109/TIM.2025.3573358. NAS for RUL.
- **Bao et al.** — lightweight term-arbitrary memory network, *IEEE TIM* 2025, DOI 10.1109/TIM.2025.3556835.
- **DS-transformer** — dual-stream cross-attention fusion of discharge + impedance, *Scientific Reports*
  2026, DOI 10.1038/s41598-026-52202-6 (from search snippet; META).

---

## 2. Dedicated prior-art sweep on the observation-correction mechanism

### 2.1 Learned Kalman gain / neural Kalman filter for battery SOH or RUL
**Exists, and is battery-specific.** KalmanNet (TSP 2022) is the origin: keep the KF recursion, learn the
gain with an RNN. KalmanFormer (Frontiers 2025) does the same with a Transformer. Sayed & Mahmoud
(ECCE 2025) apply KalmanNet to battery SOH and claim to be first. Chen et al. (CJEE 2026) fuse multiple
capacity observations in an EKF for battery RUL. On the classical side, AUKF+CNN-BiLSTM hybrids
(e.g. IEEE 10606840, 2024) use a Kalman filter to correct a network's output — the inverse direction, but
the same "KF corrects a learned estimate" story.
**Distinguishable?** No. M5's equations are the KF predict/update with neural `K` and `H`. The battery
application exists (SOH). The RUL application with multi-observation correction exists (CJEE). The only
remaining delta is "RUL + RPT arrival + dual-rate encoder", which is a composition.

### 2.2 GRU-D and decay-based irregular-observation models applied to batteries
**GRU-D itself is not a battery paper** (Che et al., 2018, Scientific Reports — general clinical time
series). I did **not** find a peer-reviewed paper that applies GRU-D specifically to battery SOH/RUL.
That is a genuine negative result, but it is a weak novelty hook: GRU-D's decay mechanism is a special case
of "input imputation with time-gap decay", and the battery literature already handles irregular/missing
observations with neural CDEs (BatteryCDE, TTE 2025; Toom et al., JPS 2026) and neural ODEs
(RBF-KAN-nODE, J. Energy Storage 2027, DOI 10.1016/j.est.2026.125339). Applying GRU-D to batteries would be
a straightforward transfer, not a mechanism.
**Distinguishable?** No — the *problem* (irregular/missing battery observations) is occupied; only the
specific backbone is not.

### 2.3 Neural state-space models (deep state space, S4/Mamba) for battery degradation
**Exists.** DSST (RESS 2026) is a latent monotone degradation state-space with a Transformer encoder and
FPT RUL. SambaMixer (IEEE Access 2025) is Mamba S6 for SOH. MambaLithium (arXiv 2024) is Mamba for
RUL/SOH/SOC. DeepSOH (arXiv 2024) argues for state/dynamics over sparse measurements.
**Distinguishable?** No for the "latent state + sequence model + RUL" framing. Yes for one narrow thing:
none of these has an explicit *measurement-update at irregular observation times*. DSST has no correction
step at all; SambaMixer predicts each cycle independently; MambaLithium is a regressor. So the correction
step is the only surviving sliver — and it is exactly the sliver that KalmanNet/ECCE-2025 occupies.

### 2.4 "Observation-corrected" / "measurement-updated" latent degradation state
**Exists in substance, not always in name.** The phrase "observation-corrected" is not standard, but the
operation is: EKF/UKF battery RUL with capacity observations (many papers, e.g. the CJEE 2026
multi-observation EKF); AUKF-corrected CNN-BiLSTM (IEEE 2024); Bayesian updating of degradation paths with
particle filters (Brumm et al., QRE 2025, per the repo's earlier read); DSST's latent-state inference.
**Distinguishable?** No. Renaming the update step does not create a mechanism. A reviewer will map
"propagate / correct only when an RPT arrives" directly onto "predict / update only when a measurement
arrives", which is the definition of a filter.

### 2.5 Multi-rate / dual-rate sensor fusion for batteries
**Exists.** Multi-observation EKF fusion of operational capacity and aging-test capacity for RUL (CJEE
2026). Variable-time-scale capacity estimation with a dual EKF (J. Power Electronics 2026, DOI
10.1007/s43236-026-01398-x) explicitly targets the "fixed sampling interval" limitation. BatteryCDE
(TTE 2025) handles irregular sampling. The ISU-ILCC dataset itself is dual-rate by construction (1 Hz
cycling + weekly RPT).
**Distinguishable?** Partially. "Fuse two rates" is occupied. What is *not* obviously occupied is a
**clock-resolved identifiability analysis**: showing that calendar time and cycle count/charge throughput
are separately identifiable under leave-one-condition-out, because the ΔN/Δt ratio varies across
conditions. That is an analysis contribution, not an architecture contribution.

### 2.6 Transformer attention with physical-time bias
**Exists.** ConvTrans+tAPE (IEEE TIM 2025) uses time absolute position encoding for battery RUL.
SambaMixer (IEEE Access 2025) uses time-based positional encoding for jitter/variable length. RoPE-v1
(IEEE 2026, DOI 10.1109/...11581949 — META) puts scaled physical timestamps inside the rotary operator for
irregular sampling. ALiBi and continuous-time positional encodings are standard in the sequence-model
literature.
**Distinguishable?** The exact triple `b(Δt, ΔN, ΔQ)` was **not found**. But: (i) each scalar is a known
clock; (ii) a linear bias over three scalars is a reparameterisation of known relative-position biases;
(iii) in this cohort the three clocks are strongly collinear *within* a condition group (fixed C-rate and
DOD ⇒ ΔQ ≈ c·ΔN; fixed schedule ⇒ Δt ≈ s·ΔN), so the "joint" bias is only identifiable *across* conditions,
i.e. exactly where LOCO removes the training signal. A reviewer can attack this as unidentifiable rather
than novel.

---

## 3. Verdicts on the three claims

### (a) "Patch transformer over cycle-level battery data is new" → **OCCUPIED**
Closest:
1. **IIP-Mixer**, Energies 17(14):3553, 2024, DOI 10.3390/en17143553 — patchify cycle-level series,
   intra/inter-patch mixing, RUL. FULL read.
2. **CyclePatch / CPTransformer**, BatteryLife, KDD 2025, arXiv:2502.18807 — cycles as tokens,
   intra/inter-cycle modelling, transformer instantiation, 16 datasets.
3. **PatchTST-MKAN**, Engineering Research Express 8:015312, 2025/2026 — PatchTST for battery RUL.

Evidence quality: high (one full-text read, one KDD benchmark, one title-level). The only untouched
nuance is "patch = a group of raw per-cycle records encoded by a light CNN/MLP" — which is exactly what
PatchTST and CyclePatch do. **Do not claim this.**

### (b) "Attention bias using real elapsed time, cycle count and measured Ah jointly is new" →
**PARTIALLY OCCUPIED**
Closest:
1. **ConvTrans + tAPE**, IEEE TIM 74:1–14, 2025, DOI 10.1109/TIM.2025.3564016 — real-time positional
   encoding in a battery RUL transformer, in the target venue.
2. **SambaMixer**, IEEE Access 13:2313–2327, 2025, DOI 10.1109/ACCESS.2024.3524321 — time-based positional
   encoding for jitter and variable length.
3. **RoPE-v1** (IEEE 2026, META) — physical timestamps inside rotary encoding for irregular sampling.

Verdict logic: the *exact conjunction* of Δt, ΔN, ΔQ was not found. But each term is standard, and the
conjunction is a linear combination of known biases. Worse, in ISU-ILCC the three clocks are nearly
collinear within a condition group, so the joint bias is weakly identified. A reviewer will call this an
engineering choice, not a contribution. If the paper wants to keep it, it must show an ablation where each
clock is removed and the *held-out-condition* error changes in a predictable direction — not just an
in-sample improvement.

### (c) "Observation-corrected latent degradation state with a learned gain under irregular RPT arrival
is new" → **OCCUPIED (as a mechanism)**
Closest:
1. **Sayed & Mahmoud**, *Hybrid Neural-Kalman Filtering for Robust Battery Health Estimation*, IEEE ECCE
   2025, DOI 10.1109/ECCE58356.2025.11259867 — KalmanNet (learned gain) for battery SOH; authors claim
   first application.
2. **KalmanFormer**, Frontiers in Neurorobotics 18:1460255, 2025, DOI 10.3389/fnbot.2024.1460255 —
   Transformer learns the Kalman gain. FULL read.
3. **Chen et al.**, *Multi-Observation Fusion Method for RUL*, Chinese J. Electrical Engineering, DOI
   10.23919/CJEE.2025.000151 — EKF correction of a battery RUL state from multiple/different-rate capacity
   observations.
Supporting: KalmanNet (TSP 2022), DSST (RESS 2026), Kim et al. (IEEE Access 2019, RPT-reduced SOH),
BatteryCDE (TTE 2025, irregular sampling).

Verdict logic: the exact conjunction "learned-gain correction + RPT arrival + RUL" is not in one paper.
But the mechanism is KalmanNet, the battery application is ECCE 2025, the multi-observation RUL correction
is CJEE 2026, and the latent-state-transformer framing is DSST. A conjunction of four occupied parts with
no new identifiable object is not novelty. **A hostile reviewer will reject "we renamed a Kalman filter",
and on this evidence they would be right.**

---

## 4. Candidate mechanisms that would actually be distinguishable

These assume the four constraints: irregular observation times, genuinely different sampling rates, strong
between-condition heterogeneity, leave-one-condition-out evaluation. Each candidate states the observation
that would refute it.

### Candidate A — Clock-resolved identifiability (calendar vs cycle/throughput)
**Mechanism.** Maintain the degradation state on two clocks explicitly: a calendar-time channel and a
cycle/charge-throughput channel, with separate rate parameters and separate noise. The RPT observation
operator is defined on the *reference* clock, but the propagation between RPTs is the composition of the
two channels. The scientific claim is not "we added a bias" but "the two channels are separately
identifiable because ΔN/Δt varies by an order of magnitude across the 63 condition groups, and a
single-clock model is biased in a condition-dependent way".
**Why it is distinguishable.** It makes a directional prediction: error should correlate with ΔN per RPT
interval (i.e. with cycles-per-week), and the single-clock model should fail specifically on low-rate /
low-DOD groups (many cycles per week) and on high-rate groups (few cycles per week). That is a
leave-one-condition-out prediction, not an in-sample fit.
**Refuting observation.** Fit the two-channel model and a one-channel model with the same parameter count.
If the learned calendar-channel rate collapses to zero (or the two channels' gains are statistically
indistinguishable across all conditions), or if the error-vs-ΔN correlation is absent on held-out
conditions, the mechanism is refuted. Also refuted if a single clock plus condition one-hot matches it
under LOCO.

### Candidate B — Condition-descriptor-conditioned rate map with extrapolation test
**Mechanism.** Generate the individual degradation-rate state from a low-dimensional condition descriptor
(charge C-rate, discharge C-rate, mean DOD) through a monotone map, with a shared backbone and
condition-specific low-rank adaptation. The point is that LOCO forces the model to *extrapolate* the
descriptor→rate map to an unseen condition, rather than memorise condition identity.
**Why it is distinguishable.** It predicts which held-out conditions are hard: error should grow with
distance from the training condition manifold in descriptor space, and the learned map should be monotone
in C-rate and DOD where the physics says it is. A plain per-cell pooled model cannot make either
prediction.
**Refuting observation.** If a condition-one-hot model (no descriptor structure) matches the hierarchical
model under LOCO, the descriptor map is not doing anything. If held-out-condition performance equals the
global-mean-rate baseline, the map is not extrapolating. If the learned map is non-monotone in C-rate/DOD
in the region where the training data is dense, the mechanism is mis-specified.

### Candidate C — Source-time vs arrival-time observation semantics with censoring-aware likelihood
**Mechanism.** Treat every RPT as an event with a *source time* (when the test was performed) and an
*arrival time* (when the report becomes visible). The filter must (i) correct using the source time, not
the arrival time, and (ii) condition on the fact that no report has arrived between the last arrival and
the query time (a censoring term). The claim is that arrival semantics, not the correction equation, is
the identifiable object.
**Why it is distinguishable.** It predicts a specific failure mode: a filter that timestamps observations
at arrival will err during delays, and the error should grow with delay length; a filter with a censoring
term should beat one without it exactly on the delayed arm.
**Refuting observation.** On the delay7d arm, if source-time stamping and arrival-time stamping give
statistically indistinguishable results (paired CIs include zero), the mechanism is vacuous. If the
censoring term does not improve NLL/Brier on the sparse2 arm, it is not doing anything.
**Critical caveat.** The ISU-ILCC dataset description says RPTs are **scheduled**: weekly, plus an extra
RPT after 3.5 days for groups 20–64. So arrival is *protocol-driven*, not state-dependent. Candidate C is
only honest if the paper says "reporting delay is a policy perturbation we impose", not "arrivals are
irregular in nature". If the paper claims natural irregularity, a reviewer who reads the dataset
description will catch it.

---

## 5. Public datasets that could serve as a genuinely independent second cohort

Requirements: per-cycle operation data AND a different-rate health observation, clear cell identity,
definable EOL, enough cells/conditions.

| Dataset | What is actually in it (verified) | Per-cycle | Different-rate health obs | Cells / conditions | EOL | Same modality? |
|---|---|---|---|---|---|---|
| **ISU-ILCC NMC/Gr** | 251 cells, 63 groups; per-cell JSON with cycling + RPT; RPT weekly, extra 3.5-day RPT for groups 20–64; DOI **10.25380/iastate.22582234** | Yes (1 Hz) | Yes (~7 d) | 251 / 63 | Yes | Primary cohort — not independent |
| **UConn-ISU-ILCC LFP/Gr** | 64 LithiumWerks APR18650M1B, 11 conditions, RPT every ~3.5 d (~100 cycles), 1 Hz, 38 weeks, EOL 80% | Yes | Yes | 64 / 11 | Yes | Same lab/protocol lineage; chemistry-transfer cohort, not fully independent |
| **MATR-11 "aging matrix"** | 359 NCA/graphite+SiOx 21700, 207 protocols, 16 SOH metrics incl. electrode-specific capacities, EFC, knee, impedance; raw 178 GiB; DOI **10.1039/d4ee05609d**; data at data.matr.io/11 | Likely (raw telemetry) | Likely periodic diagnostic; **cadence UNVERIFIED** | 359 / 207 | Yes | **Best independent candidate** if RPT/diagnostic cadence confirmed |
| **Sandia / Battery Archive** | LFP/NCA/NMC 18650, 12-condition matrix, ≥2 cells/condition, capacity check at round boundaries (125–1000 cycles), EIS at ~3% capacity loss, EOL 80%; DOI **10.1149/1945-7111/abae37** | Per-cycle summary (raw telemetry partial) | Yes (capacity check + EIS) | ~60–70 / 12 (count UNVERIFIED) | Yes | Strong; but M1's intra-cycle patching would be degraded to summary features |
| **HUST** | 77 commercial cells, >140,000 cycles, knee-point degradation (secondary sources) | Yes | No separate RPT verified | 77 / ? | Yes | Degraded — single modality |
| **CALCE CS2/CX2** | Small LiCoO2 cohort, per-cycle capacity | Yes | Limited | ~4–8 / few (UNVERIFIED) | Yes | Degraded — too few conditions for LOCO |
| **NASA PCoE** | 4 cells (B0005/B0006/B0007/B0018), per-cycle + EIS at intervals, EOL 30% fade | Yes | Yes (EIS) | 4 / 1 | Yes | Sanity check only |
| **Oxford** | 8 Kokam LCO cells, characterisation every ~100 cycles (reported; not re-verified here) | Yes | Yes | 8 / 1 | Yes | Small, single condition |
| **Severson / TRI (MATR-1)** | 124 LFP cells, fast-charging protocols, per-cycle capacity | Yes | **No** separate RPT | 124 / many | Yes | **Cannot** support dual-rate |
| **SDU multi-stage** | Stroebl et al., *Scientific Data* 11, 2024, DOI 10.1038/s41597-024-03859-z | UNVERIFIED | UNVERIFIED | UNVERIFIED | Yes | UNVERIFIED — check before use |
| **BatteryLife** | 16 datasets harmonised, KDD 2025 | Mixed | Mixed | Large | Varies | Meta-dataset, not independent |

**Recommendation.** The only two candidates that plausibly support the *same input modality* (per-cycle
telemetry + a slower reference health observation) are **MATR-11** and **Sandia/Battery Archive**.
- MATR-11 is the stronger one on cell count and condition diversity, but its diagnostic cadence must be
  verified from the EES paper before it is used to claim "same modality".
- Sandia is verified to have capacity checks and EIS at a different rate, but the public per-cycle data is
  largely summary-level; it is a good test of the *filter* and a poor test of the *intra-cycle patch
  encoder*.
- UConn-ISU-ILCC LFP is the cleanest like-for-like replication (same RPT concept, 1 Hz) but it is the same
  lab lineage and only 11 conditions — it is a chemistry-transfer test, not an independent cohort.
- HUST, CALCE, NASA, Oxford, Severson are **degraded single-modality** validations. They can support a
  "does the filter still work without RPT?" claim, not "the dual-rate mechanism generalises".

---

## 6. The single biggest threat to the novelty claim

**M5 is a learned-gain Kalman filter, and the battery-specific version of exactly that is already
published.** Sayed & Mahmoud (IEEE ECCE 2025) claim the first KalmanNet application to battery SOH;
KalmanFormer (2025) already puts a Transformer on the gain; Chen et al. (CJEE 2026) already correct a
battery RUL state from multiple/different-rate capacity observations; DSST (RESS 2026) already frames RUL
as inference over a latent degradation state with a Transformer. The only unoccupied object is the
*conjunction* — RUL + RPT arrival + dual-rate encoder — and a conjunction of four occupied parts is an
application composition, not a mechanism. A hostile TIM reviewer will say "we renamed a Kalman filter",
and the current evidence does not give a clean answer to that.

The second, quieter threat is empirical: the repo's own results (`.control/paper/FULL_DRAFT_V1.md`) show
the filter **ties** the best gradient-boosted trees on MAE (+12 µAh, CI [−354, +414]) and wins only on
predictive density. A paper whose novelty is a mechanism but whose mechanism only wins on NLL is in a weak
position. The honest framing is the one the draft already uses: the contribution is the **as-of protocol,
arrival semantics, sample efficiency, and scheduling value**, not the filter equation. If the paper keeps
that framing and cites KalmanNet/KalmanFormer/ECCE-2025 explicitly, it can survive. If it presents M5 as
the novelty, it will not.

---

## 7. What I would tell the authors (short)

1. **Do not claim M5.** Cite KalmanNet, KalmanFormer, Sayed & Mahmoud 2025, and Chen et al. 2026 in the
   first related-work paragraph, then say what you add that they do not: arrival semantics, as-of
   validity, dual-rate identifiability, and decision-level evaluation.
2. **Do not claim the patch transformer.** IIP-Mixer, CyclePatch, PatchTST-MKAN own it.
3. **Do not claim the joint attention bias as a mechanism.** Either show a LOCO ablation where each clock
   changes held-out error in a predicted direction, or drop it to a design detail.
4. **Fix the "irregular arrival" premise.** ISU-ILCC RPTs are scheduled (weekly, +3.5 d for groups 20–64).
   The sparse2/delay7d arms are *policy perturbations you impose*. Say so. If you claim natural
   irregularity, a reviewer who reads the dataset description will catch it.
5. **The defensible contribution is empirical**: a strict as-of protocol, a calibrated predictive density,
   sample efficiency at 25–50% of cells, and a scheduling policy that beats a fixed 4-week schedule. That
   is a TIM paper. The filter is the instrument, not the contribution.

---

## Verification ledger

| Item | Source used | Level |
|---|---|---|
| DSST | ScienceDirect S0951832026014882; Crossref 10.1016/j.ress.2026.113686 | ABS + intro, VERIFIED |
| KalmanNet | ACM DL 10.1109/TSP.2022.3158588; Revach publication list | ABS, VERIFIED |
| KalmanFormer | Frontiers full text 10.3389/fnbot.2024.1460255 | FULL, VERIFIED |
| Hybrid Neural-Kalman | IEEE Xplore 11259867; Crossref 10.1109/ECCE58356.2025.11259867 | ABS, VERIFIED |
| Multi-observation EKF | IEEE Xplore 11207180; Crossref 10.23919/CJEE.2025.000151 | ABS, VERIFIED |
| ConvTrans+tAPE | Semantic Scholar 10.1109/TIM.2025.3564016 | ABS, VERIFIED |
| IIP-Mixer | MDPI full text 10.3390/en17143553 | FULL, VERIFIED |
| BatteryLife | arXiv:2502.18807 | ABS, VERIFIED |
| BatteryCDE | Crossref 10.1109/TTE.2025.3547740; TRID; CityU | ABS, VERIFIED |
| JPS neural CDE | Crossref 10.1016/j.jpowsour.2026.239987 | META, VERIFIED |
| SambaMixer | Scopus/IEEE 10.1109/ACCESS.2024.3524321 | ABS, VERIFIED |
| Kim RPT-reduced | Scopus/IEEE 10.1109/ACCESS.2019.2932719 | ABS, VERIFIED |
| ISU-ILCC | figshare 10.25380/iastate.22582234; dataset description PDF; HF loader script | VERIFIED |
| UConn-ISU-ILCC | digitalcommons.lib.uconn.edu/reil_datasets/1 | VERIFIED |
| MATR-11 | OSTI 2575174; Crossref 10.1039/d4ee05609d; data.matr.io/11 | VERIFIED (protocol cadence UNVERIFIED) |
| Sandia | IOP full text 10.1149/1945-7111/abae37 | VERIFIED (cell count UNVERIFIED) |
| HUST | HAL hal-04795354; MDPI Batteries 12(9):359 | Secondary, VERIFIED count only |
| CALCE / Oxford / SDU | not re-verified this session | UNVERIFIED |

No paper, author, DOI, venue, or number above was invented. Items marked UNVERIFIED are exactly the ones
I could not resolve to a primary source in this session.
