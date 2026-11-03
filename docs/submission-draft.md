# HANDOFF Ledger — Keep the proof

**Submission draft, 2 November 2026.** The local prototype is verified; this is
preparation material, not a submitted entry. Formal event registration and
submission have not been completed. The dedicated Hackathon #5 submission
repository URL remains unresolved in the official materials last verified.

## The problem

A release handoff can sound complete while its evidence tells a different story.
An announcement says that every check passed and localization is verified. The
recorded migration check failed, and the language review never ran. The next
maintainer needs to discover those differences before taking responsibility.

A fluent summary alone does not answer the practical questions: Which recorded
check supports this claim? Does it belong to this revision? What failed, and what
has not been checked at all?

HANDOFF Ledger turns that review into a small, inspectable workflow. Its output
keeps each claim attached to exact source lines, preserves uncertainty, and gives
the next owner concrete gaps to follow up.

## What we built

The prototype combines a local review interface with an OpenMinion agent and an
independent evidence verifier. The interface shows source files, release claims,
unknowns, risks, actual tool activity, and the recorded validation result. Selecting
a claim's citation opens and highlights the corresponding source lines.

The original SampleDock demo deliberately includes three different outcomes:

| Handoff claim | Recorded evidence | Verified classification |
| --- | --- | --- |
| Blank display names are rejected | Validation check passed | Supported |
| The upgrade migration passed | Upgrade loses the saved locale | Contradicted |
| Japanese copy is verified | Language review was not run | Unknown |

SampleDock is a **fictional, original fixture**. It is not a customer's repository,
a private production project, or evidence of a real release incident. The model
executions and the tool receipts shown in the demo are real.

For a maintainer, the useful result is an actionable handoff: investigate locale
loss, arrange the missing language review, and inspect the exact evidence behind
each conclusion. The prototype has not measured time savings or been evaluated
with external users.

## The repeatable workflow

1. `list_evidence` reads the manifest and bounded evidence inventory.
2. `read_span` reads exact lines and returns the source's verified SHA-256 hash.
3. `check_claim` reads the recorded check for each claim. Unperformed checks and
   checks from a different revision remain unknown.
4. OpenMinion's Agent collects that evidence using the three declared read-only
   tools. A second model call uses the SDK's formal schema-output interface to
   generate the report from the actual tool observations.
5. Pydantic validates the report's shape. Independent code then checks claim
   coverage, classifications, exact citations, source excerpts, and the visibility
   of unknowns and risks. A failure stays a failure; code does not manufacture a
   replacement report.

The deterministic tools establish what the structured records say. The model
organizes those observations into the handoff and explains the findings. The
independent verifier checks the result rather than trusting fluent wording.

## Building Blocks Tested

- **OpenMinion 0.1.16:** installed from the official source at commit
  `2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30`, with installation provenance checked
  at runtime.
- **`APIRuntime` and `Agent`:** real model-backed tool collection, fresh runtime
  sessions, and explicit tool exposure. The existing runtime policy remains on.
- **Custom `@tool` functions:** `list_evidence`, `read_span`, and `check_claim`,
  explicitly declared `READ_ONLY` and idempotent. Manifest hashes, path boundaries,
  and line limits are enforced in code.
- **Formal schema generation:** `APIRuntime.llm.client.complete` with a single
  schema-only `submit_output` specification. The official Ollama adapter maps its
  schema to Ollama's `format` field. Pydantic and the evidence verifier then check
  the generated result.
- **Existing local inference:** Ollama 0.40.6 with `qwen3.5:9b`. No new model was
  downloaded for these runs, and no hosted inference key was required.

The implementation uses the SDK meaningfully in both evidence collection and
report generation. It does not claim to have exercised Cortensor Portal or the
distributed Cortensor network.

## Verified execution

Two independent fresh runtime sessions completed with the same core source. A
later demonstration run also completed and exercised bounded recovery:

| Receipt | Actual tool calls | Typed output | Evidence verification | Elapsed |
| --- | --- | --- | --- | --- |
| `artifacts/attempt-7.json` | 6 succeeded, 0 failed | Passed | Passed | 55.317 s |
| `artifacts/repeat-2.json` | 7 succeeded, 0 failed | Passed | Passed | 53.411 s |
| `artifacts/demo/demo-run.json` | 5 succeeded, 1 rejected | Passed | Passed | 84.348 s |

All three cover all three claims and all three tool types. Their raw model JSON
matches the saved report. The first two runs used one collection turn each. In the
later demo, a zero-based `read_span` was rejected; the first collection turn then
lacked a successful read, so the coverage guard requested one bounded second Agent
turn. That turn read a valid span before report generation. The rejected call stays
visible in the receipt. These are measurements of this local fixture and
environment, not a general speed or reliability benchmark. The
[captured execution record](demo-execution.md) documents the separate demo result.

The completed [local demo video](../artifacts/demo/handoff-ledger-demo.mp4) is
165.416 seconds long, with English narration and captions. It is an edited
screenshot walkthrough of saved real executions, rather than a continuous screen
recording; shortened waits do not establish a new on-camera inference duration.
The video is included in this repository; formal event submission remains incomplete.

Four integrity tests also pass: the source hash/path boundary, rejection of altered
citations or classifications, rejection of changed evidence, and preservation of
failed versus unperformed checks. Historical failed runs are retained separately.
The detailed record is in [Building blocks tested](building-blocks-tested.md).

## What We Learned

**A typed API can validate an answer without constraining its generation.**
`Agent.output_type` checks the final reply in this SDK version; it does not send a
schema to the provider. Our first real tool-backed answer was accurate prose and
failed the requested report type. Reading the official SDK source led to the
explicit two-stage approach above.

**Valid JSON can still hide an important gap.** A later model report had correct
claims and citations but empty unknowns and risks. The independent verifier rejected
it. The schema now requires visible findings when the observed checks contain
unknowns or contradictions, and the model supplies explanatory text.

**Tool metadata and observed execution both matter.** Bare tool declarations were
treated as write-capable by the SDK's default metadata. Declaring the actual
read-only scope fixed our configuration while preserving policy. A separate run
skipped a required tool; the coverage guard rejected it. The code now permits at
most one policy-bound recovery turn. Neither initial clean run needed that branch;
the later demo exercised it successfully after a rejected read. This establishes
one observed recovery case, not exhaustive recovery testing.

## Limitations and next steps

The current prototype reads small UTF-8 evidence files, bounded to 64 KiB each,
with a structured check-record format. It does not run a project's test suite,
inspect arbitrary private repositories, verify the truth of an author's original
records, or approve a release. SHA-256 detects a mismatch against the manifest;
it does not establish who produced the evidence. Natural-language explanations
still need human review.

The two initial clean runs and the separate successful demo establish a working
local demonstration, not a statistical reliability claim. The demo provides one
runtime example of the missing-coverage recovery branch; the original clean-run
receipts remain unchanged. Timeout settings apply per collection/provider call,
not as a single shared deadline for the entire workflow.

Useful next steps are documented adapters for CI-produced evidence, explicit
evidence-origin metadata, and evaluation against more original fixtures. These
are proposed extensions, not shipped capabilities.

## AI assistance and attribution

Codex assisted with original implementation, inspection of the official SDK,
debugging, test design, and documentation. The demonstrated handoff model is the
local `qwen3.5:9b` running through OpenMinion. Actual tool events and independent
checks establish execution; AI-written descriptions do not substitute for them.
The workflow, interface, fixtures, and verifier are original project work.
OpenMinion is the attributed Apache-2.0 SDK dependency.

## Submission preparation status

The verified event materials request a useful repeatable OpenMinion workflow, a
real model-backed run, a public reproducible project, a one-to-five-minute demo,
and Building Blocks Tested / What We Learned notes. The
[public source](https://github.com/CarsonCCHsieh/handoff-ledger) and
[demo video](../artifacts/demo/handoff-ledger-demo.mp4) are now available.

Before formal delivery, resolve the dedicated event repository and current entry
instructions, verify the remaining eligibility/entry fields, and complete the
required entry and delivery steps. Public materials or a local prototype do
not count as joining or submitting. After confirmed submission, add the approved
showcase to Microusada and clean expendable process resources while retaining the
final deliverables and receipts.

Official references last verified for this preparation:
[Hackathon #5 overview](https://docs.cortensor.network/community-and-ecosystem/hackathon/hackathon-5),
[organizer v2 materials](https://docs-v2.cortensor.network/ecosystem/hackathon-5/),
[DoraHacks event](https://dorahacks.io/hackathon/2418),
[official OpenMinion source](https://github.com/openminion/openminion).
