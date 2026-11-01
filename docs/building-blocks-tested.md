# Building blocks tested

This is a factual development log. Failed attempts are retained as failures.

## Pinned environment

- OpenMinion 0.1.16, installed from the official repository at
  `2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30`. The workflow checks the
  installation's `direct_url.json`, rather than trusting the package version alone.
- Native Python 3.13.2 in an isolated project virtual environment.
- Existing local Ollama 0.40.6 with `qwen3.5:9b`; no new model was downloaded.
- Model digest:
  `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`.
- All evidence is an original fictional SampleDock fixture. No private project
  files or credentials were supplied to the model.

## Actual attempts

1. `artifacts/attempt-1.json`: the runtime rejected an invalid inbound channel
   before inference. The application profile omitted `default_channel`; setting
   it explicitly to `console` corrected that configuration error.
2. `artifacts/attempt-2.json`: real local model requests completed, but the
   runtime required policy confirmation for `list_evidence`. The tool did not
   execute, and Pydantic correctly rejected the confirmation text as a report.
   The application had used a bare `@tool` decorator. In this SDK version,
   `tools/decorator.py` defaults its generated tool family to `WRITE_SAFE`.
   The three genuinely read-only tools now explicitly declare
   `@tool(min_scope="READ_ONLY", idempotent=True)`. Runtime policy stays enabled.
   This was an application metadata omission, not evidence of an SDK policy bug.
3. `artifacts/attempt-3.json`: the read-only declaration removed that confirmation
   obstacle, but no custom tool executed. Runtime telemetry recorded an
   `entry_text_response`, followed by fallback freshness classification requiring
   live data and an exact date. The runtime returned a freshness failure, which
   Pydantic again rejected. A fixed fictional snapshot does not establish
   present-day facts; the application must communicate that scope clearly.
4. `artifacts/attempt-4.json`: the same SDK and model used its supported native
   tool-calling configuration, with an explicit frozen-fixture request. Five real
   tool calls succeeded: `list_evidence`, `read_span(checks, 1, 3)` and
   `check_claim` for C01, C02 and C03. The model accurately described supported,
   contradicted and unknown claims, but returned prose rather than the required
   JSON report. Pydantic rejected it; `report` remains null and semantic report
   validation was not reached. Elapsed time was 43,361 ms. This proves tool
   execution, not a successful typed-output integration or competition entry.
5. `artifacts/attempt-5.json`: after reading the SDK's official typed-output path,
   the workflow split evidence collection and report generation. `Agent`'s
   `output_type` only validates the final response; it does not transmit a schema
   to the model. The public `APIRuntime.llm.client.complete` accepts a schema-only
   `submit_output` tool, which the Ollama adapter maps to its `format` field.
   Seven real evidence tool calls succeeded and the report passed Pydantic, with
   correct source references and classifications. However, the model omitted the
   separate unknowns and risks lists. The independent semantic verifier rejected
   it. Elapsed time was 56,943 ms.
6. `artifacts/attempt-6.json`: the report schema now requires nonempty unknowns or
   risks when the actual tool observations contain those findings. This constrains
   visibility; it does not construct the report or fill in any generated text.
   With the same SDK, model and enabled policy, seven real tool attempts ran
   (six succeeded; one zero-based/out-of-range read was rejected and recovered), the
   model generated a typed report, and independent semantic/citation verification
   passed. Elapsed time was 55,270 ms. The two stages and raw generated JSON are
   recorded explicitly in the receipt.
7. `artifacts/repeat-1.json`: an independent repetition executed `list_evidence`
   and all three `check_claim` calls successfully, but skipped a separate
   `read_span` tool call. The coverage guard correctly rejected the run before
   generating a report (30,485 ms). The workflow now gives the same policy-bound
   Agent at most one explicit recovery turn for missing required calls. Tools
   still execute through the real SDK; direct Python calls never replace that
   evidence. Report findings also require explanatory text instead of claim IDs
   alone.
8. `artifacts/attempt-7.json`: six tool calls all succeeded, including direct reads
   of the recorded checks and the unverified release notes. The model generated
   specific Japanese-review and locale-loss findings. Pydantic and independent
   semantic/citation verification passed in 55,317 ms.
9. `artifacts/repeat-2.json`: a fresh runtime/session repeated the unchanged
   workflow. Seven tool calls all succeeded; Pydantic and independent verification
   again passed, in 53,411 ms. Its specific findings were also model-generated.
   Both final runs used one collection turn; neither exercised the newly bounded
   missing-coverage recovery branch. That branch has source review, not a claimed
   successful runtime test. No further inference was started after this repetition.

## Independent checks

Four local verifier tests pass: source hash and path boundaries, rejection of
altered citations/classifications, rejection of changed evidence, and preserving
the difference between a failed check and an unperformed check. These checks do
not substitute for a successful SDK integration run.

The stable `artifacts/run.json` is the canonical UI run receipt; separate named
receipts retain historical attempts and independent repetitions. A real
success requires all three tools to execute, every manifest claim to be checked,
a model-generated Pydantic report, and the independent semantic verifier to pass.
No report is manufactured when any of those stages fail.

Each run closes its APIRuntime. The application did not stop the existing Ollama
service or unload another user's model. Runtime databases and `.openminion/` state
remain excluded from source publication. CLI inference processes have exited.
The UI can be started explicitly with `.venv\Scripts\python.exe server.py --port 31931`.
