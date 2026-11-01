"""Run the real OpenMinion/Ollama workflow and retain sanitized evidence."""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import importlib.metadata
import hashlib
import io
import json
import logging
from pathlib import Path
import platform
import re
import time
import urllib.request
from uuid import uuid4

from .evidence import EvidenceVault
from .models import HandoffReport, report_schema_for_checks

SOURCE_COMMIT = "2ed5d8df3b7cd41ffb11bc96f6389436ca1c0f30"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sanitize(text: str) -> str:
    text = text.replace(str(PROJECT_ROOT), "<project>")
    text = text.replace(str(PROJECT_ROOT).replace("\\", "/"), "<project>")
    text = re.sub(r"(?i)[a-z]:[\\/](?:users[\\/])[^\s\"<>]+", "<local-path>", text)
    return re.sub(r"(?i)(bearer\s+)[\w.\-]+", r"\1<redacted>", text)


def _local_get(route: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + route, timeout=5) as response:
        return json.load(response)


def run_handoff(
    fixture_root: str | Path = "fixtures/sample-project",
    *,
    model: str = "qwen3.5:9b",
    output_path: str | Path = "artifacts/run.json",
    timeout_seconds: float = 180.0,
) -> dict:
    from openminion import APIRuntime, Agent, __version__, tool
    from openminion.modules.llm import ToolSpec

    started = time.perf_counter()
    run_label = uuid4().hex[:12]
    fixture = Path(fixture_root)
    if not fixture.is_absolute():
        fixture = PROJECT_ROOT / fixture
    output = Path(output_path)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output = output.resolve()
    if not output.is_relative_to(PROJECT_ROOT):
        raise ValueError("Output must stay inside this project")
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": 1,
        "status": "failed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "project": "",
        "sdk": {"name": "openminion", "version": __version__, "source_commit": SOURCE_COMMIT},
        "python": platform.python_version(),
        "model": {"name": model},
        "report": None,
        "tool_events": [],
        "typed_output_valid": False,
        "semantic_validation": {"valid": False, "errors": []},
        "runtime": {},
        "structured_output": {},
        "elapsed_ms": 0,
    }
    sdk_log = io.StringIO()
    captured = io.StringIO()
    handler = logging.StreamHandler(sdk_log)
    logger = logging.getLogger("openminion")
    logger.addHandler(handler)
    runtime = None
    try:
        distribution = importlib.metadata.distribution("openminion")
        direct = json.loads(distribution.read_text("direct_url.json") or "{}")
        actual_commit = direct.get("vcs_info", {}).get("commit_id")
        receipt["sdk"]["verified_install_commit"] = actual_commit
        if __version__ != "0.1.16" or actual_commit != SOURCE_COMMIT:
            raise RuntimeError("Installed SDK does not match the audited version and source commit")
        receipt["model"]["ollama_version"] = _local_get("/api/version")["version"]
        models = _local_get("/api/tags")["models"]
        selected = next((entry for entry in models if entry["name"] == model), None)
        if selected is None:
            raise RuntimeError("Requested model is not already installed; no model will be downloaded")
        receipt["model"]["digest"] = selected["digest"]
        receipt["model"]["initially_running"] = [entry["name"] for entry in _local_get("/api/ps")["models"]]
        vault = EvidenceVault(fixture)
        receipt["project"] = vault.manifest["project"]

        def record(name: str, arguments: dict, callback) -> str:
            tick = time.perf_counter()
            event = {"sequence": len(receipt["tool_events"]) + 1, "name": name, "arguments": arguments}
            try:
                value = callback()
                event.update({"status": "succeeded", "result": value})
                return json.dumps(value, ensure_ascii=False)
            except Exception as error:
                event.update({"status": "failed", "error": _sanitize(str(error))})
                raise
            finally:
                event["elapsed_ms"] = round((time.perf_counter() - tick) * 1000)
                receipt["tool_events"].append(event)

        @tool(min_scope="READ_ONLY", idempotent=True)
        def list_evidence() -> str:
            """Read the project manifest and available evidence without changing files."""
            return record("list_evidence", {}, vault.list_evidence)

        @tool(min_scope="READ_ONLY", idempotent=True)
        def read_span(evidence_id: str, start: int, end: int) -> str:
            """Read an exact bounded evidence span and its verified content hash."""
            return record("read_span", {"evidence_id": evidence_id, "start": start, "end": end}, lambda: vault.read_span(evidence_id, start, end))

        @tool(min_scope="READ_ONLY", idempotent=True)
        def check_claim(claim_id: str) -> str:
            """Read the direct recorded check for a manifest claim, preserving unrun checks as unknown."""
            return record("check_claim", {"claim_id": claim_id}, lambda: vault.check_claim(claim_id))

        state = PROJECT_ROOT / ".state" / run_label
        state.mkdir(parents=True, exist_ok=True)
        config_path = state / "agents.json"
        config = {
            "default_agent": "handoff",
            "agents": {"handoff": {"provider": "ollama", "name": "handoff", "default_channel": "console"}},
            "providers": {"ollama": {"model": model, "base_url": "http://127.0.0.1:11434", "timeout_seconds": timeout_seconds, "tool_call_strategy": "native", "temperature": 0.0}},
            "storage": {"backend": "sqlite", "path": str(state / "runtime.sqlite3")},
            "enabled_channels": ["console"],
        }
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        instructions = (
            "You are HANDOFF Ledger, an evidence-bound release handoff reviewer. "
            "This task concerns only a frozen fictional local fixture, not present-day facts. "
            "No live data, calendar date, browsing, or external verification is needed. "
            "Use only the three provided read-only tools. First list_evidence; then read_span "
            "for the source lines and check_claim for EACH claim. Never invent evidence or mark "
            "not_run as passed. Preserve contradicted checks as risks and not_run as unknowns. "
            "After checking every manifest claim, give a short factual evidence-review summary. "
            "A separate schema-constrained report stage will use the actual tool observations."
        )
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            runtime = APIRuntime.from_config_path(str(config_path), home_root=state / "home", data_root=state / "data")
            def collect(message: str, forced: list[str]):
                with Agent(
                    runtime=runtime,
                    agent_id="handoff",
                    instructions=instructions,
                    tools=[list_evidence, read_span, check_claim],
                    forced_tools=forced,
                    output_type=str,
                    session_id="handoff-" + run_label,
                ) as agent:
                    return agent.run(message, timeout_seconds=timeout_seconds)

            result = collect(
                    "Call list_evidence. Review only the immutable fictional SampleDock "
                    "demo-r3 snapshot exposed by the three read-only tools. Read source spans "
                    "and check every manifest claim, then summarize the recorded findings. "
                    "This is a local evidence exercise, with no question about current dates, "
                    "news, or real-world release readiness. Do not fetch live data.",
                    ["list_evidence"],
            )
            receipt["runtime"] = {"run_id": result.run_id, "session_id": result.session_id, "run_state": result.run_state, "result_id": result.id}
            receipt["agent_response"] = _sanitize(result.text)
            receipt["runtime"]["tool_collection_turns"] = [dict(receipt["runtime"])]

            called = {event["name"] for event in receipt["tool_events"] if event["status"] == "succeeded"}
            checked = {event["arguments"].get("claim_id") for event in receipt["tool_events"] if event["name"] == "check_claim" and event["status"] == "succeeded"}
            missing = sorted({"list_evidence", "read_span", "check_claim"} - called)
            missing_claims = sorted(set(vault.claims) - checked)
            if missing or missing_claims:
                # One bounded model-backed recovery turn, through the same Agent
                # and policy path. Never substitute direct Python calls as proof.
                first_claim = next(iter(vault.claims.values()))
                requests = []
                if "list_evidence" in missing:
                    requests.append("list_evidence with no arguments")
                if "read_span" in missing:
                    requests.append("read_span with arguments " + json.dumps({
                        "evidence_id": first_claim["evidence_id"],
                        "start": first_claim["line"], "end": first_claim["line"],
                    }))
                requests.extend("check_claim with claim_id=" + json.dumps(claim_id) for claim_id in missing_claims)
                forced = missing or ["check_claim"]
                recovery = collect(
                    "Call " + requests[0] + ". The independent workflow validator found "
                    "required tool coverage missing. Execute each of these read-only requests: "
                    + "; ".join(requests) + ". Use only the frozen local fixture; no live data. "
                    "Do not merely describe a tool call. Summarize after execution.",
                    forced,
                )
                receipt["runtime"]["tool_collection_turns"].append({
                    "run_id": recovery.run_id, "session_id": recovery.session_id,
                    "run_state": recovery.run_state, "result_id": recovery.id,
                })
                receipt["agent_response"] += "\n" + _sanitize(recovery.text)

            called = {event["name"] for event in receipt["tool_events"] if event["status"] == "succeeded"}
            if not {"list_evidence", "read_span", "check_claim"}.issubset(called):
                raise RuntimeError("Not all three read-only tools actually executed")
            checked = {event["arguments"].get("claim_id") for event in receipt["tool_events"] if event["name"] == "check_claim" and event["status"] == "succeeded"}
            if checked != set(vault.claims):
                raise RuntimeError("The SDK did not execute check_claim for every manifest claim")

            # Agent.output_type validates its final prose; it does not send a schema
            # to the provider. The public LLM client supports schema-only
            # submit_output, which the official Ollama adapter maps to `format`.
            # Supply actual tool observations, never a preconstructed report.
            observations = {
                "project": vault.manifest["project"],
                "revision": vault.manifest["revision"],
                "observed_claim_checks": [
                    event["result"] for event in receipt["tool_events"]
                    if event["name"] == "check_claim" and event["status"] == "succeeded"
                ],
            }
            schema = report_schema_for_checks(observations["observed_claim_checks"])
            response = runtime.llm.client.complete(
                messages=[
                    {"role": "system", "content": (
                        "Create the schema-constrained HandoffReport from only these recorded "
                        "tool observations of a frozen fictional fixture. Include every claim "
                        "exactly once. Its status must equal the observed classification. "
                        "Copy each reference object exactly, including id, source, both line "
                        "numbers, sha256 and excerpt. Each claim must cite its own reference id. "
                        "Write concise rationales. The unknowns array must explicitly state "
                        "every unperformed or stale check and its claim id; the risks array "
                        "must explicitly state every failed check and its claim id, including "
                        "the concrete observation (not an id alone). Never "
                        "leave either array empty when such observations exist. Do not invent "
                        "evidence or add present-day facts."
                    )},
                    {"role": "user", "content": json.dumps(observations, ensure_ascii=False)},
                ],
                tools=[ToolSpec(
                    name="submit_output",
                    description="Return the evidence-bound HandoffReport as structured data.",
                    input_schema=schema,
                    strict=True,
                )],
                provider="ollama",
                model=model,
                tool_choice="required",
                temperature=0.0,
                max_output_tokens=2200,
                metadata={"purpose": "handoff_report", "thinking": "fast"},
            )
            receipt["structured_output"] = {
                "method": "OpenMinion LLMClient.complete / schema-only submit_output / Ollama format",
                "provider": response.provider,
                "model": response.model,
                "ok": response.ok,
                "latency_ms": response.latency_ms,
                "usage": response.usage.model_dump(),
                "finish_reason": response.finish_reason,
                "raw_text": _sanitize(response.output_text),
                "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest(),
                "returned_tool_names": [call.name for call in response.tool_calls],
            }
            if not response.ok:
                raise RuntimeError(f"Structured report inference failed: {response.error}")
            if any(call.name != "submit_output" for call in response.tool_calls):
                raise RuntimeError("Structured report returned an unexpected tool request")
            report = HandoffReport.model_validate_json(response.output_text)
            receipt["typed_output_valid"] = True
            receipt["report"] = report.model_dump()
            errors = vault.validate_report(receipt["report"])
            receipt["semantic_validation"] = {"valid": not errors, "errors": errors}
            receipt["status"] = "succeeded" if not errors else "failed"
    except Exception as error:
        receipt["error"] = {"type": type(error).__name__, "message": _sanitize(str(error))}
        raw_text = getattr(error, "raw_text", None)
        if raw_text is not None:
            receipt["invalid_model_output"] = _sanitize(str(raw_text))
    finally:
        if runtime is not None:
            try:
                with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                    runtime.close()
            except Exception as error:
                receipt["cleanup_error"] = _sanitize(str(error))
                receipt["status"] = "failed"
        logger.removeHandler(handler)
        handler.close()
        receipt["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        output.with_suffix(".log").write_text(_sanitize(sdk_log.getvalue() + captured.getvalue()), encoding="utf-8")
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt
