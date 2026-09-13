# ============================================================================
# Backend Dev's real application image, replacing DevOps's placeholder
# (2026-09-12 — see git history for the original placeholder header). This
# file is Backend Dev's to own; DevOps builds/pushes/deploys it, doesn't
# edit its contents (backend/CLAUDE.md "Directory Structure").
#
# Base image, WORKDIR, and CMD/handler *structure* are unchanged from the
# placeholder — that part is dictated by how AWS Lambda container images
# work (package_type = "Image", no separate "handler" config; CMD is the
# handler), not by app content. Only the "what gets copied in and
# installed" part changes: the real FastAPI app under app/, and the real
# requirements.txt (this directory's, not a placeholder pip install line).
# ============================================================================

# AWS-provided base image for Lambda Python container images (Python 3.12,
# root CLAUDE.md stack). Sets WORKDIR=/var/task (== $LAMBDA_TASK_ROOT) and
# bakes in the Lambda Runtime Interface Client/entrypoint already — do not
# override ENTRYPOINT.
FROM public.ecr.aws/lambda/python:3.12

# requirements.txt is owned jointly: Architect's schema-layer pins
# (sqlalchemy, alembic, geoalchemy2, pydantic) plus Backend Dev's app-layer
# additions (fastapi, mangum, boto3, pyjwt) below them in the same file —
# see that file's own header comment.
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r "${LAMBDA_TASK_ROOT}/requirements.txt"

# The real application code.
COPY app/ ${LAMBDA_TASK_ROOT}/app/

# package_type = "Image" Lambda functions have no separate "handler" config
# — CMD here *is* the handler, in "<module>.<callable>" form (see
# infra/CLAUDE.md "Lambda + API Gateway"). Matches app/main.py's
# `handler = Mangum(app)`.
CMD ["app.main.handler"]
