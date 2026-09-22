# Demo script — 3 minutes

The demo goes at the top of the README. Most people who look at this repo will
watch it and never clone anything, so it is the highest-leverage 3 minutes of
work in the whole project.

**Record with:** Claude Desktop with the server registered, screen recording on,
terminal visible for the last segment. No voiceover needed — captions are fine
and easier to redo.

**Before recording:** run every question once so the cache is warm. Waiting for
API calls on camera is dead air, and you will re-record because of it.

---

## Segment 1 — It works (0:00–0:30)

**Type exactly:**

> What was NVIDIA's total revenue in fiscal year 2024?

**What good looks like:** one `resolve_company` call, one
`get_financial_concept` call, then an answer that gives the figure **and names
the tag and the fiscal period**.

**Caption:** "Every answer names its source — which XBRL tag, which filing,
which period."

Do not linger. This segment only exists to establish that the thing works.

---

## Segment 2 — It refuses to guess (0:30–1:00)

**Type exactly:**

> What was Apple's revenue last year?

**What good looks like:** `resolve_company` returns more than one plausible
match and the agent **asks which one you mean** rather than picking.

> If your fuzzy matcher resolves this cleanly, use a genuinely ambiguous query
> instead. Find one by running `resolve_company` against a few common words
> before you record. Do not fake ambiguity — pick a query that is really
> ambiguous.

**Caption:** "It refuses when the top two matches are too close. A confident
wrong CIK is worse than a question."

This is the segment an FDE interviewer will notice.

---

## Segment 3 — The fiscal-year trap (1:00–1:45)

**The centrepiece. Give it the most time.**

**Type exactly:**

> Compare NVIDIA's and Apple's revenue for fiscal year 2024.

**What good looks like:** the numbers, plus a **warning** that the two fiscal
years cover different periods — NVIDIA's FY2024 ended January 2024, Apple's
fiscal year ends in September.

**Caption:** "NVIDIA's FY2024 ended in January. Apple's ends in September. Naive
comparison compares different twelve-month windows — and the chart looks fine."

Pause on the warning for a full two seconds. This is the single best evidence in
the project that you thought about the data rather than just wiring up an API.

---

## Segment 4 — It says no (1:45–2:15)

**Type exactly:**

> What is NVIDIA's current stock price?

**What good looks like:** a clear refusal explaining that EDGAR holds filing
data, not market data — and **no invented number**.

**Caption:** "4 of the 25 evaluation questions exist only to check that it
refuses. A system that answers everything can't be trusted on anything."

---

## Segment 5 — The evidence (2:15–3:00)

**Switch to the terminal. Run:**

```bash
python -m pytest -q
```

Let the test count land on screen.

```bash
python evals/run_eval.py --provider groq --runs 3
```

Show it running. Cut to the generated `evals/results/RESULTS.md` and scroll the
table slowly.

**Caption:** "25 questions, 3 runs each. Accuracy, refusal correctness, citation
rate, variance. Including the failures."

**Final frame:** hold on the results table for three seconds. End.

---

## Checklist before you publish

- [ ] Under 3:30. Ruthlessly.
- [ ] Text readable at 720p — zoom the terminal font before recording
- [ ] No API keys, tokens, or personal paths visible anywhere on screen
- [ ] The fiscal-year warning is legible and on screen long enough to read
- [ ] Real numbers throughout — never stage output you did not actually get
- [ ] Uploaded and linked at the very top of the README, above everything

## If a segment does not work

Do not fake it. Fix the tool, or cut the segment and record four instead of
five. A demo showing four real behaviours beats one showing five where the
viewer can tell one was staged — and in an interview, "I cut that segment
because the disambiguation wasn't reliable enough yet" is a *better* answer than
a smooth demo you cannot defend.
