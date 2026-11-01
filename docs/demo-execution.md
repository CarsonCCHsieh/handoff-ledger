# HANDOFF Ledger: demo execution record

Recorded on 2 November 2026. This document describes a fresh execution started
through the local UI, separate from the two previously frozen successful runs.
It records an actual SDK/model result, not a replacement report assembled for
the demonstration.

## Receipt and result

The inspected receipt is [`artifacts/demo/demo-run.json`](../artifacts/demo/demo-run.json).
Its SHA256 is:

```text
7fc3b5cd5a6ad0016045e35417000453a9f9ec45fbd71f824cdb9538a0d99a1d
```

| Field | Observed value |
| --- | --- |
| Start time | `2026-11-01T23:16:05.052500+00:00` |
| Final status | `succeeded` |
| Recorded elapsed time | 84,348 ms (84.348 seconds) |
| Tool attempts | 6 total: 5 succeeded, 1 rejected |
| Typed output | `typed_output_valid: true` |
| Independent semantic validation | `valid: true`, `errors: []` |
| Tool-collection turns | 2, within the same session |
| SDK | OpenMinion 0.1.16, source commit `2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30` |
| Local model | `qwen3.5:9b`, Ollama 0.40.6 |

## What actually happened

| Sequence | Tool request | Recorded outcome |
| --- | --- | --- |
| 1 | `list_evidence()` | Succeeded |
| 2 | `read_span(evidence_id="checks", start=0, end=3)` | Rejected: `Invalid or oversized evidence span` |
| 3 | `check_claim(claim_id="C01")` | Succeeded: supported |
| 4 | `check_claim(claim_id="C02")` | Succeeded: contradicted |
| 5 | `check_claim(claim_id="C03")` | Succeeded: unknown |
| 6 | `read_span(evidence_id="checks", start=1, end=1)` | Succeeded |

The invalid zero-based span was not accepted as evidence. After the first Agent
collection turn, the workflow had successful claim checks but no successful
`read_span`. Its independent coverage check therefore requested one bounded,
model-backed recovery turn through the same Agent and policy path. That second
turn obtained the valid span. The receipt contains two distinct collection run
IDs under the same session; the second entry is appended by the coverage-recovery
branch in [`runner.py`](../src/handoff_ledger/runner.py).

This is an exercised coverage-recovery case, rather than an ordinary tool-argument
correction completed inside the first Agent turn. It is also not a reason to
report six successful calls: one of the six attempts was rejected. No direct
Python tool invocation was substituted as execution proof.

OpenMinion's schema-output call then returned the report. Pydantic validation and
the independent evidence checks both passed. The report preserves three distinct
conclusions: blank-name validation is supported; the claimed upgrade-migration
success is contradicted by saved-locale loss; Japanese-copy verification remains
unknown because its review was not run. Unknowns and risks contain concrete text
and the conclusions cite exact source lines.

## Relationship to the frozen runs

| Receipt | Elapsed time | Successful / rejected tool attempts | Collection turns |
| --- | --- | --- | --- |
| `artifacts/attempt-7.json` | 55.317 s | 6 / 0 | 1 |
| `artifacts/repeat-2.json` | 53.411 s | 7 / 0 | 1 |
| `artifacts/demo/demo-run.json` | 84.348 s | 5 / 1 | 2 |

Both earlier clean runs passed typed and semantic validation without entering the
coverage-recovery branch. Their frozen documentation accurately describes that
earlier evidence. This additional execution now provides one real successful
example of the bounded recovery branch. It does not establish exhaustive recovery
testing, general model reliability, or a performance benchmark. The earlier
receipts and frozen documents are unchanged.

## Fixture and presentation disclosure

SampleDock is original synthetic project evidence. It is not a private customer
repository or a real production incident. The SDK calls, local-model inference,
rejected request, recovery turn, and validation result in this receipt are real.
The workflow reviews recorded evidence; it did not run SampleDock's tests or
independently establish that the fictional check records describe real events.

The accompanying demonstration uses an **edited screenshot walkthrough of saved
real executions**, not a continuous screen recording. Cuts and shortened waits
must remain disclosed. The 84.348-second timing comes from this receipt; an edited
video's duration is not the duration of a new on-camera inference. Materials that
show this run must use its five-success/one-rejection count rather than borrowing
the earlier clean-run counts.

## Repository and submission state

The integration handoff records the private repository
[CarsonCCHsieh/handoff-ledger](https://github.com/CarsonCCHsieh/handoff-ledger) at
commit `8045c0b9a627d5fb99da79e7793ecaddefb5fdb3`. That is a private source
snapshot, not a public release or proof that this later document is included in
that commit. Formal Cortensor entry/submission remains incomplete, and no public
video link exists at this record's handoff. This documentation task did not run a
model, operate a browser, publish content, or change the earlier frozen proofs.
