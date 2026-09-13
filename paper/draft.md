# Reliability-Targeted Bedtime Planning with Explicit Infeasibility

*Draft — Methods, Results, Limitations. Markdown for now; converts to IEEEtran
at submission. Every number traces to a table in `docs/` and regenerates via
`python evaluation/run_study.py`.*

---

## 3. Methods

### 3.1 Problem formulation

Sleep models are forecasters: given behaviour, they return a predicted outcome.
A person with a fixed obligation the next morning has the inverse question,
which is a constraint rather than a prediction:

> *I must be up at 05:40 and I cannot miss it. What do I have to do tonight?*

Let **x** ∈ ℝ^d be a night's feature vector and *f*(**x**) → [0,1] a trained
classifier estimating the probability of waking on schedule. A forward system
reports *f*(**x**). We instead solve, for a required reliability *τ*:

> find the **latest** bedtime *b* such that *f*(**x** with bedtime *b*) ≥ *τ*,
> and if none exists, report that fact together with the achievable ceiling and
> its cause.

*Latest*, not earliest, is deliberate: among bedtimes satisfying the constraint,
the latest imposes the least behavioural cost. A planner returning the safest
bedtime rather than the latest feasible one is needlessly punitive and will be
ignored.

### 3.2 Feature partition

The *d* inputs are partitioned into three classes, and only the first is
admissible in a same-night plan:

- **Controllable tonight** — bedtime, screen time before bed, caffeine, ambient
  noise, room temperature, stress, exercise.
- **Habit-level** — sleep-timing consistency, habitual snooze count, habitual
  alarm response latency, accumulated sleep debt. Real determinants of wake
  reliability, but not changeable before tonight.
- **Fixed** — age, chronotype, resting heart rate.

The partition is what makes a plan actionable. Section 4.5 shows it is also what
keeps the planner sound: removing it is the only ablation that produces promises
the world cannot keep.

### 3.3 Inverse planning

**Algorithm 1 — bedtime sweep.** The primary control is swept across its
admissible range [20:00, 02:00] at 15-minute resolution (25 candidates),
scored in one batched forward pass, and the latest candidate meeting *τ* is
returned.

```
Input:  features x, target τ
Output: latest feasible bedtime or ⊥, achievable ceiling, full curve

B ← [26.00, 25.75, …, 20.00]            # latest first, 0.25 h steps
S ← f_batch([x with bedtime b for b in B])
best ← max(S)
for (b, s) in zip(B, S):
    if s ≥ τ: return b, best, curve      # first hit is the latest
return ⊥, best, curve
```

Exhaustive scanning rather than gradient search is deliberate. A random forest's
response is a step function with no gradient to follow, the admissible range is
only 25 points wide, and the whole curve is worth returning for display. Section
4.3 confirms the sweep returns the true latest feasible bedtime in every
simulated scenario including non-monotone response curves, where a gradient
method would settle in a local optimum.

**Algorithm 2 — greedy coordinate ascent.** When bedtime alone is insufficient,
the remaining controllable inputs are searched one at a time.

```
Input:  features x, target τ, budget R
Output: modified features, achieved reliability, list of changes

current ← x ;  r ← f(current) ;  steps ← []
repeat R times:
    if r ≥ τ: break
    M ← [(name, clamp(v + dir·step·3, lo, hi)) for each controllable lever]
    M ← [m in M where m changes the current value]
    if M empty: break
    G ← f_batch([current with m applied for m in M])
    i ← argmax(G) ;  gain ← G[i] − r
    if gain ≤ 0.002: break
    merge M[i] into steps (fold repeats on one lever into one instruction)
    current ← current with M[i] ;  r ← G[i]
return current, f(current), steps
```

Two details matter for reimplementation. **Re-scoring after each committed
move** is what prevents double-counting redundant levers: two levers acting
through one physiological channel do not contribute additively, and scoring them
independently overstates the plan. **Stopping as soon as *τ* is met** yields the
fewest changes that suffice rather than every change available; Section 4.3
confirms the resulting set is exactly minimal.

*R* = 8. It was 3 until simulation showed the search exhausting its budget
rather than its options — a traced case reached 0.66 against a 0.70 target and
needed one further round. Raising it cut false refusals from 10 to 3 of 42 and
never once produced an unkeepable promise.

### 3.4 Parameters

Everything an implementation needs. Each lever is defined by a direction (the
sign of the change expected to help), an admissible range, and a step size; one
round of Algorithm 2 moves the chosen lever by three steps.

| Lever | Dir. | Range | Step |
| --- | --- | --- | --- |
| bedtime_hour | − | 20.0 – 26.0 h | 0.25 |
| screen_minutes_before_bed | − | 0 – 180 min | 15 |
| caffeine_mg | − | 0 – 400 mg | 40 |
| ambient_noise_db | − | 20 – 70 dB | 5 |
| room_temp_c | **set-point** | 14 – 30 °C | → 20.5 |
| stress_level | − | 0 – 100 | 10 |
| exercise_minutes | + | 0 – 120 min | 20 |

Room temperature is the one lever with no monotone direction: its candidate is
the set-point 20.5 °C rather than an extreme, since both hotter and colder are
worse.

Habit features and the healthy reference each is counterfactually set to when
attributing an infeasibility:

| Habit feature | Reference |
| --- | --- |
| sleep_consistency | 85 / 100 |
| snooze_count | 0 |
| alarm_response_ms | 5,000 ms |
| sleep_debt_hours | 0 |

| Threshold | Value | Applies to |
| --- | --- | --- |
| Coordinate-ascent budget *R* | 8 rounds | Algorithm 2 |
| Minimum gain to commit a move | 0.002 | Algorithm 2 |
| Minimum gain to report a single lever | 0.001 | lever ranking |
| Minimum gain to report a habit cause | 0.01 | attribution |
| Bedtime resolution | 0.25 h over 20:00–02:00 | Algorithm 1 |

Derived features, which two distinct trailing windows govern — a point easily
missed:

- **Habit features, 7-night window.** `sleep_consistency` is the standard
  deviation of night-anchored bedtime over the preceding 7 nights, mapped
  linearly onto 0–100 with an SD of 3 h scoring zero. `sleep_debt_hours` is the
  cumulative shortfall against an assumed 8 h need over the same window, clipped
  to [−2, 4].
- **Wake-proxy baseline, 28-night window**, minimum 3 observations in the
  (participant, day-type) bucket.

`chronotype_code` bins each participant's median night-anchored bedtime: lark
below 23:00, intermediate to 24:30, owl beyond. Night-anchored hour maps clock
time onto a 20–26 axis so a night spanning midnight does not wrap, splitting at
12:00.

### 3.5 Infeasibility and attribution

If neither algorithm reaches *τ*, the planner does not return a bedtime. It
returns the achievable ceiling and attributes the shortfall to the **habit**
partition by counterfactual substitution: each habit feature is independently
set to a healthy reference value and re-scored, and those yielding a gain above
0.01 are reported, ranked, with a weeks-not-tonight horizon.

The output is therefore of the form *"95% is not reachable tonight; the best
available combination reaches 60%. What limits you is habit rather than tonight:
responding to your alarm on the first attempt is worth 30 points on its own. Set
a backup alarm on a second device."*

### 3.6 Datasets

Two public wearable cohorts, both downloadable without application.

| | LifeSnaps | PMData |
| --- | --- | --- |
| Participants with sleep data | 69 | 16 |
| Person-nights | 3,551 | 1,881 |
| Duration | ~4 months | 5 months |
| Device | Fitbit Sense | Fitbit Versa 2 |
| Source | Zenodo 7229547 (CC BY 4.0) | datasets.simula.no |

Sleep timing in LifeSnaps exists only in a 9.7 GB MongoDB dump; the released
CSVs contain none. Nights carrying several sleep episodes are folded to the
longest, giving one row per participant-night.

**Feature availability is the binding constraint.** Of the 15 model inputs, 3–4
are directly available, 5 derivable under stated assumptions, and 6–7 absent
entirely. Critically, **no public wearable dataset records alarm interaction**,
so habitual snooze count and alarm response latency — half the habit partition —
cannot be populated. Of the seven controllable levers, only bedtime, stress and
exercise exist.

### 3.7 Target construction

Neither dataset contains an alarm, so the outcome must be constructed. We label
a night successful when the participant woke no more than *N* minutes after
their habitual wake time for that kind of day, with *N* = 30.

Three choices, each defensible and each reported with a sensitivity analysis:

1. **One-sided.** Oversleeping is waking *late*. A symmetric window scores
   someone who woke forty minutes early as a failure, which is a different
   construct.
2. **Day-type aware.** People wake later at weekends by choice. Against a pooled
   baseline the label degenerates into a weekday detector.
3. **Baseline from prior nights only**, over a 28-night window with at least
   three observations — distinct from the 7-night window governing the habit
   features of Section 3.4 — computed within (participant, day-type) with **no
   fallback to pooled history**. Borrowing pooled history for a thin weekend
   bucket judges a 10:00 lie-in against a 07:00 weekday habit and scores three
   hours of oversleeping — reintroducing exactly the contamination the bucketing
   removes. This costs ~11% of nights and is the cheaper error.

**We call this wake-time regularity, not wake success.** Section 5 explains why.

### 3.8 Models and protocol

Random forests (200 trees, depth 12, minimum leaf 8, seed 42) for both the
duration regressor and the regularity classifier, identical to the
configuration used on the synthetic panel so that differences isolate the data.

**Splits are by participant.** A participant contributes ~50 nights; splitting
rows at random lets a model identify the person rather than learn anything
about nights. All reported figures are means over 8 grouped splits.

**Outcome columns are never predictors.** Sleep duration is approximately
time-in-bed × efficiency, so time-in-bed, efficiency and wake time are excluded
by an assertion rather than by convention. For the regularity classifier, sleep
duration is additionally excluded: combined with bedtime it reconstructs wake
time and hence the label.

**Habit features use strictly prior nights.** Including tonight's own value in
its trailing window leaks the target into the predictors.

**Uncertainty is clustered.** All intervals come from resampling participants,
never rows. Mixed-effects models (random intercept; GEE with exchangeable
working correlation for the binary outcome) account for repeated nights.

---

## 4. Results

### 4.1 Synthetic data substantially overstates predictability

Retrained on real cohorts with identical model, features and protocol:

| Cohort | MAE (h) | R² | vs. mean baseline |
| --- | --- | --- | --- |
| Synthetic panel | 0.403 | **+0.702** | +45.6% |
| LifeSnaps | 1.016 | **+0.186** (95% CI 0.075–0.297) | +15.0% |
| PMData | 1.072 | **−0.090** | +3% |

R² falls by roughly a factor of four. On the 16-participant replication cohort
the model is worse than predicting the mean. Across splits R² ranges −0.077 to
+0.395, so no single-split figure is reportable; the interval nonetheless
excludes zero, so the model does beat the mean on LifeSnaps.

For wake-time regularity the gap is smaller but present: AUC 0.761 synthetic
against 0.660 (95% CI 0.610–0.710) on LifeSnaps and 0.675 on PMData. The
interval excludes chance. Unweighted accuracy exceeds the majority-class
baseline by only 1.0 point.

An oracle predicting each held-out participant's own mean duration beats the
model in 5 of 8 splits. Consistent with this, the unconditional intraclass
correlation is **0.336** for sleep duration — a third of the variance is a
stable person-level trait — but only **0.060** for wake regularity, which is
almost entirely night-to-night.

Two predictors survive in both models under different estimators: later bedtime
(−0.295 SD of sleep duration, CI −0.354 to −0.236; OR 0.677, CI 0.496–0.925 for
regularity) and resting heart rate. **No habit feature reaches significance in
either model.**

### 4.2 The stated reliability is calibrated

Over 3,180 held-out person-nights from 46 participants:

| Predicted | n | Observed |
| --- | --- | --- |
| 0.66 | 436 | 0.649 |
| 0.76 | 1,115 | 0.765 |
| 0.84 | 1,178 | 0.832 |
| 0.93 | 127 | 0.929 |

**ECE 0.0148 (95% CI 0.0139–0.0571).** The interval is wide and right-skewed;
the point estimate alone overstates the precision.

Calibration alone is insufficient, and we report Brier alongside for that
reason: a predictor that always returns the base rate achieves a *perfect* ECE
of 0.0000 while carrying no information. Brier separates them — 0.1727
(CI 0.1490–0.2003) against 0.1898 for the base-rate predictor. The honest
description is **well calibrated, weakly informative**, which is the combination
honest refusal requires: the model does not know much, but it knows how much it
knows.

### 4.3 The algorithm is sound but incomplete

The recommendation cannot be validated observationally — it is conditional on a
bedtime no participant adopted on our instruction. We therefore validate the
*algorithm* against exhaustive search over seven analytic ground-truth models ×
six targets, including non-monotone response curves, redundant levers,
interacting levers and hard ceilings.

| Property | Result |
| --- | --- |
| Bedtime sweep returns the latest feasible bedtime | **42/42** |
| Promises only reachable targets (soundness) | **0 violations** |
| Lever set exactly minimal when successful | **100%** |
| Refuses only unreachable targets (completeness) | 92.9% (3/42 false refusals) |

The planner never over-promises at any iteration budget tested. Its failure mode
is conservatism — refusing some achievable targets — which for a system whose
contribution is honest refusal is the correct direction to err. Behaviour at the
achievable ceiling is exact: a target equal to the ceiling is promised, one
0.001 above is refused.

### 4.4 Refusal beats always-promising

Over-promise rate — promising a target the held-out participant's own achieved
rate could not deliver:

| Target | Always promise | 90-min cycle rule | Inverse planner |
| --- | --- | --- | --- |
| 0.90 | 0.867 | 0.867 | **0.068** |
| 0.95 | 1.000 | 1.000 | **0.040** |

At a 0.95 target the model-free planners promise every night and are wrong every
time. A cycle calculator has no mechanism for knowing it cannot deliver, so it
never says so.

### 4.5 Every component contributes differently

| Ablation | Verdict correct | False refusals | Broken promises | Bedtime optimal |
| --- | --- | --- | --- | --- |
| Full planner | 0.929 | 3 | **0** | 1.00 |
| No bedtime sweep | 0.881 | 5 | 0 | **0.69** |
| No coordinate ascent | **0.762** | **10** | 0 | 1.00 |
| No habit partition | 0.857 | 3 | **3** | 1.00 |
| No attribution | 0.929 | 3 | 0 | 1.00 |

The sweep buys optimality rather than feasibility: without it, minimality falls
from 1.00 to 0.56 and the planner recommends earlier bedtimes than necessary.
Coordinate ascent buys completeness. **The habit partition is the only component
whose removal breaks soundness** — without it the planner offers plans requiring
changes nobody can make before bed. The attribution changes no verdict at all;
what it changes is whether the user is told why (2 habit causes named versus 0).

### 4.6 Observational evidence is directionally positive but inconclusive

Nights where a participant coincidentally slept near the recommended hour,
compared within participant against their other nights:

| Tolerance | Matched | Participants usable | Difference | 95% CI |
| --- | --- | --- | --- | --- |
| ±15 min | 43 | 9 | +0.085 | −0.055 – +0.225 |
| ±30 min | 86 | 9 | +0.045 | −0.128 – +0.217 |
| ±45 min | 137 | 11 | +0.093 | −0.043 – +0.230 |
| ±60 min | 168 | 11 | +0.071 | −0.056 – +0.199 |

The direction is positive at every tolerance and no interval excludes zero. With
9–11 participants contributing a paired difference this is underpowered by
construction, and we report it as suggestive only. Detecting an effect of the
observed magnitude would require approximately **50–75 participants**.

---

## 5. Limitations

We state these before a reader has to find them.

**The target is constructed, not measured.** Neither dataset contains an alarm,
an intended wake time, or any record of whether a participant had somewhere to
be. Our label measures deviation from personal schedule and nothing more.

**The target showed no association with wellbeing.** Tested against PMData's
daily self-reported sleep quality (*d* = −0.093), readiness (−0.026) and
LifeSnaps' tiredness indicator (−0.041), all effects were negligible and two
pointed the wrong way. Restricting to weekdays did not help. The plain reading
is that waking later than habit is usually a lie-in rather than a failure. **We
therefore renamed the target from wake success to wake-time regularity**, and
the paper claims nothing about how anyone felt.

**The models are weak in absolute terms.** R² 0.186 and AUC 0.660 explain a
minority of variance. We argue this motivates rather than undermines the
contribution — a planner built on a signal this thin *should* decline to
promise — but a reader who wants strong point predictions will not find them.

**The system was developed against synthetic data, and that development was
optimistic.** The planner and its thresholds were built and tuned on a
physiologically-structured simulated panel that we now know overstates
predictability by roughly a factor of four in R² and 0.10 in AUC. We report the
gap as a finding in Section 4.1 because training sleep models on simulated
panels is common practice, but it is also a limitation of this work
specifically: design decisions made against the simulation may be tuned to a
world more predictable than the real one. The parameters in Section 3.4 were
re-examined against real data and simulation ground truth, and one — the
coordinate-ascent budget — was changed as a result; we cannot rule out that
others carry the same bias.

**Half the habit partition is unpopulated.** Habitual snooze count and alarm
response latency are absent from every public wearable dataset, because no
consumer device instruments the alarm. The infeasibility attribution therefore
runs on two of its four intended inputs.

**Four of seven controllable levers are absent.** Only bedtime, stress and
exercise exist in these cohorts. The coordinate-ascent results in Section 4.5
are measured in simulation with the full lever set and are therefore an upper
bound on what that component contributes in deployment today.

**The simulation scenarios are ours.** Soundness holds across seven ground-truth
models we designed, including cases built to defeat greedy search. They are
principled rather than convenient, but they are not a proof, and a different
family of response surfaces might expose different behaviour.

**No deployment study.** The end-to-end claim — that following the advice
improves waking — is not established and cannot be from retrospective data. Our
matched-subset analysis is directionally positive and underpowered. Establishing
it requires giving people the recommendation and measuring what follows.

**Cohort generalisability.** 85 participants across two cohorts, neither
demographically representative. Neither dataset yields a numeric age (LifeSnaps
de-identifies to `<30`/`>=30`; PMData ships no demographics), so no age-adjusted
analysis is possible.

**Sleep staging is consumer-grade.** Fitbit's sleep classification is not
polysomnography, and its error is not independent of the behaviours we model.

---

## Appendix: reproducibility

All results regenerate from committed code:

```
pip install -r requirements.txt -r requirements-research.txt
python evaluation/run_study.py --out results/ --figures figures/
```

Datasets are not redistributed; both are obtainable without application from the
sources in Section 3.6. 311 tests cover the pipeline, including assertions that
participant splits are disjoint, that outcome columns cannot become predictors,
and that habit features use strictly prior nights.
