# HANDOFF Ledger — demonstration script

**Master cut: 4 minutes 20 seconds; condensed cut: 2 minutes 30 seconds.** These
are planning scripts, distinct from the completed 165.416-second English-narrated,
captioned [local demo](../artifacts/demo/handoff-ledger-demo.mp4). The completed
cut is an edited screenshot walkthrough of saved real executions and has not
been publicly uploaded. Its newer recovery run is documented in
[the captured execution record](demo-execution.md); the suggested cuts below do
not establish the timing or exact narration of that finished video.

The default walkthrough presents the saved output of real, verified model runs.
Say that explicitly. Do not click the run button and imply a new execution took
place while displaying a stored receipt. No new inference is required to record
this version of the demonstration.

## Condensed 2:30 cut

This version can use edited screenshots from the actual local UI and approved
receipts. Label it **Edited screenshot walkthrough of saved real executions**.
Still frames do not establish an on-camera interactive or fresh inference run.
Use the master cut below for precise evidence and navigation details.

| Time | Actual material on screen | Suggested narration |
| --- | --- | --- |
| 0:00–0:18 | Full workspace and synthetic-project label | HANDOFF Ledger helps the next maintainer inspect the evidence behind a release handoff. This is an edited walkthrough of saved, verified model executions. SampleDock is original fictional demo data. |
| 0:18–0:42 | Release notes, then the three check records | The announcement says every check passed. The records show that blank-name validation passed, an upgrade loses the saved locale, and a Japanese language review was never run. Those are three different handoff decisions. |
| 0:42–1:08 | Claim cards, migration citation, highlighted source line 2 | The report preserves supported, contradicted and unknown claims. A citation takes the reviewer to the migration failure. The independent verifier checks the source hash, exact excerpt and classification. The handoff keeps the locale defect and missing review visible. |
| 1:08–1:38 | Audit trail, attempt-7 and repeat-2 receipt facts | OpenMinion really called the read-only tools. Its official schema interface then generated the report, followed by Pydantic and evidence checks. Two fresh sessions passed: six successful calls in fifty-five seconds, then seven in fifty-three seconds. These are recorded timings for this fixture. |
| 1:38–2:03 | Verified unknown/risk text and documented earlier rejection | An earlier response was valid JSON but hid the unknowns and risks in empty lists. The verifier rejected it. The current schema requires visible findings, and the model writes their explanations. Code does not fill in a successful fallback report. |
| 2:03–2:30 | Final workspace with readable limitations caption | This prototype reads small structured files; it does not run tests or approve a release. The initial clean runs needed no recovery; a later demo passed after one rejected read and a bounded second Agent turn. Codex assisted development. Real tool events and independent checks support a handoff someone else can inspect. |

The short cut may leave detailed registration status to the accompanying written
draft, but must not imply registration, submission, publication, or a prize. No
new live run is required for either cut.

## Recording setup

- Start the existing local UI with
  `.venv\Scripts\python.exe server.py --port 31931`, then open
  `http://127.0.0.1:31931/`. The server reads the existing `artifacts/run.json`.
- Keep the synthetic-project label visible. Use only the original SampleDock
  files, the project UI, approved source, and sanitized run receipts on screen.
  Frame the recording to exclude account tabs, notifications, unrelated files,
  terminal history, and private filesystem breadcrumbs.
- Prepare `artifacts/attempt-7.json`, `artifacts/repeat-2.json`, and
  `artifacts/reproducibility.json` in a clean local viewer. Keep the same files
  intact; a recording edit must not change their contents.
- Confirm the displayed result is the saved successful run: one supported claim,
  one contradicted claim, one unknown claim, plus specific unknown/risk text.
  This is a pre-recording inspection, not permission to substitute success if the
  loaded state differs. Show the actual state and investigate before recording.
- The core source, README, fixture, and receipts are already prepared. This script
  does not register an event account, publish a repository, submit an entry, or
  authorize another model run.

## 0:00–0:25 — Show the handoff problem

**Screen:** Full review workspace, including the synthetic-project label. Avoid
opening run details yet; let viewers see the source/review/audit layout.

**Narration:**

> This is HANDOFF Ledger. A handoff may say a release is ready while its recorded
> checks show a failure and an unfinished review. The next maintainer needs a
> clear explanation and a way to inspect the evidence. This walkthrough shows a
> saved, verified execution of the local OpenMinion workflow.

## 0:25–0:55 — Establish the original synthetic fixture

**Screen:** Select `release-notes.md`, then `checks.jsonl` in Source evidence.
Pause on the three check records so their different statuses can be read.

**Narration:**

> SampleDock is original fictional demo data, not a private customer project. Its
> draft announcement says every check passed and Japanese copy was verified. The
> records show something more useful: blank-name validation passed, an upgrade
> loses the saved locale, and the Japanese review was never run.

## 0:55–1:35 — Follow a claim to exact evidence

**Screen:** Show the supported, contradicted, and unknown cards. Select the
upgrade-migration citation. The source pane should highlight line 2 of
`checks.jsonl`; pause long enough to read its failed status and locale-loss detail.

**Narration:**

> Each conclusion has a trail. The migration claim is contradicted, and its
> citation takes us directly to the recorded failure. The verifier checks this
> source hash, the exact excerpt, and the claim's classification. The language
> review stays unknown, because not running a check is different from a failed
> check.

## 1:35–2:05 — Show what the next owner receives

**Screen:** Bring Still unknown and For the next owner into view. Read their
actual saved wording rather than a replacement caption with invented findings.

**Narration:**

> The handoff preserves two concrete follow-ups: perform the Japanese language
> review and investigate the migration's locale loss. These findings were
> generated by the model from actual tool observations. The application checks
> them before reporting success. It does not turn missing evidence into an
> assurance that a release is ready.

## 2:05–2:45 — Show the real execution receipt

**Screen:** Show The audit trail and expand Run details. Then show selected fields
from `attempt-7.json`: `status`, `tool_events`, `typed_output_valid`,
`semantic_validation`, `model`, and `elapsed_ms`. Keep the JSON file name visible.

**Narration:**

> This receipt records six successful tool calls, with OpenMinion 0.1.16 and the
> existing local qwen3.5:9b model. The tool functions really
> read the fixture. The model's raw JSON is retained, and both typed output and
> independent evidence checks passed. This run took about fifty-five seconds on
> this machine; this walkthrough is displaying its stored result.

**Facts to display:** `attempt-7.json` has 6 succeeded / 0 failed tool calls,
`typed_output_valid: true`, `semantic_validation.valid: true`, and
`elapsed_ms: 55317`. Do not use attempt-6's earlier 7-attempt count here.

## 2:45–3:15 — Demonstrate repeatability without replaying a result

**Screen:** Open `repeat-2.json`, then the two run entries in
`reproducibility.json`. Show their distinct runtime/session identifiers and
successful validation fields. Long hashes need not be read aloud.

**Narration:**

> A separate fresh session repeated the unchanged workflow. It made seven
> successful tool calls and passed both checks in about fifty-three seconds. The
> call sequence can differ, so we retain the events instead of assuming that a
> convincing answer proves execution. These are two real runs of this fixture,
> not a claim of general reliability.

## 3:15–3:50 — Explain the SDK integration and one useful failure

**Screen:** Show the short Evidence flow in the README, or the corresponding
`Agent` and `runtime.llm.client.complete` calls in the approved source. Then show
the documented attempt-5 failure in `docs/building-blocks-tested.md`.

**Narration:**

> OpenMinion handles evidence collection through three declared read-only tools.
> Its official schema-output interface then generates the report, followed by
> Pydantic and citation checks. One earlier run produced valid JSON but omitted
> the unknowns and risks. Our independent verifier rejected it. That failure led
> to explicit visibility constraints; no fallback report was filled in by code.

## 3:50–4:20 — State the limits and close

**Screen:** Return to the claim cards and highlighted evidence. End with the
project name and existing local workspace, without unverified submission badges
or invented public links.

**Narration:**

> This prototype reads small structured evidence files. It does not run a
> project's tests or approve a release, and its explanations still need human
> review. Both initial clean runs completed without the missing-tool recovery
> turn. A later demo exercised that bounded turn after a rejected read and passed
> both validation layers. That is one recovery example, not a reliability study.
> Codex assisted the
> implementation and debugging; real SDK events and independent checks support
> the result. HANDOFF Ledger leaves the next owner a summary they can inspect.

## Capture and delivery notes

- Preserve enough source text and citation detail for a reviewer to follow the
  migration finding. Keep captions consistent with the saved receipts.
- If cuts shorten navigation, retain the disclosure that this is a saved-run
  walkthrough. Do not present a recorded elapsed time as the duration of a new
  on-camera execution.
- The target remains within the verified one-to-five-minute requirement. Verify
  the exported video's actual duration and readability before using it.
- Registration and formal submission remain incomplete. The dedicated event
  submission repository URL has not been resolved in the verified materials.
  Add real source/video/delivery links only after those steps occur.
