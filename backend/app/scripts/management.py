"""Dispatch table for one-off management commands, invoked directly via
`aws lambda invoke` -- bypassing API Gateway/Mangum entirely. See
`app/main.py`'s `handler` for the branch that routes here, and
`seed_dev_data.py`'s module docstring ("How to actually run this against
the real dev database") for *why* this exists: Aurora sits in private
subnets with no NAT Gateway, no bastion host, and the RDS Data API is not
enabled (checked against `infra/modules/networking` and
`infra/modules/aurora`, not assumed) -- the deployed Lambda's own VPC
route is the only thing on this side of the account that can reach it, so
a script that needs to write to Aurora has to run inside a Lambda
invocation.

Not an HTTP surface -- there is no API Gateway route in front of this, no
JWT/Cognito auth applies, and none should ever be added here. The trust
boundary is IAM: only a caller who already holds `lambda:InvokeFunction`
on this one function in the target AWS account can reach it at all, which
is the same "already has real AWS access" boundary as `terraform apply`
or any other direct AWS action elsewhere in this repo. Keep this dispatch
table tiny and strictly dev/ops-only -- never wire real application
business logic through it; that belongs behind the normal FastAPI/Mangum
path with normal auth.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger("app.scripts.management")

_COMMANDS: dict[str, Callable[[dict], dict]] = {}


def _command(name: str):
    def decorator(fn: Callable[[dict], dict]) -> Callable[[dict], dict]:
        _COMMANDS[name] = fn
        return fn

    return decorator


@_command("seed_dev_data")
def _run_seed_dev_data(event: dict) -> dict:
    from app.scripts.seed_dev_data import SeedConfigError, run_seed

    identities_path = event.get("identities_path")
    try:
        counts = asyncio.run(run_seed(identities_path))
    except SeedConfigError as exc:
        return {"ok": False, "command": "seed_dev_data", "error": str(exc)}
    return {"ok": True, "command": "seed_dev_data", "counts": counts}


@_command("alembic_upgrade")
def _run_alembic_upgrade(event: dict) -> dict:
    from app.scripts.run_migrations import run_upgrade

    revision = event.get("revision", "head")
    result = run_upgrade(revision)
    return {"ok": True, "command": "alembic_upgrade", **result}


def run_management_command(event: dict, context: Any) -> dict:
    """Entry point called from `app.main.handler`. Never raises -- every
    outcome (including an unknown command or an unhandled exception from
    the command itself) comes back as a `{"ok": bool, ...}` dict in the
    Lambda invoke response payload, since there's no HTTP status code to
    carry it on this path.
    """
    command = event.get("_management_command")
    fn = _COMMANDS.get(command)
    if fn is None:
        return {
            "ok": False,
            "error": f"Unknown management command: {command!r}. "
            f"Known commands: {sorted(_COMMANDS)}",
        }
    try:
        return fn(event)
    except Exception as exc:  # noqa: BLE001 - top-level Lambda invoke boundary
        logger.exception("management command %r failed", command)
        return {"ok": False, "command": command, "error": str(exc)}
