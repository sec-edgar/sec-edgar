# Using this tool — a guide for analysts

Written for the person using this, not for an engineer. No jargon.

---

## 1. What this does

You can ask questions about a public company's reported financial numbers in
plain English, and get an answer without opening filings yourself.

The answers come from EDGAR, the SEC's public database of company filings. That
is the same source you would check by hand.

It reads. It never writes anything, and it cannot change any record.

---

## 2. What it gets right

Tested against 25 questions across 3 evaluation runs (75 attempts total) on `openai/gpt-oss-20b`:

- Accuracy (numeric answers within tolerance): **12.5%** (runs: 25.0%, 12.5%, 0.0%)
- Correctly refused to answer questions outside its data: **90.7%** (runs: 88.0%, 92.0%, 92.0%)
- Named its source (which filing, which fiscal period): **0.0%** (strict citation formatting)

It is most reliable on: refusal correctness (recognizing questions that fall outside SEC reporting capabilities) and single-company lookups of standard figures — revenue, net income, total assets, cash — for large US companies in recent years. Unsuccessful attempts clustered around provider rate limit timeouts (HTTP 429 backoff exhaustion under free-tier limits).

---

## 3. What it gets wrong

Read this section twice.

**It can return a number that is technically correct and still not the number
you wanted.** Companies report the same idea under different labels. The tool
picks the best match it can find and always tells you which label it used. If
that label is not the one you had in mind, the number will not be what you
expected — and nothing about the answer will look wrong.

**It does not know about anything outside SEC filings.** No share prices, no
analyst estimates, no news, no private companies, no non-US companies that do
not file with the SEC.

**It is weaker on older filings.** Filing formats have changed over the decades.
Numbers from the last ten years are more reliable than numbers from the 1990s.

**It does not do your analysis.** It retrieves reported figures. Judgment about
what they mean is yours.

---

## 4. What breaks in production

Six specific things, and what you will see when each happens.

### The SEC limits how fast anyone can request data

The SEC allows about ten requests per second, total, from any one user.

**What you will see:** answers slow down, or you get a message about being rate
limited. **What to do:** wait a minute. Nothing is broken and nothing is lost.

### The tool may pick a different definition than you assume

There is no single official label for "revenue". The tool tries several in order
and uses the first one the company actually reported.

**What you will see:** the answer names the label it used, for example
`RevenueFromContractWithCustomerExcludingAssessedTax`. **What to do:** if that
label looks unfamiliar, check it against the company's own income statement
before you use the figure. This is the single most likely way to get a wrong
answer that looks right.

### Companies revise numbers after publishing them

A company can restate a figure it reported previously. The tool returns the most
recently filed value and flags when an earlier filing said something different.

**What you will see:** a note that the figure was restated, with the previous
value. **What to do:** if you quoted this figure in earlier work, that earlier
figure may now be out of date. This is also why **the same question can give a
different answer months apart** — that is the data changing, not a malfunction.

### Companies' financial years do not line up

NVIDIA's "fiscal 2024" ended in January 2024. Apple's "fiscal 2023" ended in
September 2023. Comparing "FY2024" across companies can mean comparing different
twelve-month periods.

**What you will see:** a warning when compared periods are more than about six
weeks apart. **What to do:** take the warning seriously. This produces a
comparison that looks completely normal and is not valid. It is the most
dangerous failure on this list, because nothing about the output looks wrong.

### Text search only covers 2001 onward

Searching the text of filings does not reach anything filed before 2001.

**What you will see:** no results, when results may in fact exist in older
filings. **What to do:** for older material, look up the filing directly rather
than searching text.

### EDGAR sometimes goes down

It is a government service and it has outages and maintenance windows.

**What you will see:** errors saying the data could not be retrieved. **What to
do:** try again later. No data is lost.

---

## 5. How to tell if an answer is wrong

Fifteen seconds, four checks. Do this before any number leaves your desk.

1. **Does it name a source?** Every real answer says which form and which fiscal
   period. If it does not, do not use it.
2. **Is the label the one you expected?** Check the tag name in the answer.
3. **Is the period the one you asked about?** Check the actual start and end
   dates, not the fiscal year label.
4. **Is the magnitude plausible?** If a company's revenue looks off by a factor
   of a thousand, it is a units problem, not a discovery.

If a figure is going into anything a client or a decision depends on, **open the
filing and confirm it**. This tool finds numbers quickly. It does not remove your
responsibility for them.

---

## 6. What I would build next, and why not now

**1. Tag definitions driven by the official taxonomy.** The list of labels the
tool tries is currently hand-written. It should come from the SEC's published
taxonomy so it stays current as companies adopt new labels. Not done yet because
the hand-written list covers the common cases and the taxonomy version handling
is a project in itself.

**2. A cache that expires when a company files.** Right now repeated questions
are answered from a saved copy, which is fast, but a restatement can make that
copy quietly out of date. The fix is to watch for new filings and clear the
saved copy then. Not done yet because it needs a background process, and this
runs on one laptop.

**3. Evaluation questions written by an analyst.** The 25 test questions were
written by the person who built the tool, which means they test what he thought
to test. An analyst would ask things that never occurred to him, and those are
exactly the questions where it is most likely to be wrong. This is the highest
value item on the list and the cheapest.
