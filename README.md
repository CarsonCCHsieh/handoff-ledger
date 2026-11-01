# HANDOFF Ledger

An original local workflow that checks whether release handoff claims match their
recorded evidence. It uses the OpenMinion Python SDK with a real, already-installed
Ollama model. It never treats a plausible model answer as proof that a check passed.

The included SampleDock fixture is fictional. Its recorded checks deliberately
contain a passing validation, a failed migration and an unperformed language review.
They are demonstrations of evidence handling, not actual product test results.

## Demonstration and findings

- [Demo video](artifacts/demo/handoff-ledger-demo.mp4): an English-narrated, captioned,
  edited screenshot walkthrough of actual application states. Waiting time is
  abbreviated; it is not a continuous screen recording.
- [Captured execution](docs/demo-execution.md): the newer 84.348-second run passed
  both validation layers after one rejected read and a bounded second Agent turn.
- [Submission narrative](docs/submission-draft.md) and
  [building blocks tested](docs/building-blocks-tested.md).

The repository is preparation material. Formal event registration and submission
remain incomplete; a working prototype and a video do not establish participation.

## Run locally

Requires Python 3.11+ and a running local Ollama server. This qualification environment
uses Python 3.13.2, OpenMinion 0.1.16 and the existing `qwen3.5:9b` model.
No hosted inference account, API key, token purchase or model download is required.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install "git+https://github.com/openminion/openminion.git@2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30"
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m handoff_ledger run --output artifacts/run.json
.venv\Scripts\python.exe server.py --port 31931
```

Then open `http://127.0.0.1:31931/` for the local evidence-review interface.
The server and model run locally; the included fixture is fictional. Starting the
server does not register or submit a competition entry.

The application refuses a model that is not already installed. It also verifies
the SDK's installed version and VCS commit before calling inference. Different
model behavior, resource requirements and execution times remain possible.

## Evidence flow

1. `list_evidence` reads a project manifest and the bounded evidence inventory.
2. `read_span` returns exact source lines, a content hash and a stable reference ID.
3. `check_claim` reads the direct check record and distinguishes supported,
   contradicted and unknown claims. Unrun and obsolete-revision checks stay unknown.
4. OpenMinion's Agent runs the model-backed tool workflow. Its public LLM client
   then generates a schema-constrained report from the actual tool observations,
   using the same local model. Pydantic validates that generated `HandoffReport`.
5. An independent verifier rejects altered/unobserved citations, unsupported claim
   classifications, missing direct references and hidden unknowns or risks.

The three tools are read-only. They are bound to the supplied fixture directory,
enforce manifest SHA-256 hashes and reject paths escaping that directory. The
application does not expose shell, deletion, external account or network tools.
The runtime may register its built-in tool families; the Agent's explicit
`tools=[...]` list limits the tools exposed to this workflow.

## Result contract

`handoff_ledger.runner.run_handoff(...)` returns and saves a receipt with:

- `status`: `succeeded` only after actual tool calls and both validation stages;
- `report`: model-generated claims, unknowns, risks and evidence references;
- `tool_events`: actual arguments, results and timings from the registered tools;
- `sdk`, `model`, `runtime`, `elapsed_ms`: pinned provenance and execution facts;
- `structured_output`: the SDK schema interface, raw model JSON and inference usage;
- `error`: a sanitized failure when execution does not complete successfully.

Failures remain failures. A failed run never receives a generated replacement report.
JSON receipts and sanitized SDK logs are saved under `artifacts/`. Runtime databases,
the isolated virtual environment and temporary installation files are private local
development resources excluded from the source repository.

## Validation and current limits

The original verifier tests cover changed evidence, escaping paths, forged citations,
incorrect pass/fail classifications and the distinction between failed and unrun
checks. A real SDK/model receipt, rather than these tests alone, establishes whether
the integration ran successfully.

The current workflow completed in two independent fresh runtime sessions:
`artifacts/attempt-7.json` (six successful tool calls, 55.317 seconds) and
`artifacts/repeat-2.json` (seven successful tool calls, 53.411 seconds). Both passed
Pydantic and independent citation/classification checks, with explanatory unknowns
and risks generated by the model. No source changes occurred between these two
executions. A fresh run writes its local receipt to `artifacts/run.json`; the newer
captured execution is preserved separately in `artifacts/demo/demo-run.json`.

The earlier `attempt-6.json` also completed, with seven real tool attempts (six
succeeded; one out-of-range read was rejected before recovery), but its findings
were only claim IDs. Earlier failures and raw SDK logs are retained privately,
rather than included in this source bundle. A bounded extra Agent turn handles
missing required tool calls. Neither initial clean run needed it; the newer
captured run did exercise it successfully. See the
[captured execution record](docs/demo-execution.md) for that separate result and
[the factual integration log](docs/building-blocks-tested.md) for the initial work.

`artifacts/reproducibility.json` is the immutable initial freeze, matching commit
`8045c0b9a627d5fb99da79e7793ecaddefb5fdb3`. Later documentation and demo additions
are separate from that historical snapshot; executable review code and fixture
bytes remain unchanged. No general reliability claim follows from these examples.

This prototype reads small UTF-8 fixtures (64 KiB per evidence file); it does not
inspect arbitrary private repositories, run their tests or prove general release
readiness. Its deterministic claim checker currently supports structured check
records. Natural-language explanations still need human review.

Upstream SDK source: [OpenMinion at the audited commit](https://github.com/openminion/openminion/tree/2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30).
The SDK is Apache-2.0 licensed. HANDOFF Ledger's workflow, fixtures and integrity
checks are original implementation work; upstream examples were interface references.
