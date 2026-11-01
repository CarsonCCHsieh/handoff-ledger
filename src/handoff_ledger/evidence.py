"""Read-only, manifest-bound tools with content hashes and exact line references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class EvidenceVault:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve(strict=True)
        self.manifest = json.loads((self.root / "manifest.json").read_text("utf-8"))
        self.sources = {item["id"]: item for item in self.manifest["evidence"]}
        self.claims = {item["id"]: item for item in self.manifest["claims"]}
        self.references: dict[str, dict[str, Any]] = {}
        for evidence_id in self.sources:
            self._read(evidence_id)

    def _read(self, evidence_id: str) -> tuple[dict[str, Any], list[str]]:
        item = self.sources[evidence_id]
        relative = Path(item["source"])
        path = (self.root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(self.root):
            raise ValueError("Evidence path escapes the fixture root")
        path = path.resolve(strict=True)
        if path.stat().st_size > 65536:
            raise ValueError("Evidence exceeds the bounded 64 KiB limit")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Evidence hash does not match its manifest")
        return item, data.decode("utf-8").splitlines()

    def list_evidence(self) -> dict[str, Any]:
        return {
            "project": self.manifest["project"],
            "revision": self.manifest["revision"],
            "claims": list(self.claims.values()),
            "evidence": [
                {**item, "line_count": len(self._read(key)[1])}
                for key, item in self.sources.items()
            ],
        }

    def read_span(self, evidence_id: str, start: int, end: int) -> dict[str, Any]:
        item, lines = self._read(evidence_id)
        if not 1 <= start <= end <= len(lines) or end - start >= 40:
            raise ValueError("Invalid or oversized evidence span")
        reference = {
            "id": f"{evidence_id}:L{start}-L{end}",
            "source": item["source"],
            "line_start": start,
            "line_end": end,
            "sha256": item["sha256"],
            "excerpt": "\n".join(lines[start - 1 : end]),
        }
        self.references[reference["id"]] = reference
        return reference

    def check_claim(self, claim_id: str) -> dict[str, Any]:
        claim = self.claims[claim_id]
        reference = self.read_span(claim["evidence_id"], claim["line"], claim["line"])
        observation = json.loads(reference["excerpt"])
        if observation.get("check_id") != claim["check_id"]:
            raise ValueError("Claim points to a different check")
        status = observation.get("status")
        if observation.get("revision") != self.manifest["revision"] or status == "not_run":
            classification = "unknown"
        elif status == "passed":
            classification = "supported"
        elif status == "failed":
            classification = "contradicted"
        else:
            classification = "unknown"
        return {
            "claim_id": claim_id,
            "claim": claim["title"],
            "classification": classification,
            "observation": observation,
            "reference": reference,
        }

    def validate_report(self, report: dict[str, Any]) -> list[str]:
        """Reject unsupported classifications and altered or fabricated references."""
        errors = []
        claims = report["claims"]
        reported_ids = [item["id"] for item in claims]
        if len(set(reported_ids)) != len(reported_ids) or set(reported_ids) != set(self.claims):
            errors.append("Report must cover every manifest claim exactly once")
        references = report["references"]
        reference_map = {item["id"]: item for item in references}
        if len(reference_map) != len(references):
            errors.append("Duplicate reference identifiers")
        for reference in references:
            if self.references.get(reference["id"]) != reference:
                errors.append(f"Unobserved or altered reference: {reference['id']}")
        for item in claims:
            if item["id"] not in self.claims:
                continue
            facts = self.check_claim(item["id"])
            if item["status"] != facts["classification"]:
                errors.append(f"Classification conflicts with evidence: {item['id']}")
            expected_reference = facts["reference"]["id"]
            if expected_reference not in item["evidence_refs"]:
                errors.append(f"Claim lacks its direct evidence: {item['id']}")
            if any(ref not in reference_map for ref in item["evidence_refs"]):
                errors.append(f"Claim cites a missing reference: {item['id']}")
        if any(item["status"] == "unknown" for item in claims) and not report["unknowns"]:
            errors.append("Unknown findings must remain visible in unknowns")
        if any(item["status"] == "contradicted" for item in claims) and not report["risks"]:
            errors.append("Contradictions must remain visible in risks")
        return errors
