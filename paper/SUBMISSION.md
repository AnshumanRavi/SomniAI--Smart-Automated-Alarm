# Submission package

Target: **IEEE ICHI 2027, Early Bird track.**

## The deadline, and what is actually confirmed

| Fact | Source | Confidence |
| --- | --- | --- |
| Early Bird deadline **21 Sep 2026, 23:59 AoE** | search results citing the ICHI announcement | **unconfirmed** |
| Submissions via OpenReview | same | **unconfirmed** |
| Organisers: Shi, Wu (Temple), Bian (Indiana) | same | likely |
| ICHI 2027 website | not yet live as of 13 Sep 2026 | confirmed absent |

**Everything below assumes the 21 Sep date is real, and it has not been verified
against a primary source.** The ICHI 2027 site is not up, and the
[@ieeeichi](https://x.com/ieeeichi) account could not be read programmatically.
**Confirm this by hand before doing anything else** — it is a two-minute check
that decides whether the next week is urgent or not.

The rules below are taken from the **ICHI 2026** cycle, which is the closest
model available. They must be re-checked against ICHI 2027's own CFP when it
publishes:

- Long papers only in the Early Bird track.
- **10 pages including references**; minimum 7 pages of main content excluding
  references.
- IEEE Proceedings format.
- **Double-blind** in the Early Bird track. Note the ICHI 2026 main CFP page said
  *single*-blind — the two pages disagree, so this specifically needs checking.
- **No supplementary materials.** Everything needed for review must be inside the
  page limit.
- Rejected Early Bird papers **may revise and resubmit to the regular track**.
- Accepted papers may be recommended to the *Journal of Healthcare Informatics
  Research*.

## Why submitting to Early Bird is close to free

The resubmission rule is the whole argument. If it is accepted, you are done six
months early. If it is rejected, you get expert reviews on a paper that has
never been read by a stranger, and you resubmit to the regular track having
addressed them. The only real cost is the work of formatting, which has to
happen anyway.

The one risk worth naming: a rejection is a rejection, and if the regular-track
reviewers overlap with the Early Bird reviewers, a weak first impression can
carry. That is an argument for submitting a clean paper, not for not submitting.

## Files

| File | What it is |
| --- | --- |
| `ichi2027.tex` | The submission. IEEEtran, `conference` class, double-blind. |
| `figures/*.pdf` | Vector figures, copied from `/figures` (regenerable). |
| `draft.md` | The Markdown source of record. Edit both, or edit here and port. |
| `references.md` | Reference audit — every citation checked against the publisher record. |

## Build

There is **no LaTeX toolchain on this machine**, so `ichi2027.tex` has been
checked structurally but **never compiled**. It passes: balanced environments and
braces, no dangling `\ref`, no undefined `\cite`, every `\includegraphics`
target present. That is not the same as compiling.

Easiest path: upload `paper/` to Overleaf and compile there.

```
pdflatex ichi2027 && pdflatex ichi2027
```

**The page count is unverified and is the main open risk.** Estimate: ~4,240
words of body text, 8 tables, 4 figures, 2 algorithms — likely 9–10 pages, i.e.
right at the limit. If it overruns, trim in this order:

1. Table~\ref{tab:calib} (calibration bins) — the ECE figure in the text carries
   the result; the four-row table is a nicety.
2. The parameter table's threshold block — move to the artifact, referenced.
3. Fig. 5 (ablation) — Table VII already reports every number in it.
4. Section III-D's derived-feature paragraph — compress to two sentences.

Do **not** trim the limitations section to make space. It is load-bearing for
this paper's argument, and cutting it is how the paper stops being honest.

## Before submitting

- [ ] **Confirm the deadline and the blind policy** against ICHI 2027's own CFP.
- [ ] **Compile it.** Check page count, check no figure lands on a page alone,
      check the tables are not overfull.
- [ ] **Authorship.** Settle the author list and order with the co-author before
      submission, not after. He wrote the original system.
- [ ] **Anonymise the artifact.** The repo is public under a real name, and
      `REPRODUCE.md` names it. Under double-blind, use an anonymising proxy
      (e.g. `anonymous.4open.science`) and put that URL in the footnote in
      Section "Reproducibility", replacing the placeholder.
- [ ] **Check the AI-disclosure policy.** IEEE requires disclosure of generative
      AI use in the preparation of submissions. Find ICHI 2027's wording and
      comply with it exactly.
- [ ] **Scrub the PDF metadata** — LaTeX embeds the author name from the system
      unless told otherwise. Under double-blind this deanonymises you.

## arXiv: post it, but afterwards

**Do not post the preprint before the submission goes in.** Under a double-blind
policy a preprint carrying your names, posted days before the deadline, is
exactly the thing anonymity rules exist to prevent. Most venues permit arXiv
preprints, but the safe sequencing costs nothing:

1. Submit to ICHI.
2. Then post to arXiv, with the real author block restored.

Category: `cs.LG` primary, cross-list `cs.HC` and `eess.SP`. Licence: CC BY 4.0,
which is compatible with LifeSnaps' licence and keeps the preprint reusable.

The preprint version should differ from the submission in exactly two ways: real
authors, and the real repository URL instead of the anonymised proxy.

## Cover letter

A conference submission usually has no cover-letter field — this is for the
optional *comments to the chairs* box, and for the JHIR journal path if the
paper is recommended there. Trimmed to fit a text box:

> We submit *Reliability-Targeted Bedtime Planning with Explicit Infeasibility*
> to the ICHI 2027 Early Bird track.
>
> The paper inverts a trained sleep model against a required reliability rather
> than reading it forward, and treats infeasibility — the case where no
> admissible plan reaches the target — as a first-class output with
> counterfactual attribution rather than as a failed search. The nearest prior
> work is algorithmic recourse; we differ in that the constraint is a required
> probability rather than a decision boundary, and in that our feature partition
> is temporal rather than binary, separating what a person can change tonight
> from what is changeable only over weeks.
>
> Two aspects of the evaluation warrant flagging to reviewers in advance, since
> both are unusual and both are deliberate.
>
> First, we report that a physiologically-structured synthetic panel overstates
> predictability on this task by roughly a factor of four in R². We developed
> our own system against such a panel, so this is a finding about our own prior
> work as much as about the practice generally, and we report it because
> training sleep models on simulated data is common.
>
> Second, we report a baseline that outperforms our method. Forward prediction,
> using the same model without search, achieves a lower over-promise rate at
> every target. We include it because omitting it would be selective reporting;
> we explain in Section IV-D why the two are making different kinds of claim and
> why observational data can check one but not the other.
>
> The central limitation is stated plainly throughout: there is no deployment
> study, and the end-to-end claim that following the advice improves waking is
> not established. All results regenerate from the artifact, which is available
> at an anonymised URL.
