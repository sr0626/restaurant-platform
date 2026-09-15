"""Backend Dev's one-off operational scripts (dev/test seeding, etc.).

Not part of the request-serving app surface — nothing under `app/routers`
imports this package. Shipped inside the same container image as the rest
of `app/` (the Dockerfile does `COPY app/ ${LAMBDA_TASK_ROOT}/app/`, which
already includes this directory) so `app/main.py`'s management-command
branch (see that module) can import and run these scripts from inside a
real Lambda invocation without any image/Dockerfile change — see
`seed_dev_data.py`'s module docstring for why that matters (Aurora has no
network path reachable from outside this Lambda's VPC).
"""
