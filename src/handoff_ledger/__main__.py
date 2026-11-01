import argparse
import json

from .runner import run_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real local evidence-bound handoff")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--fixture", default="fixtures/sample-project")
    parser.add_argument("--output", default="artifacts/run.json")
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    receipt = run_handoff(args.fixture, model=args.model, output_path=args.output, timeout_seconds=args.timeout)
    print(json.dumps({"status": receipt["status"], "tool_calls": len(receipt["tool_events"]), "typed_output_valid": receipt["typed_output_valid"], "semantic_validation": receipt["semantic_validation"], "elapsed_ms": receipt["elapsed_ms"], "error": receipt.get("error")}, ensure_ascii=False))
    return 0 if receipt["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
