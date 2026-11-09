# DATA IDENTIFIABILITY · question A

> Programme: `online-mechanisms-20261110`
> Audit run: 2026-11-10, by data/protocol identifiability auditor
> Scope: can the proposed **online exposure-advancing predictor** be identified on the data actually on disk?
> Every number below was computed from the files in this session. Probe scripts: `protocol/_probe/*.py`. Machine-readable outputs: `protocol/_probe/*.json`, `*_eol*.csv`.

---

## 0. The question under audit

An online predictor that (i) advances by **real operating exposure** (Ah-throughput / equivalent full cycles / physical time) rather than one fixed step per RPT, (ii) **corrects only when a real measurement arrives**, and (iii) handles **interval-censored EOL** (first hitting time of 80% SOH) and **right-censoring**.

The load-bearing clause is (i). To test "advance by exposure" against "one step per RPT" you must observe exposure **between** RPTs at a finer granularity than the RPT grid. That is the axis this audit tests hardest.

---

## 1. Inventory of data sources

| # | Path | Size (bytes) | What it actually is | Schema | Supports |
|---|---|---|---|---|---|
| 1 | `E:\桌面\rul\data\external\uconn\data_cc_1.pkl` | 70,370,957 (70.37 MB) | RPT-level **summary table** + fixed-length diagnostic voltage matrices. **Not** raw cycling. | `dict`, 13 keys, all `np.ndarray`: `cell_id`, `group_id`, `rpt`, `num_cycles` (float), `voltage` (14373×600), `q_dchg`, `soh`, `dcir_chg_20/50/90`, `dcir_dchg_20/50/90` | RPT-level SOH, per-RPT cycle-segment length, DCIR at 3 SOCs |
| 2 | `E:\桌面\rul\data\external\uconn\data_slowpulse_1.pkl` | 16,034,596 (16.03 MB) | RPT **pulse (DCIR) traces** | `dict`, 16 keys: same as above **plus** `soc` (20/50/90), `soc - coulomb`, `pulse_type` (`chg`/`dchg`); `voltage` (17130×101) | 6 pulse curves per RPT (3 SOC × 2 directions) |
| 3 | `E:\桌面\rul\data\external\isu_raw\RPT_json.zip` | 929,406,930 (929.4 MB) | 251 per-cell RPT JSONs (+1 `.m` example); 25.9–70.4 MB each | double-encoded JSON; 10 top-level keys: `capacity_{discharge,charge}_{C_2,C_5}` (16–80 scalars), `QV_{discharge,charge}_{C_2,C_5}` = `{Q,V,t,E,I}` per RPT, **`start_stop_time` = `{start,stop}` datetime lists**, `DCR` | RPT capacity, within-RPT `t`/`I`, **real calendar timestamps** |
| 4 | `E:\桌面\rul\data\external\isu_raw\Q_interpolated.zip` | 47,797,453 (47.8 MB) | 251 CSVs, 999×17 interpolated capacity curves | header = 17 capacity values, 999 interpolated rows | interpolated curves only — **no new axis** |
| 5 | `E:\桌面\rul\data\external\isu_raw\Valid_cells.csv` | 1,727 | 251-cell roster (`G<cond>C<n>`) | 1 column `Cell` | cell roster |
| 6 | `E:\桌面\rul\data\external\isu_raw\one\G30C1.json` | 12,618,160 (12.62 MB) | one extracted zip member (identical schema) | as #3 | prototyping only |
| 7 | `E:\桌面\rul\data\external\README_uconn.txt` | ~0.02 MB | **Cloudflare "Just a moment…" challenge HTML**, not a README | — | evidence the UConn download path was bot-blocked |
| — | `E:\桌面\rul\data\external\uconn\cycling_part1.zip` | **MISSING** | official UConn REIL raw cycling (6.55 GB) | — | raw current/voltage/temperature, true per-cycle axis, calendar time |
| — | `E:\桌面\rul\data\external\uconn\cycling_part2.zip` | **MISSING** | official UConn REIL raw cycling (7.05 GB) | — | same |

**Verdict on item 1–2 being "raw operating records": they are not.** The `voltage` matrices are fixed-length narrow-window diagnostics: global span 74.4 mV (3.3485–3.4229 V), **per-record span median 19.0 mV, max 42.5 mV**. A full Li-ion discharge spans >1000 mV. These are pulse/relaxation segments at a fixed SOC, not cycles. There is **no current array and no temperature array anywhere in either pickle**.

Out-of-scope but present locally (not audited here): `bayreuth/` (48 F0xxx zips + `M0002_aging.txt` 41.69 MB), `nasa_pcoe/`, `calce/`, `severson/b1c0.parquet` (31.53 MB).

---

## 2. Field-level availability

Legend: **A** = available as recorded · **D** = derivable from recorded data (stated rule) · **M** = missing. "Visible at t" = usable as a feature at prediction time without look-ahead.

| Variable | UConn | ISU-ILCC | Visible at t? | Note |
|---|---|---|---|---|
| SOH at RPT | **A** (`soh`, 72.34–100.0) | **D** = capacity / capacity@RPT0 | only at an RPT arrival | the measurement that triggers correction |
| RPT index | **A** | **A** | ✅ | a counter, not a physical axis |
| Cumulative cycle count | **D** = `cumsum(num_cycles)`, see §3 caveat | **M** | ✅ (UConn) | no cycle field exists in ISU JSONs (regex scan for `*cycl*` keys → NONE) |
| Cycles between RPTs (segment length) | **A** as `num_cycles` (per-interval, **not** cumulative) | **M** | ✅ | confirmed independently by repo `FALSIFIED.md` F-005 ("`num_cycles` 是段长非累计") |
| Calendar timestamp per RPT | **M** — no `time`/`date`/`start`/`stop` key in either pickle | **A** — `start_stop_time`, 251/251 cells | ✅ (ISU) | the only *recorded* physical axis in the whole audit |
| Ah-throughput (cumulative) | **D** ≈ Σ `q_dchg`·segment — an **approximation** | **M** | ✅ (UConn, approx.) | requires per-cycle current; absent |
| Current I | **M** | **A only inside an RPT** (`QV_*.I`) | ⚠️ within-RPT only | never between RPTs |
| Voltage V | **A** as pulse segments (600 / 101 pts) | **A** inside RPT (`QV_*.V`) | ⚠️ | no continuous cycling voltage |
| Temperature | **M** | **M** | ❌ | no thermal channel in either dataset |
| EOL interval `[L,U]` | **D** (§4) | **D** (§4) | ❌ label only | never a feature |
| Right-censoring indicator | **A** — but **0** censored cells | **A** — **40** censored cells | ❌ label only | |
| Condition label | **A** `group_id` 1–11 | **A** `G<cond>` → 1–64 | ✅ | |
| Condition **factors** (C-rate, DoD) | **M** — only `group_id`; no factor table local | **A** `.research/results/isu_conditions.csv` | ✅ (ISU) | UConn's 11 conditions are unlabelled beyond their id |

---

## 3. Inspection cadence (numbers, not adjectives)

### 3.1 UConn — 2,855 RPT records, 64 cells, 11 conditions

Row grain: `(cell_id, rpt)` is the true unit. `data_cc_1.pkl` carries 2–6 rows per `(cell_id, rpt)` (mean 5.03: `{2:7, 3:109, 4:526, 5:1350, 6:863}`) with **bit-identical** `q_dchg`/`soh`/`num_cycles`, differing only in the `voltage` matrix — a storage artefact. `data_slowpulse_1.pkl` is exactly 6 rows per `(cell_id, rpt)` = 3 SOC × 2 pulse directions (2,855 × 6 = 17,130 ✓). Collapsing to `(cell, rpt)` gives **2,855 records / 64 cells / 11 conditions**.

RPTs per cell: **min 22, median 43, mean 44.61, max 77**.

**(a) Gap in RPT index** — essentially contiguous: `Δrpt = 1` for 2,790 consecutive pairs, `Δrpt = 2` once (cell 60 at rpt 75). So the RPT *index* carries almost no cadence information.

**(b) Gap in cumulative cycles** (= `num_cycles`, the segment length), n = 2,759 (2,727 non-NaN):

| stat | min | p05 | p25 | median | p75 | p95 | max | CV | max/min |
|---|---|---|---|---|---|---|---|---|---|
| cycles | 12 | 67 | 84 | **98** | 119 | 140 | 197 | **0.229** | **16.4×** |

Per-cell CV of the segment: median 0.091, p90 0.122, max 0.141. 57.9% of segments lie within ±20% of the global median. Cumulative cycles per cell: min 2,588, median 3,918, max 8,464.

**(c) Gap in calendar time** — **MISSING**. No timestamp field exists.

> Cadence is irregular enough to separate "per-RPT step" from "per-cycle advance" (CV 0.229, 16.4× range), but the irregularity is *slow drift* (segments grow ~100 → ~147 late in life), not random jitter. Any test of "advance by exposure" on UConn is therefore confounded with a **time-varying segment length that is itself a function of aging**.

### 3.2 ISU-ILCC — 251 cells, 63 conditions

RPTs per cell: **min 2, max 80, median 20**; distribution is broad (`{5:40, 16:20, 17:14, 15:13, 21:11, 26:10, 20:9, 29:9, 28:8, 19:8, …}`). 40 cells have exactly 5.

**(c) Gap in calendar time** (from `start_stop_time.start`), n = 4,669 consecutive gaps:

| stat | min | p05 | p25 | median | p75 | p95 | max | mean | sd | CV |
|---|---|---|---|---|---|---|---|---|---|---|
| days | 4.33 | 4.91 | 7.99 | **8.01** | 8.48 | 10.01 | 16.19 | 8.20 | 1.42 | **0.174** |

Deciles (days): 4.33, 7.85, 7.97, 7.99, 8.00, 8.01, 8.06, 8.29, 8.87, 9.29, 16.19. Campaign span: min 8.0, median **141.1**, max 674.1 days.

**(b) Gap in cycles** — **MISSING**. No cycle counter exists in the ISU release.

> ISU's RPT schedule is a near-perfect weekly grid (median 8.01 d, CV 0.174) with a handful of 4-day and 16-day outliers. **This is the opposite regime from UConn**: on ISU the physical axis is observed but almost regular; on UConn the physical axis is irregular but only inferable. Neither dataset contains a stretch where a *recorded* physical axis is *substantially irregular*.

---

## 4. Interval-censored EOL

### 4.1 The rule I would use

For each cell, on a declared physical axis `x`, let `soh_i` be the SOH at observation `i`:

```
j = min{ i : soh_i < 0.80 }                     # first observation below threshold
if j does not exist      -> right-censored at x_last
elif j == 0              -> left-censored (no upper bracket) -> EXCLUDE
elif soh_j == 0.80       -> exact hit
else                     -> interval:  L = x_{j-1},  U = x_j,  T_EOL ∈ (L, U]
```

`L` and `U` are **label-side only**; neither may enter a feature. Cells whose EOL falls inside the training window must be handled by the censoring likelihood, not dropped.

### 4.2 UConn (threshold `soh < 80`, axis = `cumsum(num_cycles)`)

| status | cells |
|---|---|
| **interval** | **64 / 64** |
| right-censored | **0** |
| exact hit | 0 |
| left-censored / below-at-first | 0 |

Bracket width: median **131** cycles, IQR [101, 149], min 75, max 176 — i.e. **2.9% of U**. `L` median 3,827; `U` median 3,943. `soh_last` ranges 72.34–79.18, so **every** cell crosses.

**⚠ Three defects that a frozen contract must resolve:**

1. **Systematic gap at RPT index 42.** `num_cycles` is NaN for exactly **32 of 64 cells**, all at `rpt == 42` — *not* a trailing segment (only 3 of the 32 have it as their last row; positions-from-end range 1–34). Since `cumsum` propagates NaN, **the raw cumulative axis is undefined past RPT 42 for half the fleet**, and 31 of those 32 cells have their EOL after RPT 42.
2. **The imputation choice moves EOL.** Forward-filling the gap vs dropping the row shifts absolute EOL by **median 91 cycles (2.35% of U), range 68–137**. Bracket *width* is usually invariant, but for **2 cells (39, 41) the 80% crossing lands exactly on RPT 42**, so the interval itself changes: dropping the row moves EOL to RPT 43 (width ≈ 98–101 cycles), while treating the segment as 0 collapses `L = U` into a **spurious exact hit**.
3. **The repo's own artefacts already disagree.** `.research/results/v2_main.py:73-75` forward-fills (`if not np.isfinite(v): v = last`); `protocol/uconn_eol_intervals.csv` is consistent with *dropping* the row (no zero-width intervals; cell 41 EOL at RPT 43, width 101). Any downstream EOL-dependent number inherits this ~2.4% discrepancy. **This must be frozen to one rule before any modelling.**

*(Correction to `DATA_CONTRACT.md` §2: the gap is at RPT index 42, mid-series — not "末段缺失" (trailing-segment) — and it does affect the EOL crossing for the affected cells.)*

### 4.3 ISU-ILCC (threshold `soh < 0.80`, axis = calendar days from `start_stop_time.start`)

| status | C/5 discharge | C/2 discharge |
|---|---|---|
| **interval** | **211** | **219** |
| **right-censored** | **40** | **32** |
| exact hit | 0 | 0 |
| left-censored | 0 | 0 |

Counts are **invariant** to normalising by `capacity@RPT0` vs `max(capacity)` (identical in every cell — the first RPT is always the maximum). Bracket width in days: median **8.0**, p10 8.0, p90 9.6, max 13.4. Median EOL day ≈ 94.1.

**The 40 right-censored cells are genuine, not an artefact** — verified by inspecting their traces: normal `cap0` (mean 0.2844 vs 0.2833 for interval cells), strictly monotone slow fade (`ratio_min` ≈ 0.92), EOL simply beyond the record. They are **structurally clustered**: all 40 sit in conditions **20–29** (all 4 cells of each), each with **exactly 5 RPTs** and a campaign span of **exactly 25 days**. So 10 of 63 conditions contain **no EOL event at all**.

> Consequence: ISU gives a genuine right-censoring test bed, but it is **not exchangeable** with the event-bearing conditions — the censored block is 10 whole conditions, so any leave-one-condition-out split puts either 0% or 100% censoring in the holdout. Censoring cannot be evaluated as a *random* mechanism here.

---

## 5. Ah-throughput per cell

**UConn — DERIVED ONLY (approximation).** Σ over RPT intervals of `q_dchg` × segment cycles:

| stat | min | median | max |
|---|---|---|---|
| Ah | 2,837.8 | **4,417.0** | 9,273.8 |

This substitutes the RPT-measured discharge capacity for the true per-cycle throughput in the intervening cycles. It is **not** charge throughput. True per-cycle Ah requires the raw cycling files (item 7/8 in §1, **MISSING**).

**ISU — MISSING.** The number of cycles between consecutive RPTs is not recorded, so no throughput integral can be formed. What exists is the *measured capacity at each RPT*, which is the numerator of SOH, not exposure.

---

## 6. Cross-condition transfer units

**ISU-ILCC — confirmed from the data, exact match.**
- 251 cells ↔ 251 rows of `Valid_cells.csv` (set difference empty both ways).
- **63 conditions**, ids `1..64` with **15 absent** — exactly the id set of `.research/results/isu_conditions.csv` (set equality `True`, no missing, no extra).
- Per-condition cells: **62 conditions × 4 cells + 1 condition × 3 cells = 251**. The 3-cell condition is **61**.
- Mapping is carried by the filename itself: `G<cond>C<n>.json`; `group` in the factor table matches the `G` index 1:1.

**UConn — confirmed from the data.**
- **64 cells** (`cell_id` 2..65), **11 conditions** (`group_id` 1..11).
- Cell→condition is a **partition**: 0 cells appear in more than one group.
- Per-condition cells: **G1–G10 = 6 each, G11 = 4** → 64.
- **The factor values (C-rate, DoD) per group are MISSING locally** — only the integer `group_id` survives. Unlike ISU, there is no `uconn_conditions.csv` anywhere in the repo. Any claim about UConn condition *factors* is unsupported by local files.

---

## 7. Blunt verdict

# PARTIALLY

**What is identifiable:**

| Component of question A | Status | Evidence |
|---|---|---|
| Interval-censored EOL `[L,U]` at 80% SOH | ✅ **YES** | 64/64 UConn intervals; 211–219/251 ISU intervals; 0 exact hits |
| Right-censoring | ✅ **YES, ISU only** | 40 cells (C/5) / 32 (C/2), conditions 20–29 |
| Right-censoring on UConn | ❌ **NO** | 0 of 64 cells are censored — the mechanism cannot be *tested* there |
| Correct only when a measurement arrives | ✅ **YES** | RPT arrival is discrete and known in both |
| Advance by **calendar time** | ✅ **ISU only** | `start_stop_time`, 251/251 cells |
| Advance by **cycle count** | ⚠️ **UConn only, derived + broken** | `cumsum(num_cycles)`; undefined past RPT 42 for 32/64 cells |
| Advance by **Ah-throughput** | ❌ **NO** | derived approximation on UConn; absent on ISU |
| **Exposure observed between RPTs** | ❌ **NO — this is the blocker** | no sub-RPT current/throughput anywhere |

**Why PARTIALLY and not YES.** The proposal's distinguishing claim is that advancing by *real operating exposure* beats one fixed step per RPT. That comparison needs exposure **between** RPTs. Locally, exposure is only ever known **at** RPT boundaries — as a segment length (UConn) or a timestamp (ISU). So the "continuous exposure" model and the "per-RPT step" baseline are both constrained to the same RPT grid; what separates them is only how the *interval* between two RPTs is parameterised, not any observed intra-interval dynamics. The mechanism can be *implemented* and *compared*, but its central premise — that real exposure resolution matters — **cannot be demonstrated**, only assumed.

**The single missing quantity:** the raw cycling records between RPTs — per-cycle current/charge throughput and its timestamps.
- UConn: `cycling_part1.zip` (6.55 GB) + `cycling_part2.zip` (7.05 GB), **not local**; the local `README_uconn.txt` is a Cloudflare challenge page, i.e. the download was bot-blocked. Obtainable from the UConn REIL digitalcommons release with a non-blocked client.
- ISU: `Cycling_json.zip` (~10.2 GB per `DATA_CONTRACT.md` §9), **not local**.

**Also required before any EOL-dependent claim is trustworthy:** freeze one rule for the RPT-42 gap (§4.2) — the repo currently ships two incompatible ones, worth ~2.4% of EOL.

**Recommendation.** Do **not** frame the contribution as "exposure-advancing beats per-RPT stepping" on these data — it is not identifiable and a reviewer can defeat it with the argument above. What *is* defensible: **calendar-time-advancing online prediction with interval-censored EOL and right-censoring on ISU** (251 cells, 63 conditions, 40 genuinely censored, real timestamps), with UConn as a secondary cycle-axis replication carrying the explicit caveats in §4.2. Either download the cycling files first, or drop the Ah-throughput/exposure-resolution claim entirely.

---

## 8. Reproducibility

All numbers produced by these scripts (run from `E:\桌面\rul\rul_v4_20261107`):

| Script | Produces |
|---|---|
| `_probe/uconn_a_inventory.py` | field inventory, cells/groups/RPTs per cell → `uconn_summary.json` |
| `_probe/uconn_b_grain.py` | row-grain and NaN diagnosis |
| `_probe/uconn_c_cadence.py` | first cadence pass (superseded — see note) |
| `_probe/uconn_d_monotone.py` | proof `num_cycles` is per-interval, not cumulative |
| `_probe/consolidated.py` | corrected cumulative-axis cadence, EOL, Ah; ISU normalisation robustness |
| `_probe/final_details.py` | segment stats, NaN location, per-condition aggregation |
| `_probe/rpt42_impact.py` | RPT-42 gap impact → `uconn_cycle_axis_status.csv` |
| `_probe/isu_a_proto.py`, `isu_b_extract.py` | ISU extraction over 251 JSONs → `isu_cells.csv`, `isu_eol.csv`, `isu_summary.json` |
| `_probe/isu_censor_check.py` | verification that the 40 censored cells are genuine |
| `_probe/voltage_and_cond.py` | voltage-matrix semantics; condition-set equality |
| `_probe/reconcile.py`, `diag_137.py`, `confirm_fill.py`, `degenerate.py` | reconciliation with `uconn_eol_intervals.csv` / `v2_main.py`; gap-imputation sensitivity |

*Note on `uconn_c_cadence.py`: it applied `np.diff` to a per-interval quantity and reported a spurious negative-gap distribution. It is retained as the record of how the `num_cycles` semantics were discovered; its cadence numbers are superseded by `consolidated.py`.*

**Cross-check against existing repo artefacts.** `protocol/uconn_data_contract.json` reports `n_gaps 2727, median 98, q25 84, q75 119, min 12, max 197, cv 0.2292, n_rows_dedup 2855, 64 cells, 11 conditions` — reproduces exactly here (2,759 total − 32 NaN = 2,727). `uconn_eol_intervals.csv` matches on bracket width (median 131, IQR [101,149], 2.9% of U) but differs in absolute `L`/`U` for the 32 gapped cells per §4.2 item 3.
