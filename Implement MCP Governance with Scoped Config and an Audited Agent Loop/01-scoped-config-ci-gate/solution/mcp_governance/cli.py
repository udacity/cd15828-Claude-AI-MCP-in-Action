"""``mcp-governance`` command-line entry point.

Subcommands are added per governance concern:

* ``ci-check <path>`` -- the merge-time gate; exit 0 clean / 1 on violations.
* ``decide`` -- render the build-vs-reuse decision matrix.
* ``run <request.json>`` -- run one request through the audited agent loop.
* ``audit`` -- print the recorded audit trail.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from mcp_governance.audit import AuditTrail, SystemClock
from mcp_governance.bridge import build_bridge
from mcp_governance.config import PROJECT_ROOT
from mcp_governance.decision import decision_matrix
from mcp_governance.loop import ModelRunner, run_agent
from mcp_governance.scoping import run_ci_check

DEFAULT_AUDIT_LOG = PROJECT_ROOT / "audit_log.json"


def _cmd_ci_check(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    report = run_ci_check(args.path, environ)
    print(json.dumps(report.model_dump(), indent=2))
    return 0 if report.ok else 1


def _cmd_decide(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    recs = decision_matrix()
    width = max(len(r.need) for r in recs)
    print(f"{'INTEGRATION NEED'.ljust(width)}  RECOMMENDATION  RATIONALE")
    for r in recs:
        print(f"{r.need.ljust(width)}  {r.recommendation.value.ljust(14)}  {r.rationale}")
    return 0


def _cmd_run(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    payload = json.loads(Path(args.path).read_text())
    request = payload["request"] if isinstance(payload, dict) else str(payload)
    caller = payload.get("caller_identity", "cli-user") if isinstance(payload, dict) else "cli-user"

    runner: ModelRunner | None = getattr(args, "runner", None)
    if runner is None:
        from mcp_governance.loop import AnthropicRunner

        runner = AnthropicRunner()

    bridge = asyncio.run(build_bridge())
    trail = AuditTrail()
    outcome = run_agent(
        request=request,
        runner=runner,
        bridge=bridge,
        trail=trail,
        clock=SystemClock(),
        caller_identity=caller,
    )
    trail.append_to_file(Path(args.audit_log))
    report = {
        "outcome": outcome.model_dump(),
        "audit_trail": [e.model_dump() for e in trail.entries],
    }
    print(json.dumps(report, indent=2))
    return 0


def _cmd_audit(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    entries = AuditTrail.load_file(Path(args.audit_log))
    print(json.dumps([e.model_dump() for e in entries], indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcp-governance", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ci = sub.add_parser("ci-check", help="validate an .mcp.json for secrets and missing env vars")
    p_ci.add_argument("path", help="path to the .mcp.json (or ~/.claude.json) to check")
    p_ci.set_defaults(func=_cmd_ci_check)

    p_decide = sub.add_parser("decide", help="render the build-vs-reuse decision matrix")
    p_decide.set_defaults(func=_cmd_decide)

    audit_log_help = "audit trail JSON path"
    p_run = sub.add_parser("run", help="run one request through the audited agent loop")
    p_run.add_argument("path", help="path to a request.json with 'request' and 'caller_identity'")
    p_run.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG), help=audit_log_help)
    p_run.set_defaults(func=_cmd_run)

    p_audit = sub.add_parser("audit", help="print the recorded audit trail")
    p_audit.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG), help=audit_log_help)
    p_audit.set_defaults(func=_cmd_audit)

    return parser


def main(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    runner: ModelRunner | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.runner = runner  # injected for tests; None -> real AnthropicRunner for `run`
    env = os.environ if environ is None else environ
    func = args.func
    return int(func(args, env))


if __name__ == "__main__":
    sys.exit(main())
